"""Análises: os resultados do estudo em SQL (pasta analysis/), em 4 gráficos.

Cada gráfico lê uma view do banco; as consultas ficam nos arquivos .sql, e esta página só
desenha. As views são criadas rodando analysis/09_views_dashboard.sql (e o 06, para a do dia
da semana) no DB Browser.
"""

import plotly.graph_objects as go
import streamlit as st

from app import charts, settings, ui

GROUPS = ui.groups()
SLEEP = GROUPS["sleep"]["color"]
# Vermelho de "pior" (o mesmo --bad das pílulas), ajustado ao fundo; o plotly não lê variáveis CSS.
WORST = "#b52828" if settings.is_light() else ui.TONES["bad"]
RECOVERY = GROUPS["recovery"]["color"]
ACTIVITY = GROUPS["activity"]["color"]
STUDY = "Estudo de 01/10 a 10/11/2026"
# Altura dos 4 gráficos: calculada para a página inteira caber numa tela de 1920×950 (um print).
CHART_HEIGHT = 184

# Só nesta página: conteúdo mais largo (as notas e o subtítulo ocupam menos linhas e sobra altura
# para os gráficos) e painéis com menos respiro, para a página caber numa tela sem rolagem.
CSS = """
<style>
.block-container { max-width: 1640px; }
[class*="st-key-panel-analyses-"] { padding: 16px 20px; gap: 8px; }
/* Painéis da mesma linha com a mesma altura (a do mais alto), como a grade do Resumo: as colunas
   esticam e o bloco de cada coluna vira grid de uma linha 1fr, que o painel preenche. */
[class*="st-key-row-analyses-"] [data-testid="stHorizontalBlock"] { align-items: stretch !important; }
[class*="st-key-row-analyses-"] [data-testid="stColumn"] > [data-testid="stVerticalBlock"] {
    display: grid; grid-auto-rows: 1fr; height: 100%;
}
/* Título do painel e seletor Passos / Tempo ativo na mesma linha (sem quebrar; o !important
   vence o flex-wrap que o Streamlit põe no container horizontal). */
.st-key-analyses-activity-head { flex-wrap: nowrap !important; }
.st-key-analyses-activity-head > div:first-child { flex: 1 1 auto; min-width: 0; }
</style>
"""


def read_view(query, dates=()):
    """Lê uma view; devolve None (e avisa) se ela ainda não foi criada no banco."""
    try:
        return charts.load(query, dates=dates)
    except Exception:
        st.info("Os dados deste gráfico vêm de uma view que ainda não existe no seu banco. "
                "Rode o `analysis/09_views_dashboard.sql` no DB Browser para criá-la.")
        return None


def signed(value):
    """+7,8 / -0,4 / 0,0: o sinal ajuda a ler acima ou abaixo do normal."""
    text = ui.format_number(abs(value), 1)
    return f"+{text}" if value > 0 else f"-{text}" if value < 0 else text


def band_label(label):
    """'tarde(01h25 ou mais)' -> 'Tarde<br>01h25 ou mais' (nome em cima, horário embaixo)."""
    name, _, hours = label.partition("(")
    return f"<b>{ui.capitalize(name.strip())}</b><br>{hours.rstrip(')')}"


def weekday_chart(df):
    """Barras por noite da semana, com a quinta (a pior) em vermelho."""
    df = df.sort_values("numero_dia")
    worst = df["numero_dia"] == 4
    fig = go.Figure(go.Bar(
        x=df["dia_semana"], y=df["nota_media"],
        marker=dict(color=[WORST if w else charts.rgba(SLEEP, 0.35) for w in worst]),
        text=[ui.format_number(v, 1) for v in df["nota_media"]], textposition="outside",
        customdata=df[["noites_registradas", "media_horas_na_cama"]],
        hovertemplate="Noite de %{x}: nota %{y:.1f}<br>%{customdata[0]} noites, "
                      "%{customdata[1]:.1f} h na cama<extra></extra>",
        showlegend=False,
    ))
    charts.style(fig, height=CHART_HEIGHT)
    fig.update_layout(hovermode="closest")
    fig.update_yaxes(range=[0, df["nota_media"].max() * 1.18])
    return fig


