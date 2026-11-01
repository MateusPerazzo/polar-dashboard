import streamlit as st

from app import ui

st.set_page_config(page_title="Polar Loop", page_icon=":material/monitor_heart:", layout="wide")

pages = [
    st.Page("app/views/overview.py", title="Resumo", default=True),
    st.Page("app/views/sleep.py", title="Sono"),
    st.Page("app/views/recovery.py", title="Recuperação"),
    st.Page("app/views/heart_rate.py", title="Frequência cardíaca"),
    st.Page("app/views/activity.py", title="Atividade"),
    st.Page("app/views/settings.py", title="Configurações"),
]
current = st.navigation(pages, position="hidden")

ui.inject_global_css()

# Barra do topo das páginas de detalhe: voltar à esquerda; status e Sincronizar à direita.
# No Resumo, a barra fica no cabeçalho da própria página, ao lado da saudação (overview.py),
# para não sobrar uma linha vazia à esquerda.
if current.title != "Resumo":
    with st.container(horizontal=True, vertical_alignment="center", key="topbar"):
        st.page_link("app/views/overview.py", label="Resumo", icon=":material/arrow_back:")
        ui.top_actions()

current.run()
