# Dashboard Polar Loop

Dashboard local em Python para visualizar meus dados do Polar Loop (sono, frequência cardíaca, HRV e calorias), obtidos pela API AccessLink da Polar. Quando o projeto terminar, o código vai ser publicado em um repositório **público no GitHub**.

## Objetivo principal: aprender

Este projeto existe para eu aprender, não apenas para ter o dashboard pronto. Por isso:

- **Explique cada decisão antes de executá-la**: o que vai ser feito, por quê e quais alternativas existiam.
- **Não escreva código sem eu pedir explicitamente.** Sugerir, explicar conceitos e mostrar o caminho pode. Criar ou editar arquivos de código, só quando eu pedir.
- Prefira passos pequenos e incrementais a entregar muita coisa de uma vez.
- Quando houver um conceito novo (OAuth2, HTTP, pandas, etc.), explique de forma breve e aponte a documentação oficial.
- Se eu tomar uma decisão ruim, diga, mas a decisão final é minha.

## Contexto técnico

- **Sistema:** Windows 11. O dashboard roda localmente e não é hospedado em servidor.
- **Linguagem:** Python.
- **Fonte de dados:** API Polar AccessLink v3. Doc oficial: https://www.polar.com/accesslink-api/

### O que sabemos sobre a AccessLink (a confirmar na documentação)

- O cliente da API é registrado em https://admin.polaraccesslink.com, onde se obtêm `client_id` e `client_secret`.
- A autenticação usa **OAuth2 (authorization code flow)**. Depois de obter o token, é preciso **registrar o usuário** na API antes de acessar os dados.
- Endpoints relevantes para este projeto: sono, Nightly Recharge (HRV), frequência cardíaca contínua e atividade diária (calorias).
- Alguns dados (atividade/exercícios) usam um **modelo de transações**: os dados novos são "consumidos" e, depois do commit, não aparecem de novo. Isso influencia a necessidade de armazenar os dados localmente.

## Segurança e privacidade (o repositório será público)

Nada sensível pode chegar ao GitHub. Isso inclui tanto credenciais quanto meus dados de saúde.

- **Credenciais** (`client_id`, `client_secret`, access token, ID de usuário da Polar) **nunca** ficam no código. Elas ficam em variáveis de ambiente ou em um `.env` local.
- **Dados de saúde** baixados da API (banco de dados, CSV, JSON, cache) ficam numa pasta local que **não** é versionada.
- O `.gitignore` é criado **antes do primeiro commit** e cobre `.env`, a pasta de dados, arquivos de banco e de token.
- Um `.env.example` com os nomes das variáveis, **sem valores reais**, documenta a configuração para quem clonar o projeto.
- **Atenção ao histórico do git:** algo sensível que foi commitado uma vez continua no histórico mesmo depois de apagado. Antes de cada commit, confira o que está sendo incluído (`git status` / `git diff --staged`).
- Testes, exemplos e prints do README usam **dados fictícios**, nunca meus dados reais.
- Não enviar meus dados de saúde a serviços externos.

## Decisões em aberto

Decidiremos juntos, com explicação dos prós e contras:

- [x] Framework do dashboard: Streamlit + plotly
- [x] Como armazenar os dados localmente: SQLite
- [x] Gerenciamento de ambiente e dependências: venv + pip
- [x] Biblioteca HTTP: requests (+ python-dotenv)

## Estrutura

Dois pacotes: `polar/` (dados: API + banco, sem Streamlit) e `app/` (interface). Imports sempre absolutos a partir da raiz (`from polar import db`, `from app import ui`). Caminhos de `data/` são calculados a partir da raiz (`Path(__file__).resolve().parent.parent`).

