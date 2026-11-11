-- Análise 3: o horário em que vou dormir afeta a minha recuperação?
--
-- O QUE EU MEDI
-- A Polar dá duas notas para a recuperação de cada noite:
--   - carga do sistema nervoso: vai de -10 a +10. O 0 quer dizer "igual
--     ao meu normal"; positivo é melhor que o normal, negativo é pior.
--   - status de recuperação: uma nota de 1 (muito ruim) a 6 (muito bom).
--     Como é uma escala de níveis, e não uma medida exata, eu a resumo
--     pela mediana (a nota da noite que fica no meio, quando coloco todas
--     em ordem), e não pela média.
--
-- COMO EU FIZ
-- 1. Transformei o horário de dormir em minutos, para poder comparar.
--    Os horários da madrugada ganham 24 horas a mais; assim, 00h30 conta
--    como mais tarde que 23h30, como acontece na vida real.
-- 2. Separei as noites em três grupos com quantidades parecidas:
--      cedo:  antes das 00h25         (14 noites)
--      médio: de 00h25 até 01h24      (13 noites)
--      tarde: 01h25 ou mais           (12 noites)
--
-- RESULTADO (11/11/2026, 39 noites)
--
--   grupo    noites   sistema nervoso (média)   status (mediana)
--   cedo       14            -0,4                 entre 3 e 4
--   médio      13            +2,5                      4
--   tarde      12            -0,3                      4
--
-- À primeira vista, dormir mais tarde não piora a recuperação: os três
-- grupos ficaram parecidos.
--
-- O DIA DA SEMANA ESTAVA ATRAPALHANDO A COMPARAÇÃO
-- Quando separei também pelo dia da semana, ficou claro que ele pesa mais
-- do que o horário:
--   - nas noites de sexta e sábado, a recuperação foi ruim em qualquer
--     horário (entre -3,6 e -9,8). Nesses dias eu não tenho rotina: saio,
--     durmo tarde e não tenho horário certo.
--   - o grupo "tarde" mistura dois tipos de noite bem diferentes: 4 noites
--     de sábado com status 1 (o pior) e 8 noites de dias de semana com
--     status de 4 a 6. Por isso a mediana dele (4) engana: ela fica no
--     meio dos dois tipos e não representa nenhum deles.
--   - o grupo "cedo" tem 5 noites de quinta, quase todas com recuperação
--     ruim.
--
-- Tirando as noites de sexta e sábado (sobram 27), a recuperação ficou:
-- cedo +1,1, médio +3,0 e tarde +7,8. As noites em que durmo mais tarde
-- são principalmente as de terça e quarta. Nas manhãs seguintes eu posso
-- acordar mais tarde (aula online na quarta, sem a primeira aula na
-- quinta). Já na quinta eu durmo mais cedo, mas na sexta acordo às 6h.
--
-- CONCLUSÃO
-- O horário em que vou dormir, sozinho, não decide como eu me recupero.
-- O que parece pesar mais é:
--   1. o horário em que preciso acordar, e se ele combina com a minha
--      rotina;
--   2. a falta de rotina nas noites de sexta e sábado.
-- Isso combina com o que apareceu nas análises 1 e 2. Mas ainda são
-- poucas noites (só 5 noites "tarde" em dias de semana), então é uma
-- hipótese a confirmar com mais dados, não uma certeza.
--
-- OBSERVAÇÃO
-- A noite registrada em 01/10 (em que fui dormir no dia 30/09) não entra
-- nas consultas que usam o dia da semana, porque o meu calendário começa
-- em 01/10.


-- Consulta 1: a recuperação do sistema nervoso em cada grupo de horário
WITH analise3 as(
    SELECT dia,
        status_recuperacao,
        substr(inicio_sono, 12,5) as inicio_sono, recuperacao_sistema_nervoso,
        CASE
        WHEN (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2))<600 THEN (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2)+1440)
        ELSE (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2))
        END as minutos_dormir
        FROM fato_noite
)
SELECT count(a.dia) as noites,
    round(avg(a.recuperacao_sistema_nervoso),1) as media_rec_snc,
    CASE
    WHEN a.minutos_dormir<1465 THEN 'cedo(antes das 00h25)'
    WHEN a.minutos_dormir<1525 THEN 'médio(00h25-01h24)'
    ELSE 'tarde(01h25 ou mais)'
    END as zona_dormiu
FROM analise3 as a
GROUP by zona_dormiu
ORDER by MIN(a.minutos_dormir);