def bedtime_chart(df):
    """Barras agrupadas por faixa de horário: todas as noites x sem sexta e sábado."""
    df = df.sort_values("minutos_inicio")
    x = [band_label(label) for label in df["zona_dormiu"]]
    fig = go.Figure()
    for name, column, count, color in [
        ("Todas as noites", "media_todas", "noites_todas", charts.rgba(RECOVERY, 0.35)),
        ("Sem sexta e sábado", "media_sem_sex_sab", "noites_sem_sex_sab", RECOVERY),
    ]:
        fig.add_bar(
            x=x, y=df[column], name=name, marker=dict(color=color),
            # Numa linha só: com o gráfico baixo, duas linhas passavam do topo e das faixas.
            text=[f"{signed(v)} · {n} noites" for v, n in zip(df[column], df[count])],
            textposition="outside",
            hovertemplate=f"{name}: %{{y:+.1f}}<extra></extra>",
        )
    charts.style(fig, height=CHART_HEIGHT)
    low = min(df["media_todas"].min(), df["media_sem_sex_sab"].min(), 0)
    high = max(df["media_todas"].max(), df["media_sem_sex_sab"].max(), 0)
    pad = max(high - low, 1) * 0.35
    fig.update_layout(barmode="group", hovermode="x unified")
    fig.update_yaxes(range=[low - (pad if low < 0 else 0), high + pad],
                     zeroline=True, zerolinecolor=charts.chart_colors()["text"], zerolinewidth=1)
    return fig


def activity_chart(df, column, unit):
    """Dispersão: um ponto por dia, sem linha de tendência (a análise não achou relação)."""
    fig = go.Figure(go.Scatter(
        x=df[column], y=df["nota_sono"], mode="markers",
        marker=dict(color=charts.rgba(ACTIVITY, 0.75), size=10,
                    line=dict(color=charts.chart_colors()["surface"], width=1)),
        customdata=df["dia"].dt.strftime("%d/%m"),
        hovertemplate=f"%{{customdata}}: %{{x}} {unit}<br>Nota da noite seguinte: %{{y}}<extra></extra>",
        showlegend=False,
    ))
    charts.style(fig, height=CHART_HEIGHT)
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(showgrid=True, gridcolor=charts.chart_colors()["grid"], griddash="dot")
    return fig


def hrv_chart(df):
    """Pontos de cada noite + a linha da média de 7 noites (só com a janela completa)."""
    fig = go.Figure()
    fig.add_scatter(x=df["dia"], y=df["hrv_medio"], mode="markers", name="HRV da noite",
                    marker=dict(color=charts.rgba(RECOVERY, 0.4), size=7),
                    hovertemplate="Noite: %{y:.0f} ms<extra></extra>")
    fig.add_scatter(x=df["dia"], y=df["media_movel"], mode="lines", name="Média de 7 noites",
                    line=dict(color=RECOVERY, width=3),
                    hovertemplate="Média de 7 noites: %{y:.1f} ms<extra></extra>")
    charts.style(fig, height=CHART_HEIGHT)
    return charts.daily_ticks(fig, df["dia"])


def conclusion_note(text):
    st.html(f'<p class="analysis-note">{text}</p>')


ui.set_accent(SLEEP)
st.html(CSS)
st.html(f"""
<div class="eyebrow">{ui.icon('insights')} Estudo em SQL</div>
<div class="page-title">Análises</div>
<div class="page-subtitle">4 perguntas sobre o meu sono, respondidas com SQL sobre um modelo
estrela. O que se repete nas respostas: a regularidade da rotina parece pesar mais do que
qualquer fator isolado. São 39 noites de uma pessoa só, então as conclusões são hipóteses,
não certezas. {STUDY}.</div>""")

with st.container(key="row-analyses-top"):
    week_col, bed_col = st.columns(2, gap="medium")

