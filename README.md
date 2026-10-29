# Dashboard Polar Loop

Dashboard local, em Python, para visualizar os dados de um Polar Loop: sono, recuperação (Nightly Recharge / HRV), frequência cardíaca e atividade. Os dados vêm da [API Polar AccessLink v3](https://www.polar.com/accesslink-api/) e ficam guardados só no seu computador, num banco SQLite.

Feito com [Streamlit](https://streamlit.io) e [plotly](https://plotly.com/python/).

## Estrutura

```
dashboard.py      ponto de entrada do Streamlit (navegação e barra do topo)
polar/            dados: falar com a API e guardar no banco
  auth.py         autorização OAuth2 (roda uma vez)
  api.py          chamadas à AccessLink
  db.py           schema do SQLite e funções de gravação
  sync.py         baixa os últimos 28 dias e grava no banco
app/              interface
  ui.py           identidade visual: cores, CSS e componentes
  charts.py       leitura do banco e gráficos
  insights.py     regras do "Insight do dia" e tradução dos códigos da Polar
  views/          uma página por grupo (Resumo, Sono, Recuperação, FC, Atividade)
scripts/
  explore.py      diagnóstico: mostra a estrutura das respostas da API
tests/            testes automatizados (dados fictícios)
data/             banco, token e respostas brutas (não versionado)
```

## Como rodar

Requer Python 3.12. Os comandos abaixo são do PowerShell no Windows.

1. Crie o ambiente virtual e instale as dependências:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
2. Registre um cliente em [admin.polaraccesslink.com](https://admin.polaraccesslink.com) com o redirect `http://localhost:5000/callback`.
3. Copie `.env.example` para `.env` e preencha `POLAR_CLIENT_ID` e `POLAR_CLIENT_SECRET`.
4. Autorize o acesso (abre o navegador; rode uma vez):
   ```powershell
   .\.venv\Scripts\python.exe -m polar.auth
   ```
5. Baixe os dados:
   ```powershell
   .\.venv\Scripts\python.exe -m polar.sync
   ```
6. Abra o dashboard:
   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run dashboard.py
   ```

A Polar guarda sono, Nightly Recharge e FC contínua só pelos últimos 28 dias. Sincronize com frequência (botão **Sincronizar** no dashboard ou o passo 5) para não perder histórico.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

## Privacidade

- Credenciais ficam no `.env` e o token em `data/`. Nenhum dos dois é versionado (veja o `.gitignore`).
- Os dados de saúde ficam em `data/polar.db` e não saem do computador. O "Insight do dia" é gerado por regras locais, sem serviço externo.
