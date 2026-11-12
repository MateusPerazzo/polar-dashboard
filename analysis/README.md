# Análises: o que os meus dados de sono contam

## A pergunta
Quis entender melhor a minha rotina, o meu sono e a minha recuperação:
onde eu estava errando, onde estava acertando e o que dá para melhorar.
Ao mesmo tempo, este é um projeto de estudo de modelagem e análise de
dados, a área em que quero trabalhar. É um estudo exploratório: as
conclusões são hipóteses bem fundamentadas, não verdades estatísticas.

## Os dados
Uso os dados da minha própria pulseira, a Polar Loop, obtidos pela API da
Polar: sono, recuperação noturna (HRV e Nightly Recharge) e atividade
diária. São cerca de 6 semanas (01/10 a 10/11/2026), com 39 noites
registradas.

Escolhi dados meus, e não um banco público qualquer, porque estudar algo
que faz parte da minha rotina é mais interessante, e o resultado me
ajuda de verdade.

## Como eu organizei
Montei o estudo seguindo práticas que profissionais da área usam hoje
em projetos de dados, em quatro etapas:

**1. Diagnóstico dos dados brutos** ([00_diagnostico.sql](00_diagnostico.sql))
Antes de analisar, conferi a qualidade dos dados: tipos (`typeof`),
valores vazios, dias faltando e valores fora do normal. Separei o que
era erro de medição (noites sem a pulseira) do que era um dia atípico
de verdade, que precisa ficar na análise.

**2. Arquitetura em camadas e modelo estrela** ([01_modelo.md](01_modelo.md))
Me inspirei na **arquitetura medalhão**, que separa os dados em camadas
conforme o nível de tratamento:

- **bronze e prata:** as tabelas que o meu código grava a partir da API.
  Elas já chegam com uma limpeza básica (sem registros duplicados,
  leituras de frequência cardíaca iguais a zero descartadas e horários
  da noite reconstruídos). Num projeto deste tamanho, as duas camadas
  ficam juntas;
- **ouro (gold):** a camada de análise, montada como um **modelo
  estrela**, que é a única que as análises leem.

O modelo estrela tem uma tabela de calendário e duas tabelas de fatos,
cada uma com a sua granularidade bem definida:

- `dim_data`: o calendário (dia, mês, dia da semana), gerado com uma
  CTE recursiva e compartilhado pelas duas tabelas de fatos;
- `fato_noite`: uma linha por noite (nota do sono, recuperação, HRV,
  horários);
- `fato_dia`: uma linha por dia (passos, calorias, tempo ativo).

Tudo foi feito com views em SQL, então as análises sempre leem os dados
mais recentes.

**3. Consultas avançadas em SQL**
- CTEs em sequência e CTE recursiva;
- funções de janela: `ROW_NUMBER`, `COUNT OVER`, `PARTITION BY` e
  `AVG OVER` com `ROWS BETWEEN` (média móvel);
- mediana calculada em SQL puro, que não tem uma função pronta para isso;
- JOINs com datas deslocadas (a atividade de um dia com o sono da noite
  seguinte) e cálculos com datas e horários que passam da meia-noite.

**4. Método de análise**
Cada análise segue o ciclo **padrão → hipótese → teste → conclusão**:
- faixas com quantidades parecidas (tercis), para comparar grupos de
  forma justa;
- mediana em vez de média quando a nota é uma escala de níveis;
- **estratificação** para achar variáveis de confusão (foi assim que o
  dia da semana apareceu por trás do horário de dormir);
- **análise de sensibilidade**, para conferir se um resultado se mantém
  com mais dados;
- conclusões sempre com números, tamanho da diferença e limitações.

## O que eu descobri

| # | pergunta | resposta curta |
|---|---|---|
| 1 | [Se mexer mais melhora o sono?](05_analise_atividade_sono.sql) | Não apareceu relação clara: as diferenças entre dias parados e ativos foram de no máximo 3,4 pontos, numa nota que varia de 52 a 80. |
| 2 | [O dia da semana muda o sono?](06_analise_dia_semana.sql) | A noite de quinta é a pior (nota 60,2, contra 72,4 da terça). Na sexta acordo às 6h, depois de manhãs por volta das 8h30 na quarta e das 7h30 na quinta. Mas o motivo não é só acordar cedo ou dormir pouco: nas segundas normais (sem contar 2 feriados) também acordo às 6h, com ainda menos horas na cama (5,6 h), e a nota é melhor (66). A causa ainda está em aberto: pode ser a mudança de horário ao longo da semana ou o cansaço acumulado até a quinta. |
| 3 | [Dormir mais tarde piora a recuperação?](07_analise_hora_de_dormir.sql) | Sozinho, não. O que pesou foi o dia da semana: nas noites de sexta e sábado, sem rotina, a recuperação foi ruim em qualquer horário. Tirando essas noites, as noites em que fui dormir mais tarde tiveram a melhor recuperação (+7,8, contra +1,1 das que fui dormir mais cedo, numa escala de -10 a +10), porque vinham antes de manhãs em que eu podia acordar mais tarde. |
| 4 | [Como o meu HRV evoluiu?](08_analise_hrv.sql) | Acompanhei o HRV (variabilidade da frequência cardíaca: quanto mais alto em relação ao meu normal, melhor a recuperação) pela média das últimas 7 noites. Ela ficou estável em ~95 ms, caiu para 86 no fim de outubro, num período fora da rotina, e subiu até 113 em novembro, o maior valor do período. |

## O fio condutor
As análises apontam para o mesmo lado: **a regularidade da rotina parece
pesar mais do que qualquer fator isolado**, como se mexer mais ou dormir
cedo. As noites de sexta e sábado, sem rotina, tiveram recuperação ruim
em qualquer horário, e a queda do HRV aconteceu num período fora da
rotina. A noite de quinta, a pior da semana, ainda não tem uma
explicação fechada.

## Limitações
- **Uma pessoa só:** os resultados valem para mim, não para outras
  pessoas.
- **Pouco tempo:** 39 noites. Cada dia da semana tem só 5 ou 6 noites, e
  não dá para falar em padrão que se repete.
- **Causa:** os dados mostram o que acontece junto, não o que causa o
  quê. Por isso as conclusões são hipóteses a testar.

## Próximos passos
- Deixar os horários mais regulares: testar ir dormir uma hora mais cedo
  nas quintas e ver se a nota da noite melhora.
- Anotar os eventos fora da rotina (festas, provas, treinos pesados),
  para conseguir explicar as quedas.
- Continuar coletando dados e refazer as análises com alguns meses.
