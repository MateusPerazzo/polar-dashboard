-- fato_dia: uma linha por dia, com a atividade.
--
-- O tempo ativo vem em segundos e conta qualquer movimento do dia, não só
-- treino (média de ~5,6 h).
--
-- Dias para lembrar nas análises (ver seção 7 do diagnóstico):
--   11/10  fiquei sem a pulseira boa parte do dia (sítio): os valores estão
--          incompletos, então esse dia sai das análises de atividade
--   31/10  10,3 h ativas, valor real (limpeza depois da festa), então fica
--   último dia: se o sync for no meio do dia, ele vem incompleto

DROP VIEW IF EXISTS fato_dia;

CREATE VIEW fato_dia AS
    SELECT date as dia,
        steps as passos,
        active_calories as calorias_ativas,
        active_duration_s as tempo_ativo_s
    FROM daily_activity;