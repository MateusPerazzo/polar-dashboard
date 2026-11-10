-- fato_noite: uma linha por noite, com o sono e o Nightly Recharge juntos.
--
-- A date do sono é o dia em que acordo. Uso LEFT JOIN a partir do sleep:
-- hoje todas as noites têm Recharge (conferi na seção 6 do diagnóstico),
-- mas se um dia faltar (noite curta, atraso no sync), a noite continua
-- aqui, só com o Recharge vazio.
-- Conferência: o número de linhas tem que ser igual ao de noites do sleep.
--
-- Noites que não existem aqui: 27/10 e 31/10. Nas duas eu esqueci de
-- colocar a pulseira para dormir (a de 31/10 foi depois da festa de
-- Halloween, que acabou às 5h). Não foram tiradas por mim.
--
-- fim_sono e horas_na_cama entraram depois, na análise 2, para testar se
-- as noites de quinta eram mais curtas. horas_na_cama é o tempo entre
-- dormir e acordar (com os despertares no meio). O julianday transforma a
-- data em número de dias, então a conta funciona mesmo cruzando a
-- meia-noite; * 24 passa de dias para horas. Fica sem ROUND aqui: cada
-- análise arredonda só na hora de mostrar.

DROP VIEW IF EXISTS fato_noite;

CREATE VIEW fato_noite AS
SELECT s.date AS dia,
    s.sleep_score AS nota_sono,
    n.nightly_recharge_status AS status_recuperacao,
    n.ans_charge AS recuperacao_sistema_nervoso,
    n.heart_rate_variability_avg as hrv_medio,
    s.sleep_start_time AS inicio_sono,
    s.sleep_end_time as fim_sono,
    ((julianday(s.sleep_end_time)- julianday(s.sleep_start_time)) * 24) AS horas_na_cama
FROM sleep as s
LEFT JOIN nightly_recharge as n on s.date=n.date;