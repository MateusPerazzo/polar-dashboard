-- Diagnóstico dos dados antes de montar a camada gold.

-- 1. Quanto dado eu tenho
-- 32 noites (sono e recharge) e 34 dias de atividade, de 01/10 a 03/11.
-- Faltam 2 noites (27/10 e 31/10). Pouco dado ainda, então as análises
-- vão ser mais exploratórias.
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