-- Consulta 2: cada grupo de horário separado pelo dia da semana
-- (o dia em que fui dormir, e não o dia em que acordei)
WITH analise3 as(
    SELECT dia,
        status_recuperacao,
        substr(inicio_sono, 12,5) as inicio_sono, recuperacao_sistema_nervoso,
        CASE
        WHEN (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2))<600 THEN (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2)+1440)
        ELSE (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2))
        END as minutos_dormir
        FROM fato_noite
)
SELECT count(a.dia) as noites,
    round(avg(a.recuperacao_sistema_nervoso),1) as media_rec_snc,
    CASE
    WHEN a.minutos_dormir<1465 THEN 'cedo(antes das 00h25)'
    WHEN a.minutos_dormir<1525 THEN 'médio(00h25-01h24)'
    ELSE 'tarde(01h25 ou mais)'
    END as zona_dormiu,
    d.dia_semana
FROM analise3 as a
INNER JOIN dim_data as d on a.dia=date(d.dia, '+1 day')
GROUP by zona_dormiu,dia_semana
ORDER by d.numero_dia;


-- Consulta 3: os mesmos grupos, sem as noites de sexta e sábado
WITH analise3 as(
    SELECT dia,
        status_recuperacao,
        substr(inicio_sono, 12,5) as inicio_sono, recuperacao_sistema_nervoso,
        CASE
        WHEN (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2))<600 THEN (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2)+1440)
        ELSE (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2))
        END as minutos_dormir
        FROM fato_noite
)
SELECT count(a.dia) as noites,
    round(avg(a.recuperacao_sistema_nervoso),1) as media_rec_snc,
    CASE
    WHEN a.minutos_dormir<1465 THEN 'cedo(antes das 00h25)'
    WHEN a.minutos_dormir<1525 THEN 'médio(00h25-01h24)'
    ELSE 'tarde(01h25 ou mais)'
    END as zona_dormiu
FROM analise3 as a
INNER JOIN dim_data as d on a.dia=date(d.dia, '+1 day')
WHERE d.numero_dia in (1,2,3,4,7)
GROUP by zona_dormiu
ORDER by MIN(a.minutos_dormir);


-- Consulta 4: quantas noites de cada status (1 a 6) há em cada grupo
WITH analise3 as(
    SELECT dia,
        status_recuperacao,
        substr(inicio_sono, 12,5) as inicio_sono, recuperacao_sistema_nervoso,
        CASE
        WHEN (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2))<600 THEN (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2)+1440)
        ELSE (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2))
        END as minutos_dormir
        FROM fato_noite
)
SELECT count(a.dia) as noites,
    CASE
    WHEN a.minutos_dormir<1465 THEN 'cedo(antes das 00h25)'
    WHEN a.minutos_dormir<1525 THEN 'médio(00h25-01h24)'
    ELSE 'tarde(01h25 ou mais)'
    END as zona_dormiu,
    status_recuperacao
FROM analise3 as a
GROUP by zona_dormiu,status_recuperacao
ORDER by zona_dormiu,status_recuperacao;


-- Consulta 5: a mediana do status em cada grupo
-- O SQLite não tem uma função pronta para a mediana, então eu a calculei
-- em três passos:
--   1. numerei as noites de cada grupo, da pior nota para a melhor
--      (ROW_NUMBER com PARTITION BY);
--   2. contei quantas noites cada grupo tem (COUNT OVER);
--   3. fiquei só com a noite do meio. Quando o grupo tem um número par de
--      noites, são duas no meio, e eu faço a média delas. As contas
--      (total + 1) / 2 e (total + 2) / 2 encontram essas posições.
-- No grupo "cedo", as duas noites do meio têm notas 3 e 4, e a média dá
-- 3,5. Como o status é uma escala de níveis, na conclusão escrevo
-- "entre 3 e 4".
WITH analise3 as(
    SELECT dia,
        status_recuperacao,
        substr(inicio_sono, 12,5) as inicio_sono, recuperacao_sistema_nervoso,
        CASE
        WHEN (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2))<600 THEN (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2)+1440)
        ELSE (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2))
        END as minutos_dormir
        FROM fato_noite
),
analise4 as(
    SELECT dia,
        status_recuperacao,
        CASE
        WHEN minutos_dormir<1465 THEN 'cedo(antes das 00h25)'
        WHEN minutos_dormir<1525 THEN 'médio(00h25-01h24)'
        ELSE 'tarde(01h25 ou mais)'
        END as zona_dormiu
        FROM analise3
),
analise5 as(
    SELECT dia,
        status_recuperacao,
        zona_dormiu,
        ROW_NUMBER() OVER (PARTITION BY zona_dormiu ORDER by status_recuperacao) as posicao_faixa,
        COUNT(*) OVER (PARTITION BY zona_dormiu) as total_faixa
        FROM analise4
)
SELECT
    zona_dormiu,
    total_faixa,
    round(avg(status_recuperacao),1) as mediana
FROM analise5
WHERE posicao_faixa = (total_faixa + 1) / 2 or posicao_faixa = (total_faixa + 2) / 2
GROUP by zona_dormiu, total_faixa;