-- dim_data: o calendário da camada gold, com uma linha por dia.
--
-- Gera todos os dias entre a primeira e a última data da daily_activity
-- (é a tabela com o maior período). Usei CTE recursiva em vez de pegar as
-- datas das tabelas porque assim os dias sem registro, como 27/10 e 31/10,
-- também entram, e o calendário fica sem buracos. As datas vêm de
-- subconsultas, então depois de cada sync ele já acompanha os dados novos.
--
-- Colunas:
--   dia          a data, chave para ligar com os fatos
--   ano_mes      ex.: 2026-10
--   numero_dia   segunda = 1 ... domingo = 7 (padrão ISO). O strftime('%w')
--                usa domingo = 0 e devolve texto, então converti com CASE + CAST
--   dia_semana   nome do dia, para ler o resultado
--
-- Por enquanto é só o SELECT. Depois vira view com CREATE VIEW.

WITH RECURSIVE calendario(dia) AS ( --Cria minha CTE
    SELECT (SELECT (min(date)) FROM daily_activity) AS dia    
    UNION ALL
    SELECT date(dia,'+1 day')                  
    FROM calendario
    WHERE dia<(SELECT(max(date)) FROM daily_activity)                   
)
SELECT dia,strftime('%Y-%m', dia) AS  ano_mes,
	CASE 
		WHEN strftime('%w', dia)= '0' THEN 7 
		ELSE CAST(strftime('%w', dia) AS INTEGER)
	END AS numero_dia,
	CASE strftime('%w', dia)
    	WHEN '1' THEN 'Segunda'
		WHEN '2' THEN 'Terça'
		WHEN '3' THEN 'Quarta'
		WHEN '4' THEN 'Quinta'
		WHEN '5' THEN 'Sexta'
		WHEN '6' THEN 'Sábado'
		WHEN '0' THEN 'Domingo'
    	ELSE 'erro'
	END	AS dia_semana
FROM calendario;