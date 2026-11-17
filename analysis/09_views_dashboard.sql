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
    -- Período do estudo publicado; para uma nova versão, mudar as datas aqui.
    -- Dentro da CTE: o WHERE roda antes da janela (OVER), então a média
    -- móvel só usa noites do período.
    WHERE dia BETWEEN '2026-10-01' AND '2026-11-10'
)
SELECT dia,
    hrv_medio,
    CASE
    WHEN contagem < 7 THEN NULL
    ELSE ROUND(media_movel, 1)
    END AS media_movel
FROM analise4;


-- Atividade x sono: um ponto por dia (vem da análise 1, 05_analise_atividade_sono.sql)
     DROP VIEW IF EXISTS atividade_sono_dia;

    CREATE VIEW atividade_sono_dia as
    SELECT fd.dia,
        passos,
        ROUND((tempo_ativo_s/3600.0), 1) as tempo_ativo_h,
        fn.nota_sono
    FROM fato_dia as fd
    LEFT JOIN fato_noite as fn ON fn.dia=date(fd.dia,'+1 day')
    -- Período do estudo publicado; para uma nova versão, mudar as datas aqui.
    -- Pela noite seguinte (fn.dia): o último dia é 09/11, cuja noite é a de 10/11.
    WHERE (fd.dia<>'2026-10-11') AND (fn.dia is NOT NULL)
        AND fn.dia BETWEEN '2026-10-01' AND '2026-11-10';





-- Hora de dormir x recuperação: com e sem sexta e sábado (vem da análise 3, 07_analise_hora_de_dormir.sql)
-- Uma linha por faixa de horário, com a recuperação do sistema nervoso
-- de todas as noites e sem as noites de sexta e sábado (sem rotina).
DROP VIEW IF EXISTS hora_dormir_recuperacao;

CREATE VIEW hora_dormir_recuperacao AS
WITH analise3 AS (
    SELECT dia,
        recuperacao_sistema_nervoso,
        CASE
        WHEN (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2))<600 THEN (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2)+1440)
        ELSE (substr(inicio_sono,12,2)*60+substr(inicio_sono,15,2))
        END AS minutos_dormir
    FROM fato_noite
    -- Período do estudo publicado; para uma nova versão, mudar as datas aqui.
    WHERE dia BETWEEN '2026-10-01' AND '2026-11-10'
),
analise4 AS (
    SELECT a.dia,
        a.recuperacao_sistema_nervoso,
        a.minutos_dormir,
        d.numero_dia,
        CASE
        WHEN a.minutos_dormir<1465 THEN 'cedo(antes das 00h25)'
        WHEN a.minutos_dormir<1525 THEN 'médio(00h25-01h24)'
        ELSE 'tarde(01h25 ou mais)'
        END AS zona_dormiu
    FROM analise3 AS a
    LEFT JOIN dim_data AS d ON a.dia = date(d.dia, '+1 day')
)
SELECT zona_dormiu,
    MIN(minutos_dormir) AS minutos_inicio,
    COUNT(*) AS noites_todas,
    ROUND(AVG(recuperacao_sistema_nervoso), 1) AS media_todas,
    COUNT(CASE WHEN numero_dia NOT IN (5, 6) THEN 1 END) AS noites_sem_sex_sab,
    ROUND(AVG(CASE WHEN numero_dia NOT IN (5, 6) THEN recuperacao_sistema_nervoso END), 1) AS media_sem_sex_sab
FROM analise4
GROUP BY zona_dormiu;