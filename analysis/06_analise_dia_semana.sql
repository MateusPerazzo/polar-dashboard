-- Análise 2: o dia da semana muda o meu sono?
--
-- Montei no formato de uma questão de prova técnica (parecida com a da PwC):
--   - a noite é atribuída ao dia em que fui dormir, e não ao dia em que
--     acordei (a date do sono). Por isso o JOIN é d.dia + 1 dia;
--   - os dias sem noite registrada contam no calendário, mas não entram
--     na média: COUNT(d.dia) conta os dias e COUNT(fn.dia) só as noites
--     (o AVG já ignora os NULL, então não precisa de WHERE);
--   - a ordem é da semana (numero_dia), e não alfabética.
--
-- Resultado em 10/11/2026 (41 dias, 38 noites):
--
--   noite     noites   nota média   horas na cama
--   segunda      5        67,0          6,7
--   terça        5        72,4          7,5    <- melhor nota
--   quarta       5        68,0          7,0
--   quinta       6        60,2          5,9    <- pior nota e noite mais curta
--   sexta        5        69,2          8,8
--   sábado       6        66,3          9,3
--   domingo      6        67,3          6,7
--
-- A noite de quinta para sexta ficou bem abaixo das outras (7 a 12 pontos).
-- Minha hipótese: as manhãs de quarta (aula online, sem deslocamento) e de
-- quinta (sem a primeira aula) me deixam acordar mais tarde, mas na sexta
-- tenho todas as aulas e cerca de 1 hora de deslocamento.
--
-- Testei três previsões:
--   1. "Na quinta eu vou dormir mais tarde": NÃO se confirmou. Foi o
--      contrário: nas quintas eu durmo mais cedo e com mais regularidade
--      (sempre entre 23h45 e 00h27) do que nas terças e quartas.
--   2. "Na sexta eu acordo mais cedo": confirmou. Nas 6 sextas acordei
--      entre 05h56 e 06h10, e as noites ficaram com 5,7 a 6,2 h na cama.
--      Nas manhãs de quarta acordei em média ~08h30 e nas de quinta
--      ~07h30.
--   3. "O problema é acordar às 6h": NÃO se confirmou. Nas segundas
--      normais (sem contar os feriados de 12/10 e 02/11) eu também acordo
--      às 6h, com ainda menos horas na cama (5,6 h em média), e a nota é
--      melhor (66, contra 60 da noite de quinta). E no domingo eu não vou
--      dormir mais cedo: fui dormir entre 23h24 e 01h06, mais tarde que
--      nas quintas. Nas terças o horário de acordar varia; duas das que
--      fugiram das 6h vieram logo depois dos feriados.
--
-- Conclusão: a noite de quinta continua sendo a pior, mas nem acordar às
-- 6h nem dormir pouco explicam isso sozinhos, porque a noite de domingo
-- tem as duas coisas e vai melhor. A causa ainda está em aberto. Tenho
-- duas hipóteses:
--   - a mudança de horário: na quarta e na quinta acordo mais tarde, e
--     na sexta preciso voltar para as 6h;
--   - o cansaço acumulado: a quinta é o fim de uma semana de aulas, e a
--     noite de domingo vem depois de um fim de semana de noites longas.
-- Com 6 quintas e 4 segundas normais, não dá para separar uma da outra.
-- Vou testar ir dormir uma hora mais cedo nas quintas e ver se a nota
-- melhora.
-- Também apareceu que mais horas não garantem a melhor nota: o sábado tem
-- a noite mais longa (9,3 h), mas nota menor que a de terça. Talvez a
-- regularidade do horário importe também, o que combina com a hipótese da
-- rotina da análise 1. Ainda são só 5 ou 6 noites por dia da semana.
--
-- Diferente das outras views (a camada gold), esta é um resultado de
-- análise, montado em cima da gold. Para ver na ordem certa:
--   SELECT * FROM resumo_dia_semana ORDER BY numero_dia;

DROP VIEW IF EXISTS resumo_dia_semana;

CREATE VIEW resumo_dia_semana AS
SELECT d.numero_dia,
        d.dia_semana,
       COUNT(d.dia) AS dias_calendario,
       COUNT(fn.dia) AS noites_registradas,
       ROUND(AVG(fn.nota_sono), 1) AS nota_media,
       round(AVG(fn.horas_na_cama),1) as media_horas_na_cama
FROM dim_data AS d
LEFT JOIN fato_noite AS fn ON fn.dia = date(d.dia, '+1 day')
GROUP BY d.numero_dia, d.dia_semana;


-- Teste 1: nas noites de quinta eu vou dormir mais tarde?
-- Comparo com as noites de terça e quarta.
SELECT d.dia_semana                   AS noite,
       d.dia                          AS dia_dormiu,
       substr(fn.inicio_sono, 12, 5)  AS dormiu,
       fn.nota_sono
FROM dim_data AS d
LEFT JOIN fato_noite AS fn ON fn.dia = date(d.dia, '+1 day')
WHERE d.numero_dia IN (2, 3, 4)       -- terça, quarta e quinta
ORDER BY d.numero_dia, d.dia;


-- Teste 2: na sexta eu acordo mais cedo?
-- Aqui o dia da semana é o da manhã em que ACORDEI (a date do sleep),
-- por isso o JOIN com a dim_data não tem deslocamento.
SELECT d.dia_semana                              AS manha,
       s.date                                    AS dia_acordou,
       substr(s.sleep_start_time, 12, 5)         AS dormiu,
       substr(s.sleep_end_time, 12, 5)           AS acordou,
       ROUND((julianday(s.sleep_end_time)
            - julianday(s.sleep_start_time)) * 24, 1) AS horas_na_cama,
       s.sleep_score                             AS nota_sono
FROM sleep AS s
JOIN dim_data AS d ON d.dia = s.date
WHERE d.numero_dia IN (3, 4, 5)  
ORDER BY d.numero_dia, s.date;


-- Teste 3: o problema é acordar às 6h?
-- Mostra as manhãs de segunda a sexta lado a lado. Na segunda eu também
-- acordo às 6h; comparo essas noites com as de quinta para sexta.
-- (como no teste 2, o dia da semana é o da manhã em que ACORDEI)
SELECT d.dia_semana                              AS manha,
       s.date                                    AS dia_acordou,
       substr(s.sleep_start_time, 12, 5)         AS dormiu,
       substr(s.sleep_end_time, 12, 5)           AS acordou,
       ROUND((julianday(s.sleep_end_time)
            - julianday(s.sleep_start_time)) * 24, 1) AS horas_na_cama,
       s.sleep_score                             AS nota_sono
FROM sleep AS s
JOIN dim_data AS d ON d.dia = s.date
WHERE d.numero_dia IN (1, 2, 3, 4, 5)   -- manhãs de segunda a sexta
ORDER BY d.numero_dia, s.date;
