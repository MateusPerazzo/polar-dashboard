-- Análise 4: como o meu HRV evoluiu ao longo do tempo?
--
-- O QUE EU MEDI
-- O HRV (variabilidade da frequência cardíaca) mede quanto o intervalo
-- entre uma batida do coração e a seguinte varia, durante o sono, em ms.
-- Ele é muito pessoal: só faz sentido comparar com o meu próprio normal.
-- Mais alto que o normal = recuperação melhor; mais baixo = pior.
--
-- COMO EU FIZ
-- O HRV oscila muito de uma noite para a outra (de 58 a 140). Para ver a
-- tendência, usei a média móvel de 7 noites: a média de cada noite com as
-- 6 anteriores. As 6 primeiras noites ficam sem média, porque ainda não
-- existem 7 noites para calcular.
--
-- RESULTADO (12/11/2026, 39 noites, de 01/10 a 10/11)
--
--   momento    período           média de 7 noites
--   normal     07/10 a 20/10        93 a 97 ms
--   pico       22/10 a 24/10      cerca de 110 ms
--   vale       02/11                    86 ms
--   fim        10/11                   113 ms   <- o mais alto
--
-- CONCLUSÃO
-- O HRV ficou estável em outubro, caiu cerca de 24 ms no fim do mês e se
-- recuperou com força em novembro, terminando acima do pico anterior.
-- A queda coincide com a semana em que eu organizava uma festa, fora da
-- rotina, o que combina com as análises 1, 2 e 3: a rotina pesa mais do
-- que qualquer fator isolado. Também as duas noites com o HRV mais baixo
-- (58 e 63) começaram num sábado.
-- Mas é uma hipótese: os dados mostram quando o HRV caiu, não por quê, e
-- 5 semanas não bastam para saber se isso se repete. A partir de agora
-- vou anotar os eventos fora da rotina, para ter com o que comparar.
--
-- OBSERVAÇÃO
-- As noites de 27/10 e 31/10 não foram registradas e caem dentro do vale,
-- que pode ter sido ainda mais fundo. A média conta 7 noites registradas,
-- e não 7 dias: em 01/11, por exemplo, ela vai de 24/10 a 01/11.


-- Consulta: HRV de cada noite e a média móvel de 7 noites
-- (a CTE calcula a média e conta quantas noites entraram nela; fora dela,
-- a média só aparece quando a janela tem as 7 noites)
WITH analisehrv AS (
    SELECT dia,
        hrv_medio,
        AVG(hrv_medio) OVER (ORDER BY dia ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS media_movel,
        COUNT(*) OVER (ORDER BY dia ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS contagem
    FROM fato_noite
)
SELECT dia,
    hrv_medio,
    CASE
    WHEN contagem < 7 THEN NULL
    ELSE ROUND(media_movel, 1)
    END AS media_movel
FROM analisehrv
ORDER BY dia;