with week_col:
    with st.container(border=True, key="panel-analyses-week"):
        ui.panel_title(
            "O dia da semana muda o meu sono?", "Nota média do sono por noite da semana",
            "Cada barra é a média das noites que começaram naquele dia: a noite de quinta é a "
            "de quinta para sexta. São só 5 ou 6 noites por dia. "
            "View resumo_dia_semana, da análise 2.",
        )
        week = read_view("SELECT * FROM resumo_dia_semana")
        if week is not None:
            charts.show(weekday_chart(week))
            conclusion_note("A noite de quinta é a pior (60,2, contra 72,4 da terça). Não é só "
                            "acordar às 6h: a noite de domingo também termina às 6h, é ainda mais "
                            "curta nas semanas sem feriado e tem nota melhor. A causa segue em "
                            "aberto: a mudança de horário ao longo da semana ou o cansaço "
                            "acumulado.")

with bed_col:
    with st.container(border=True, key="panel-analyses-bedtime"):
        ui.panel_title(
            "Dormir mais tarde piora a recuperação?",
            "Recuperação média por horário de dormir, com e sem sexta e sábado",
            "Recuperação do sistema nervoso (ANS charge) da Polar, de -10 a +10: 0 é o meu "
            "normal, positivo é melhor e negativo é pior. As três faixas têm quantidades "
            "parecidas de noites. View hora_dormir_recuperacao, da análise 3.",
        )
        bedtime = read_view("SELECT * FROM hora_dormir_recuperacao")
        if bedtime is not None:
            charts.show(bedtime_chart(bedtime))
            conclusion_note("Sozinho, o horário não decide. As noites de sexta e sábado, sem "
                            "rotina, foram ruins em qualquer horário. Sem elas, dormir tarde teve "
                            "a melhor recuperação, mas eram na maioria terças e quartas, antes de "
                            "manhãs em que eu podia acordar mais tarde.")

with st.container(key="row-analyses-bottom"):
    activity_col, hrv_col = st.columns(2, gap="medium")

with activity_col:
    with st.container(border=True, key="panel-analyses-activity"):
        # Cabeçalho em linha: título à esquerda e, se houver dados, o seletor à direita.
        # O container é criado antes e recebe o seletor depois de ler a view.
        head = st.container(horizontal=True, vertical_alignment="top", key="analyses-activity-head")
        with head:
            ui.panel_title(
                "Se mover mais melhora o sono?", "Cada ponto é um dia e a nota da noite seguinte",
                "A atividade de cada dia e a nota do sono da noite seguinte. Se houvesse relação, "
                "os pontos formariam uma diagonal. O 11/10 (boa parte do dia sem a pulseira) fica "
                "de fora. View atividade_sono_dia, da análise 1.",
            )
        activity = read_view("SELECT * FROM atividade_sono_dia", dates=["dia"])
        if activity is not None:
            with head:
                measure = st.segmented_control(
                    "Medida", ["Passos", "Tempo ativo"], default="Passos",
                    key="analyses-activity-measure", label_visibility="collapsed",
                    width="content",
                )
            if measure == "Tempo ativo":
                charts.show(activity_chart(activity, "tempo_ativo_h", "h ativas"))
            else:
                charts.show(activity_chart(activity, "passos", "passos"))
            conclusion_note("Os pontos ficam espalhados pelas duas medidas. Separando os dias em "
                            "três faixas de atividade, a nota mudou no máximo 3,4 pontos, numa "
                            "nota que vai de 52 a 80: nos meus dados, não há relação clara "
                            "entre atividade e sono.")

with hrv_col:
    with st.container(border=True, key="panel-analyses-hrv"):
        ui.panel_title(
            "Como o meu HRV evoluiu?", "HRV de cada noite e a média das últimas 7",
            "HRV é o quanto o intervalo entre batimentos varia durante o sono. Só faz sentido "
            "comparar com o meu próprio normal: mais alto indica recuperação melhor. A média usa "
            "as 7 últimas noites registradas, por isso a linha começa na 7ª. As noites de 27/10 "
            "e 31/10, dentro da queda, não foram registradas. View hrv_media_movel, da análise 4.",
        )
        hrv = read_view("SELECT * FROM hrv_media_movel ORDER BY dia", dates=["dia"])
        if hrv is not None:
            charts.show(hrv_chart(hrv))
            conclusion_note("A média ficou em ~95 ms, chegou a ~110 e caiu para 86 na virada "
                            "para novembro, numa semana fora da rotina. Depois subiu até 113, a "
                            "maior média do período. Os dados mostram quando o HRV caiu, não "
                            "por quê.")
