from datetime import date

import plotly.graph_objects as go
import streamlit as st

from app import charts, ui

COLOR = ui.GROUPS["heart-rate"]["color"]

recharge = charts.load("SELECT date, heart_rate_avg FROM nightly_recharge ORDER BY date")
daily = charts.load(
    "SELECT date, MIN(heart_rate) AS min_hr, AVG(heart_rate) AS avg_hr, "
    "MAX(heart_rate) AS max_hr FROM heart_rate GROUP BY date ORDER BY date"
)

window = ui.page_header("heart-rate", "Coração",
                        "Sua frequência cardíaca em repouso e ao longo do dia.")
charts.require_data(daily)

nightly = charts.summarize(recharge, "heart_rate_avg")
complete = daily[daily["date"] < str(date.today())]
last_day = complete.iloc[-1] if len(complete) else daily.iloc[-1]
recent_nights = recharge.tail(window)
recent_days = daily.tail(window)

with st.container(key="row-hr-top"):
    hero_col, chart_col = st.columns([2, 3], gap="medium")
with hero_col:
    if nightly is None:
        center, note = '<div class="big-number">—</div>', "Sem dados do Nightly Recharge."
    else:
        center = (f'<div><div class="big-number">{nightly["last"]:.0f}<small>bpm</small></div>'
                  f'<div style="margin-top:12px">{ui.pill(nightly["delta"], " bpm", "down")}</div></div>')
        note = ("A pílula compara com a média das 7 noites anteriores. "
                "Mais baixa costuma indicar boa recuperação.")
    ui.hero(
        kicker=f"Última noite · {nightly['date']:%d/%m}" if nightly else "Última noite",
        title="Sua FC de repouso",
        help_text="FC média nas primeiras horas de sono, medida pelo Nightly Recharge. "
                  "É uma boa aproximação da sua FC de repouso. Mínima e máxima são do "
                  "último dia completo.",
        badge="",
        center_html=center,
        stats=[
            (f"Mínima · {last_day['date']:%d/%m}", f"{last_day['min_hr']:.0f} bpm"),
            (f"Máxima · {last_day['date']:%d/%m}", f"{last_day['max_hr']:.0f} bpm"),
        ],
        note=note,
    )
with chart_col:
    with st.container(border=True, key="panel-hr-nightly"):
        ui.panel_title(
            "FC média noturna", f"Suas noites nos últimos {window} dias",
            "Em geral, mais baixa que o seu normal indica boa recuperação; mais alta "
            "pode acompanhar cansaço, álcool, estresse ou início de doença.",
        )
        charts.show(charts.area(recent_nights["date"], recent_nights["heart_rate_avg"], COLOR,
                                "FC média", "%{y:.0f} bpm"))

with st.container(border=True, key="panel-hr-range"):
    ui.panel_title(
        "Mínima e máxima por dia", f"Faixa da sua FC nos últimos {window} dias",
        "A mínima costuma acontecer durante o sono; a máxima, em exercício ou "
        "esforço. O dia de hoje ainda está em andamento.",
    )
    fig = go.Figure()
    fig.add_scatter(x=recent_days["date"], y=recent_days["max_hr"], name="Máxima",
                    mode="lines", line=dict(color=ui.CONTEXT_GRAY, width=2),
                    hovertemplate="%{y:.0f} bpm")
    fig.add_scatter(x=recent_days["date"], y=recent_days["min_hr"], name="Mínima",
                    mode="lines", line=dict(color=COLOR, width=2),
                    hovertemplate="%{y:.0f} bpm")
    charts.show(charts.daily_ticks(charts.style(fig, height=280), recent_days["date"]))

with st.container(border=True, key="panel-hr-day"):
    title_col, picker_col = st.columns([3, 1], vertical_alignment="center")
    with title_col:
        ui.panel_title("Dia selecionado", "Todas as medições de FC do dia")
    with picker_col:
        day = charts.day_picker(daily["date"], "Dia", "hr-day")
    samples = charts.load(
        "SELECT timestamp, heart_rate FROM heart_rate WHERE date = ? ORDER BY timestamp",
        (day,), dates=["timestamp"],
    )
    ui.stat_strip([
        ("arrow_downward", "Mínima", f"{samples['heart_rate'].min():.0f} bpm",
         "Menor FC registrada no dia, normalmente durante o sono."),
        ("show_chart", "Média", f"{samples['heart_rate'].mean():.0f} bpm",
         "Média de todas as medições do dia, incluindo sono e atividade."),
        ("arrow_upward", "Máxima", f"{samples['heart_rate'].max():.0f} bpm",
         "Maior FC registrada no dia, normalmente em exercício ou esforço."),
    ])
    fig = charts.area(samples["timestamp"], samples["heart_rate"], COLOR, "FC",
                      "%{y:.0f} bpm", daily=False, height=320)
    fig.update_xaxes(tickformat="%H:%M")
    charts.show(fig)
