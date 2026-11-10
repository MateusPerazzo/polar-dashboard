-- Análise 1: a atividade do dia influencia o sono da noite seguinte?
--
-- A date do sono é o dia em que acordo, então junto a atividade do dia D
-- com a noite D+1 (date(dia, '+1 day') no JOIN). Ficam de fora:
--   - o 11/10, em que fiquei sem a pulseira boa parte do dia
--   - os dias sem a noite seguinte registrada (26/10, 30/10 e o último dia)
-- Separei os dias em três faixas de passos, com limites escolhidos para os
-- grupos ficarem com tamanhos parecidos (nov/2026; revisar com mais dados).
--
-- Resultado (nota média do sono na noite seguinte):
--   atividade baixa (menos de 3.500 passos):  11 dias, 65,2
--   atividade média (3.500 a 5.499):          12 dias, 66,2
--   atividade alta  (5.500 ou mais):          13 dias, 68,0
--
-- Conclusão: foi possível observar uma tendência de que, em média, nos dias
-- em que estou mais ativo, acabo dormindo melhor na noite seguinte. Mas a
-- diferença é pequena (2,8 pontos, enquanto minhas notas variam de 52 a 80)
-- e são só 36 dias, então ainda não dá para afirmar que a atividade melhora
-- o sono. Também pode haver outras explicações, como a rotina dos dias mais
-- ativos. Vou repetir a análise com mais dados.

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
    END as faixa_de_atv
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