- `polar/auth.py`: fluxo OAuth2, rodado uma vez (`python -m polar.auth`); grava `data/token.json`
- `polar/api.py`: chamadas GET à AccessLink com o token
- `polar/db.py`: schema SQLite (`data/polar.db`) e helpers de upsert
- `polar/sync.py`: busca os últimos 28 dias e grava no banco; pode rodar várias vezes (`python -m polar.sync`)
- `scripts/explore.py`: diagnóstico; imprime só a estrutura das respostas
- `tests/`: `unittest` com dados fictícios (`python -m unittest -v`); testam funções puras, sem API nem banco
- `README.md`: instalação e uso, para quem clonar o repositório
- `dashboard.py` (raiz): ponto de entrada do Streamlit; registra as páginas com `st.navigation(..., position="hidden")` (sem menu lateral), injeta o CSS global e desenha a barra do topo (voltar, status, Sincronizar)
- `app/ui.py`: **identidade visual**: cor/ícone de cada grupo (`GROUPS`), CSS global, componentes HTML (cabeçalho de página, painel, hero, faixa de estatísticas, pílula, anel, "?"). Novas páginas devem usar estes componentes.
- `app/charts.py`: leitura do banco e gráficos plotly no estilo do app (`area`, `bars`, `stacked_bars`, `daily_ticks`, `show`)
- `app/insights.py`: regras do "Insight do dia" (status do Nightly Recharge + HRV vs. média de 7 dias + nota do sono), tradução dos códigos da Polar e `stage_segments` (hipnograma → trechos); sem dependência do Streamlit, por isso testável
- `.streamlit/config.toml`: tema escuro fixo e toolbar mínima (mudanças exigem reiniciar o Streamlit)
- `app/views/`: uma página por grupo (caminhos nas chamadas `st.Page`/`st.page_link` começam com `app/views/`): `overview.py` (Resumo, com o destaque de cada grupo e links), `sleep.py`, `recovery.py`, `heart_rate.py`, `activity.py`. A pasta não se chama `pages/` para não ativar o modo antigo de multipáginas do Streamlit.

Códigos da API: hipnograma 0=acordado, 1=REM, 2=não-REM mais leve, 3=não-REM leve, 4=profundo, 5=indefinido; `nightly_recharge_status` 1–6 (muito ruim → muito bom); `ans_charge_status` 1–5 (muito abaixo → muito acima do usual).

Rodar sempre com `.\.venv\Scripts\python.exe` (o Python do sistema não está no PATH).
Dashboard: `.\.venv\Scripts\python.exe -m streamlit run dashboard.py`.

Durações do sono (`light_sleep`, `deep_sleep`, `rem_sleep`...) vêm em **segundos**.

## Registro de decisões

