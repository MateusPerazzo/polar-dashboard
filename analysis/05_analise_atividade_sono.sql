-- Análise 1: a atividade do dia influencia o sono da noite seguinte?
--
-- A date do sono é o dia em que acordo, então junto a atividade do dia D
-- com a noite D+1 (date(dia, '+1 day') no JOIN). Ficam de fora:
--   - o 11/10, em que fiquei sem a pulseira boa parte do dia
--   - os dias sem a noite seguinte registrada (26/10, 30/10 e o último dia)
-- Medi a atividade de dois jeitos: pelos passos e pelo tempo ativo (que
-- também pega atividades com poucos passos, como bicicleta). Em cada um,
-- separei os dias em três faixas com tamanhos parecidos (limites de
-- nov/2026; revisar com mais dados).
--
-- Resultado (nota média do sono na noite seguinte):
--
-- Por passos               09/11 (36 dias)    10/11 (37 dias)
--   baixa (< 3.500)          11 dias, 65,2      12 dias, 66,3
--   média (3.500 a 5.499)    12 dias, 66,2      12 dias, 66,2
--   alta  (5.500 ou mais)    13 dias, 68,0      13 dias, 68,0
--
-- Por tempo ativo                             10/11 (37 dias)
--   baixa (< 4,7 h)                             12 dias, 68,3
--   média (4,7 a 6,49 h)                        12 dias, 64,9
--   alta  (6,5 h ou mais)                       13 dias, 67,3
--
-- Com 36 dias, os passos pareciam mostrar uma leve tendência: quanto mais
-- ativo, melhor o sono. Mas bastou um dia a mais (09/11, um dia parado
-- seguido de uma noite boa) para a diferença entre as faixas baixa e média
-- sumir. E pelo tempo ativo não aparece tendência nenhuma.
--
-- Conclusão: nos meus dados, não existe uma relação clara de "quanto mais
-- ativo, melhor o sono". As diferenças entre as faixas são pequenas (até
-- 3,4 pontos, enquanto minhas notas variam de 52 a 80) e as duas medidas
-- de atividade não contam a mesma história.
--
-- Uma hipótese: pelo tempo ativo, as noites depois dos dias mais parados e
-- dos dias mais ativos tiveram notas melhores que as dos dias "no meio".
-- Talvez eu durma melhor nos dias com uma rotina mais definida, seja de
-- descanso ou de atividade. Ainda são poucos dados para concluir, mas é
-- uma boa pergunta para investigar com mais tempo de coleta.


-- Consulta 1: faixas por passos
WITH comparacao_sono_atividade AS (
    SELECT fd.dia as dia_atividade,
        passos,
        ROUND((tempo_ativo_s/3600.0), 1) as tempo_ativo_h,
        fn.dia as noite,
        fn.nota_sono,
    CASE
    WHEN passos<3500 THEN 'atividade_baixa'
    WHEN passos<5500 THEN 'atividade_media'
    ELSE 'atividade_alta'
    END as faixa_de_atv ,
    CASE
    WHEN (tempo_ativo_s/3600.0)< 4.7 THEN 'horas_atv_baixa'
    WHEN (tempo_ativo_s/3600.0)< 6.50 THEN 'horas_atv_media'
    ELSE 'horas_atv_alta'
    END as faixa_horas_atv
    FROM fato_dia as fd
    LEFT JOIN fato_noite as fn ON fn.dia=date(fd.dia,'+1 day')
    WHERE (dia_atividade<>'2026-10-11') AND (noite is NOT NULL)
)
SELECT faixa_de_atv,
        count(*) as dias,
        round(avg(nota_sono), 1) as nota_media
FROM comparacao_sono_atividade
GROUP BY faixa_de_atv
ORDER BY MIN(passos);


-- Consulta 2: faixas por tempo ativo
-- (a CTE é a mesma: ela só vale para o comando logo depois dela, então
-- precisa ser repetida aqui)
WITH comparacao_sono_atividade AS (
    SELECT fd.dia as dia_atividade,
        passos,
        ROUND((tempo_ativo_s/3600.0), 1) as tempo_ativo_h,
        fn.dia as noite,
        fn.nota_sono,
    CASE
    WHEN passos<3500 THEN 'atividade_baixa'
    WHEN passos<5500 THEN 'atividade_media'
    ELSE 'atividade_alta'
    END as faixa_de_atv ,
    CASE
    WHEN (tempo_ativo_s/3600.0)< 4.7 THEN 'horas_atv_baixa'
    WHEN (tempo_ativo_s/3600.0)< 6.50 THEN 'horas_atv_media'
    ELSE 'horas_atv_alta'
    END as faixa_horas_atv
    FROM fato_dia as fd
    LEFT JOIN fato_noite as fn ON fn.dia=date(fd.dia,'+1 day')
    WHERE (dia_atividade<>'2026-10-11') AND (noite is NOT NULL)
)
SELECT faixa_horas_atv,
        count (*) as dias,
        round(avg(nota_sono), 1) as nota_media
FROM comparacao_sono_atividade
GROUP BY faixa_horas_atv
ORDER BY MIN(tempo_ativo_h);