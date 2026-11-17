-- Views do dashboard: os dados da página "Análises"
--
-- PARA QUE SERVE ESTE ARQUIVO
-- Os arquivos 05 a 08 são o registro do estudo: mostram como cheguei em
-- cada conclusão. Este arquivo junta as views que a página "Análises" do
-- dashboard lê. Cada view vem de uma análise e entrega os dados prontos
-- para um gráfico; o Python só faz SELECT * FROM view.
--
-- COMO USAR
-- Rodar o arquivo inteiro uma vez no DB Browser (modo normal, não
-- somente leitura) e gravar com Ctrl+S. Pode rodar de novo quando mudar
-- alguma view: cada uma começa apagando a versão antiga (DROP VIEW).
--
-- Uma view não guarda ordem. Quem lê a view é que ordena:
--   SELECT * FROM hrv_media_movel ORDER BY dia;
--
-- VIEWS
--   resumo_dia_semana   -> barras por dia da semana  (criada no 06)
--   hrv_media_movel     -> linha da média + pontos   (vem do 08)
--   atividade_sono_dia  -> dispersão                 (vem do 05)
--   (falta)             -> barras agrupadas da hora de dormir (vem do 07)


-- Dia da semana: a view resumo_dia_semana já foi criada no
-- 06_analise_dia_semana.sql, junto com a análise 2. O dashboard lê assim:
--   SELECT * FROM resumo_dia_semana ORDER BY numero_dia;


-- HRV: a média móvel de 7 noites (vem da análise 4, 08_analise_hrv.sql)
-- Uma linha por noite. A média fica vazia (NULL) enquanto a janela ainda
-- não tem 7 noites, ou seja, de 01/10 a 06/10.
DROP VIEW IF EXISTS hrv_media_movel;

CREATE VIEW hrv_media_movel AS
WITH analise4 AS (
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
FROM analise4;


-- Atividade x sono: um ponto por dia (vem da análise 1, 05_analise_atividade_sono.sql)
-- (a escrever)


-- Hora de dormir x recuperação: com e sem sexta e sábado (vem da análise 3, 07_analise_hora_de_dormir.sql)
-- (a escrever)
