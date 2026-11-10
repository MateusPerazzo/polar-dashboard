-- Diagnóstico dos dados antes de montar a camada gold.

-- 1. Quanto dado eu tenho
-- 32 noites (sono e recharge) e 34 dias de atividade, de 01/10 a 03/11.
-- Faltam 2 noites (27/10 e 31/10): nas duas eu esqueci de colocar a
-- pulseira para dormir (a de 31/10 foi depois da festa de Halloween, que
-- acabou às 5h). Pouco dado ainda, então as análises vão ser mais
-- exploratórias.
SELECT 'sleep' AS tabela, MIN(date) AS primeira, MAX(date) AS ultima, COUNT(*) AS linhas FROM sleep
UNION ALL
SELECT 'nightly_recharge', MIN(date), MAX(date), COUNT(*) FROM nightly_recharge
UNION ALL
SELECT 'daily_activity', MIN(date), MAX(date), COUNT(*) FROM daily_activity;

-- 2. Colunas vazias ou que nunca mudam
-- sleep_goal tem um valor só (minha meta nunca mudou), então não entra.
-- sleep_rating varia, mas é a nota que eu mesmo dou toda manhã, sem muito
-- critério e tem noites com 0 (sem avaliação). 
-- Vou usar o sleep_score da Polar para medir a qualidade do sono.
SELECT COUNT(*)                     AS noites,
       COUNT(sleep_rating)          AS rating_preenchido,
       COUNT(DISTINCT sleep_rating) AS ratings_diferentes,
       COUNT(DISTINCT sleep_goal)   AS metas_diferentes
FROM sleep;

-- 3. A coluna date é o dia em que deitei ou em que acordei?
-- Filtrei as noites em que deitei antes da meia-noite: em todas, date é o
-- dia em que acordei. Ou seja, a atividade que influencia a noite D é a do dia D-1.
-- Usei substr em vez de date() porque date() converte o horário com
-- fuso (-03:00) para UTC e jogava as noites para o dia seguinte.
SELECT date              AS data_noite,
       sleep_start_time  AS inicio_sono,
       sleep_end_time    AS fim_sono
FROM sleep
WHERE substr(sleep_start_time, 1, 10) <> substr(sleep_end_time, 1, 10)
ORDER BY date;

-- 4. O que é o sleep_charge?
-- É a nota que a Polar dá comparando o sono da noite com o meu normal (média dos últimos ~28 dias), numa escala de 1 a 5.
-- A média do sleep_score sobe junto com o grupo (55 -> 62 -> 67 -> 74 -> 78)
-- e as faixas quase não se misturam (só 1/2 e 4/5 se encostam). Com só
-- um mês de dados, meu "normal" quase não mudou, então por enquanto ele é
-- praticamente o sleep_score dividido em faixas. Fica fora da gold.
SELECT sleep_charge,
       COUNT(*) AS noites,
       round(avg(sleep_score),1) AS nota_media,
       max(sleep_score) AS melhor_sono,
       min(sleep_score) AS pior_sono
FROM sleep
GROUP BY sleep_charge
ORDER BY sleep_charge;

-- 5. O total de interrupções é a soma das curtas com as longas?
-- Sim: as 33 noites aparecem no filtro. Então o total não traz informação
-- nova, e vou levar só ele para a gold. Valores em segundos.
SELECT date as data,
    total_interruption_duration as tempo_acordado,
    short_interruption_duration as tempo_curto,
    long_interruption_duration  as tempo_longo
FROM sleep
WHERE (short_interruption_duration+long_interruption_duration)=total_interruption_duration;

-- 6. As datas das tabelas batem?
-- Ter o mesmo número de linhas não prova que as datas são as mesmas, então
-- conferi com LEFT JOIN. Sono e Recharge batem nos dois sentidos (as duas
-- consultas voltam vazias). Por isso a fato_noite junta as duas, com
-- LEFT JOIN a partir do sleep. Na atividade, os dias sem noite são só
-- 27/10 e 31/10, as noites em que esqueci a pulseira.
SELECT sono.date AS data_sono, recuperacao.date AS data_recarga
FROM sleep AS sono
LEFT JOIN nightly_recharge AS recuperacao ON sono.date = recuperacao.date
WHERE recuperacao.date IS NULL;

SELECT sono.date AS data_sono, recuperacao.date AS data_recarga
FROM nightly_recharge AS recuperacao
LEFT JOIN sleep AS sono ON recuperacao.date = sono.date
WHERE sono.date IS NULL;

SELECT atv.date AS data_atividade, sono.date AS data_sono
FROM daily_activity as atv
LEFT JOIN sleep as sono ON atv.date=sono.date
WHERE sono.date is NULL;

-- 7. Dias atípicos no tempo ativo
-- O tempo ativo conta qualquer movimento do dia, não só treino (média de
-- ~5,6 h, de 1,4 h a 10,3 h). Olhei os 5 maiores e os 5 menores:
--   31/10  10,3 h: real, passei o dia limpando a casa depois da festa. Fica.
--   11/10   1,4 h: fiquei sem a pulseira boa parte do dia (sítio). O dado
--          está incompleto, então esse dia sai das análises de atividade.
--   08/11   2,8 h: só um domingo parado mesmo. Fica.
-- Cuidado: se o sync for no meio do dia, o último dia vem incompleto.
SELECT dia,
       ROUND(tempo_ativo_s / 3600.0, 1) AS horas_ativas
FROM fato_dia
ORDER BY horas_ativas DESC
LIMIT 5;

SELECT dia,
       ROUND(tempo_ativo_s / 3600.0, 1) AS horas_ativas
FROM fato_dia
ORDER BY horas_ativas
LIMIT 5;