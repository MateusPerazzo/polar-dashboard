import streamlit as st

from app import ui
from polar import sync

st.set_page_config(page_title="Polar Loop", page_icon=":material/monitor_heart:", layout="wide")

pages = [
    st.Page("app/views/overview.py", title="Resumo", default=True),
    st.Page("app/views/sleep.py", title="Sono"),
    st.Page("app/views/recovery.py", title="Recuperação"),
    st.Page("app/views/heart_rate.py", title="Frequência cardíaca"),
    st.Page("app/views/activity.py", title="Atividade"),
]
current = st.navigation(pages, position="hidden")

ui.inject_global_css()

# Barra do topo, igual em todas as páginas.
back, status, action = st.columns([2, 3, 1.3], vertical_alignment="center")
if current.title != "Resumo":
    back.page_link("app/views/overview.py", label="Resumo", icon=":material/arrow_back:")
status.html(
    f'<div class="topbar" style="justify-content:flex-end">'
    f'<span class="dot"></span>{ui.synced_at()}</div>'
)
if action.button("Sincronizar", icon=":material/sync:", width="stretch", key="sync"):
    with st.spinner("Buscando dados..."):
        sync.main()
    st.rerun()

current.run()