- **2026-10-28 · venv + pip:** padrão da linguagem; mais didático que uv.
- **2026-10-28 · Python 3.12 via winget:** instalado sem adicionar ao PATH; usamos o Python do venv.
- **2026-10-28 · Callback OAuth2 com `http.server`:** biblioteca padrão; servidor atende uma única requisição.
- **2026-10-28 · SQLite com tabelas filhas para séries:** permite consultas por horário; JSON na linha seria mais simples, mas não é consultável.
- **2026-10-28 · Upsert por data:** a API devolve janelas sobrepostas de 28 dias; re-sincronizar não duplica.
- **2026-10-28 · Horários das séries noturnas reconstruídos a partir de `sleep_start_time`:** a API manda só `HH:MM`, e a noite cruza a meia-noite.
- **2026-10-28 · Sincronizar com frequência:** sono, Nightly Recharge e FC só ficam 28 dias na API.
- **2026-10-28 · Dashboard em página única (Streamlit + plotly):** cartões com delta vs. média de 7 dias + 4 gráficos; abas ficam para depois.
- **2026-10-28 · Resumo + uma página por grupo:** o Resumo mostra só o destaque de cada grupo (nota do sono, HRV, FC média noturna, calorias), e o link "Ver detalhes" abre a página do grupo. Link (`st.page_link`), e não botão, porque é navegação.
- **2026-10-28 · Cartão inteiro clicável via CSS ("stretched link"):** o `::after` do link cobre o cartão. Depende de nomes internos do Streamlit (`st-key-*`, `stPageLink-NavLink`, `stTooltipHoverTarget`); conferir após atualizar o Streamlit.
- **2026-10-28 · Sem menu lateral:** o único acesso aos grupos são os cartões do Resumo (grade 2×2); cada página de detalhe tem um link "← Resumo" para voltar; o botão Sincronizar fica no Resumo.
- **2026-10-28 · Novo visual do Resumo (escuro, 3 colunas, Insight do dia no centro):** cartões em HTML/CSS com sparklines em SVG (sem plotly, para não conflitar com o CSS do cartão clicável).
- **2026-10-28 · Insight por regras, não por IA:** evita enviar dados de saúde para fora. Usa o status real da Polar em vez de uma "nota de prontidão" inventada.
- **2026-10-28 · Cor das pílulas pelo significado:** verde = melhor, vermelho = pior, cinza = neutro (FC noturna caindo é verde).
- **2026-10-28 · Identidade visual (`ui.py`):** uma cor por grupo em todo o app (Sono `#eda100`, Recuperação `#199e70`, FC `#e66767`, Atividade `#3987e5`); a cor segue o dado (FC é vermelha em qualquer página). Fontes Inter (texto) e Space Grotesk (títulos/números) via Google Fonts no `config.toml`. Todas as páginas seguem o esqueleto: cabeçalho → hero + evolução → tendências → painel do dia/noite.
- **2026-10-28 · Painéis por `key` de container:** o CSS estiliza containers cujo `key` começa com `panel-`, `card-`, `row-`, `hero` ou `insight`. Linhas `row-*` quebram abaixo de ~700px.
- **2026-10-28 · "?" em CSS (`ui.tip`):** mesmo estilo em todo lugar; abre no hover e no foco (toque no celular).
- **2026-10-28 · Nada de `<svg>` dentro do `st.html`:** o Streamlit sanitiza o HTML (DOMPurify, perfil só `html`) e remove SVG. Anéis são CSS puro (`conic-gradient` + `mask`, em `ui.ring`); outros desenhos vão como `<img src="data:image/svg+xml;base64,...">` (`ui.svg_image`).
- **2026-10-28 · Hipnograma em retângulos:** barras horizontais (`base` = início, comprimento em ms) numa faixa por estágio. Códigos 2 e 3 viram "Leve"; o 5 vira vão. Cores dos estágios em `ui.SLEEP_STAGES` (Profundo roxo, Leve azul, REM verde-água, Acordado laranja), as mesmas do gráfico "Sono por estágio". Roxo e azul ficam próximos para daltônicos; a posição da faixa e a legenda compensam.
- **2026-10-28 · Textos começam com maiúscula:** `ui.capitalize` é aplicado automaticamente nos valores da faixa de estatísticas, do hero e no selo. Exceção intencional: o "de 100" dos anéis, que continua o número.
- **2026-10-28 · Enquadramento:** itens de grade/flex com texto levam `min-width: 0`; valores em texto na faixa de estatísticas usam a classe `is-text` (fonte menor, quebra de linha).
- **2026-10-29 · Pacotes `polar/` + `app/`:** separa dados de interface; `dashboard.py` fica na raiz para o comando `streamlit run` não mudar. `polar_api.py` virou `polar/api.py` (sem prefixo repetido). Alternativa leve (tudo na raiz) descartada: raiz cheia e responsabilidades misturadas.
- **2026-10-29 · Testes com `unittest`:** biblioteca padrão, sem dependência nova; só funções puras e dados fictícios. `stage_segments` saiu de `views/sleep.py` para `app/insights.py`, porque importar uma página executa a página.
- **2026-10-29 · Mensagens e personagem por nível do Nightly Recharge:** `insights.LEVELS` tem título, subtítulo, conselho (baseado nas dicas do app da Polar), personagem, humor e frase para cada status 1–6; a cor de destaque continua em 3 estados (`classify`). Imagem em `app/assets/recharge/<status>.png`, exibida com `st.image` (arquivo de 2 MB; em base64 no `st.html` iria a cada recarga). Os personagens são de animes com direitos autorais: decidir antes de publicar se as imagens vão para o GitHub.
- **2026-10-29 · Setas ‹ › no Insight do dia:** botões `tertiary` (discretos) ao redor do selo da noite; deslocamento a partir da noite mais recente em `st.session_state["insight_offset"]`, alterado por `on_click`. `build_insight(..., night=)` calcula a média só com noites anteriores e troca "Esta noite" por "Na noite de dd/mm". O subtítulo do topo continua sendo o da última noite. As setas andam só pelas noites com Nightly Recharge. Os 4 cartões acompanham a noite escolhida (`card(..., until=)`): sono, HRV e FC da mesma data; atividade do **dia anterior** à noite (o dia que influenciou o sono, mesmo padrão do "último dia completo").
- **2026-10-29 · Grade do Resumo alinhada:** a partir de 641px, as colunas esticam (`align-items: stretch`, pois `vertical_alignment="top"` não estica) e o bloco de cada coluna vira grid com `grid-auto-rows: 1fr` (linhas iguais, nunca menores que o conteúdo). `flex: 1 1 0` foi descartado: com `min-height` fixa, o cartão encolhia abaixo do conteúdo e vazava. No cartão do Sono, a pílula fica embaixo do anel para a sparkline caber ao lado. Depende de `stColumn > stVerticalBlock`; conferir após atualizar o Streamlit.
- **2026-10-28 · Período compartilhado:** 7/28 dias, guardado em `st.session_state["period_days"]` e mantido entre páginas.
- **2026-10-28 · Títulos dos gráficos fora da figura:** `ui.panel_title(...)` (antes `st.subheader(help=...)`) para ter o "?" com explicação; o plotly não tem esse recurso.
- **2026-10-28 · Um eixo Y por gráfico:** HRV e FC em gráficos separados, nunca eixo duplo.
- **2026-10-28 · Cores:** slots 1–3 da paleta de referência do skill dataviz (validados para daltonismo); variam com o tema claro/escuro.
