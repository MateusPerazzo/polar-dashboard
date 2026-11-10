# Modelo da camada gold (rascunho)

Colunas de que cada pergunta precisa, de onde vêm e se são medida (número
para calcular) ou atributo (contexto para agrupar).

## 1. A atividade do dia influencia o sono da noite seguinte?

| coluna              | tabela de origem | tipo   |
|---------------------|------------------|--------|
| `steps`             | daily_activity   | medida |
| `active_calories`   | daily_activity   | medida |
| `active_duration_s` | daily_activity   | medida |
| `sleep_score`       | sleep            | medida |

A `date` do sono é o dia em que acordo, então a noite D é comparada com a
atividade do dia D-1.

## 2. O dia da semana muda o meu sono?

| coluna        | tabela de origem               | tipo     |
|---------------|--------------------------------|----------|
| dia da semana | dim_data (calculado da `date`) | atributo |
| `sleep_score` | sleep                          | medida   |

Cuidado: a noite de sexta para sábado tem a data de sábado.

## 3. O horário em que vou deitar afeta a recuperação?

| coluna                    | tabela de origem              | tipo             |
|---------------------------|-------------------------------|------------------|
| faixa da hora de deitar   | sleep (de `sleep_start_time`) | atributo         |
| `nightly_recharge_status` | nightly_recharge              | medida (ordinal) |
| `ans_charge`              | nightly_recharge              | medida           |

O status vai de 1 a 6 e é ordinal: resumir com mediana e distribuição, não
com média. O `ans_charge` é relativo ao meu normal (0 = igual ao usual).
Poucas faixas de horário, porque ainda tenho poucas noites.
A hora de deitar cruza a meia-noite: 00h30 é mais tarde que 23h00, mesmo
sendo um número menor. Tenho que tratar isso ao montar as faixas.

## 4. Como o meu HRV evolui ao longo do tempo?

| coluna                           | tabela de origem | tipo     |
|----------------------------------|------------------|----------|
| `heart_rate_variability_avg`     | nightly_recharge | medida   |
| data (com média móvel de 7 dias) | dim_data         | atributo |

Uso o HRV já resumido por noite, e não a série da `recharge_hrv`, que tem
várias medições por noite.

## Fora da gold (por enquanto)

- `sleep_goal`: nunca mudou.
- `sleep_rating`: nota manual, sem critério e com zeros.
- `sleep_charge`: com um mês de dados, é quase o `sleep_score` em faixas.
- `short_` e `long_interruption_duration`: o total já é a soma delas.
- `calories`: inclui o gasto basal; uso o `active_calories` (a confirmar).
- `distance_from_steps`: calculada a partir dos passos.
- Por enquanto a gold só tem as colunas que as 4 perguntas usam. As outras
  (`deep_sleep`,  `rem_sleep`, `continuity`...) podem entrar depois.

## Modelo estrela

### dim_data (uma linha por data)

| coluna                  | exemplo    | para quê                                          |
|-------------------------|------------|---------------------------------------------------|
| `date`                  | 2026-10-07 | chave, liga com as tabelas de fato                |
| número do dia da semana | 3          | ordenar (segunda = 1 ... domingo = 7, padrão ISO) |
| nome do dia da semana   | quarta     | ler o resultado                                   |
| mês                     | 2026-10    | agrupar no longo prazo                            |

Tirei o "fim de semana": dá para calcular a partir do dia da semana se
precisar. Também não criei uma coluna de semana: para a evolução do HRV,
vou usar a própria data com média móvel de 7 dias, que com pouco dado
mostra mais do que 4 ou 5 pontos semanais.

### fato_noite (uma linha por noite)

`sleep` LEFT JOIN `nightly_recharge` pela `date`. Hoje as datas das duas
batem (conferi com LEFT JOIN nos dois sentidos), mas uma noite curta ou um
atraso na sincronização pode deixar o sono sem Recharge. Com LEFT JOIN a
noite continua lá, só com o Recharge vazio; com JOIN comum ela sumiria.

| coluna                       | origem                   | tipo                    |
|------------------------------|--------------------------|-------------------------|
| `date`                       | sleep                    | chave                   |
| `sleep_score`                | sleep                    | medida                  |
| `nightly_recharge_status`    | nightly_recharge         | medida (ordinal)        |
| `ans_charge`                 | nightly_recharge         | medida                  |
| `heart_rate_variability_avg` | nightly_recharge         | medida                  |
| `sleep_start_time`           | sleep                    | base da hora de deitar  |
| `sleep_end_time`             | sleep                    | base da hora de acordar |
| horas na cama                | calculada (fim − início) | medida                  |

Levo o `sleep_start_time` inteiro; as faixas de horário decido na análise.
O horário de acordar e as horas na cama entraram na análise 2, para testar
se as noites de quinta eram mais curtas (eram: na sexta acordo às 6h).

### fato_dia (uma linha por dia)

| coluna              | origem         | tipo   |
|---------------------|----------------|--------|
| `date`              | daily_activity | chave  |
| `steps`             | daily_activity | medida |
| `active_calories`   | daily_activity | medida |
| `active_duration_s` | daily_activity | medida |

Os dias 26/10 e 30/10 não têm a noite seguinte (faltam as noites de 27/10
e 31/10), então ficam de fora da pergunta 1.