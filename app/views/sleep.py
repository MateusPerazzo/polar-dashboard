from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import charts, ui
from app.insights import CONTINUITY_CLASS, USUAL_SCALE, stage_segments

COLOR = ui.GROUPS["sleep"]["color"]
HR_COLOR = ui.GROUPS["heart-rate"]["color"]
STAGE_ORDER = ["Profundo", "Leve", "REM", "Acordado"]  # de baixo para cima


def hypnogram_figure(segments):
    fig = go.Figure()
    for stage in STAGE_ORDER:
        part = segments[segments["stage"] == stage]
        duration = part["end"] - part["start"]
        fig.add_bar(
            y=[stage] * len(part),
            x=duration.dt.total_seconds() * 1000,  # em eixo de datas, o comprimento é em ms
            base=part["start"],
            orientation="h",
            name=stage,
            marker=dict(color=ui.SLEEP_STAGES[stage]),
            customdata=list(zip(part["start"].dt.strftime("%H:%M"),
                                part["end"].dt.strftime("%H:%M"),
                                duration.dt.total_seconds() / 60)),
            hovertemplate=stage + " · %{customdata[0]}–%{customdata[1]}"
                                  " (%{customdata[2]:.0f} min)<extra></extra>",
        )
    charts.style(fig, height=280)
    fig.update_layout(barmode="overlay", bargap=0.15, barcornerradius=2, hovermode="closest")
    fig.update_yaxes(categoryorder="array", categoryarray=STAGE_ORDER, showgrid=False)
    fig.update_xaxes(type="date", tickformat="%H:%M")
    return fig


def asleep_seconds(row):
    return (row["light_sleep"] + row["deep_sleep"] + row["rem_sleep"]
            + (row["unrecognized_sleep_stage"] or 0))


def in_bed_seconds(row):
    start = datetime.fromisoformat(row["sleep_start_time"])
    end = datetime.fromisoformat(row["sleep_end_time"])
    return (end - start).total_seconds()


sleep = charts.load("SELECT * FROM sleep ORDER BY date")

window = ui.page_header("sleep", "Análise do sono",
                        "Entenda como suas noites estão impactando sua performance.")
charts.require_data(sleep)

sleep["asleep"] = sleep.apply(asleep_seconds, axis=1)
recent = sleep.tail(window)
last = sleep.iloc[-1]
previous_avg = sleep["asleep"].iloc[-8:-1].mean()
difference = round((last["asleep"] - previous_avg) / 60)
minutes = "minuto" if abs(difference) == 1 else "minutos"
note = (f"Você dormiu {abs(difference)} {minutes} a {'mais' if difference >= 0 else 'menos'} "
        f"que a sua média das 7 noites anteriores.")

with st.container(key="row-sleep-top"):
    hero_col, chart_col = st.columns([2, 3], gap="medium")
with hero_col:
    ui.hero(
        kicker=f"Última noite · {last['date']:%d/%m}",
        title="Seu sono",
        help_text="Nota de 1 a 100 calculada pela Polar a partir da duração, da "
                  "continuidade e da parte regeneradora do sono. O selo compara a "
                  "nota com o seu padrão dos últimos 28 dias. Sono real é o tempo "
                  "entre adormecer e acordar menos o tempo que você ficou acordado "
                  "durante a noite (as interrupções). Eficiência é o sono real "
                  "dividido pelo tempo entre adormecer e acordar.",
        badge=USUAL_SCALE.get(last["sleep_charge"], ""),
        center_html=ui.ring(last["sleep_score"] / 100, COLOR,
                            f"{last['sleep_score']:.0f}", "de 100"),
        stats=[
            ("Duração (sono real)", ui.format_duration(last["asleep"])),
            ("Eficiência", f"{last['asleep'] / in_bed_seconds(last):.0%}"),
        ],
        note=note,
    )
with chart_col:
    with st.container(border=True, key="panel-sleep-score"):
        ui.panel_title(
            "Evolução da nota", f"Suas noites nos últimos {window} dias",
            "Nota do sono de cada noite. Mais importante que um dia isolado é a "
            "tendência: noites seguidas abaixo do seu normal merecem atenção.",
        )
        charts.show(charts.area(recent["date"], recent["sleep_score"], COLOR, "Nota",
                                "%{y:.0f} pontos"))

with st.container(border=True, key="panel-sleep-stages"):
    ui.panel_title(
        "Sono por estágio", "Distribuição diária de sono profundo, leve e REM",
        "Profundo: fase mais associada à recuperação física. Leve: a maior parte "
        "da noite, transição entre as fases. REM: fase dos sonhos, ligada à "
        "memória e ao aprendizado. A altura total é o tempo dormindo, sem as "
        "interrupções.",
    )
    charts.show(charts.stacked_bars(
        recent["date"],
        [
            ("Profundo", recent["deep_sleep"] / 3600, ui.SLEEP_STAGES["Profundo"]),
            ("Leve", recent["light_sleep"] / 3600, ui.SLEEP_STAGES["Leve"]),
            ("REM", recent["rem_sleep"] / 3600, ui.SLEEP_STAGES["REM"]),
        ],
        "%{y:.1f} h",
    ))

with st.container(border=True, key="panel-sleep-night"):
    title_col, picker_col = st.columns([3, 1], vertical_alignment="center")
    with title_col:
        ui.panel_title("Noite selecionada", "Detalhes do seu sono e recuperação noturna")
    with picker_col:
        day = charts.day_picker(sleep["date"], "Noite", "sleep-night")
    night = sleep[sleep["date"] == day].iloc[0]
    ui.stat_strip([
        ("bedtime", "Deitou", night["sleep_start_time"][11:16],
         "Horário em que a Polar detectou o início do sono."),
        ("wb_sunny", "Acordou", night["sleep_end_time"][11:16],
         "Horário em que a Polar detectou o fim do sono."),
        ("timer", "Sono real", ui.format_duration(night["asleep"]),
         "Tempo entre adormecer e acordar menos o tempo que você ficou acordado "
         "durante a noite (as interrupções)."),
        ("pause_circle", "Interrupções", f"{night['total_interruption_duration'] / 60:.0f} min",
         "Tempo total acordado durante a noite, somando interrupções curtas e longas."),
        ("autorenew", "Ciclos de sono", f"{night['sleep_cycles']:.0f}",
         "Quantas vezes você passou pela sequência de estágios. Cada ciclo "
         "costuma durar cerca de 90 minutos."),
        ("linear_scale", "Continuidade", CONTINUITY_CLASS.get(night["continuity_class"], "—"),
         "Avaliação da Polar de quão contínuo foi o sono, de fragmentado a muito contínuo."),
    ])

hypnogram = charts.load(
    "SELECT timestamp, stage FROM sleep_hypnogram WHERE date = ? ORDER BY timestamp",
    (day,), dates=["timestamp"],
)
sleep_hr = charts.load(
    "SELECT timestamp, heart_rate FROM sleep_heart_rate WHERE date = ? ORDER BY timestamp",
    (day,), dates=["timestamp"],
)

with st.container(key="row-sleep-night"):
    hypno_col, hr_col = st.columns(2, gap="medium")
with hypno_col:
    with st.container(border=True, key="panel-hypnogram"):
        ui.panel_title(
            "Hipnograma", "Estágios do sono ao longo da noite",
            "Cada retângulo é um trecho da noite: começa quando você entrou no "
            "estágio e termina quando mudou. É normal passar várias vezes por "
            "todos, com mais sono profundo no começo da noite e mais REM perto do "
            "amanhecer. Vãos são trechos que a Polar não conseguiu classificar "
            "(ex.: mau contato da pulseira).",
        )
        night_end = pd.Timestamp(night["sleep_end_time"]).tz_localize(None)
        charts.show(hypnogram_figure(stage_segments(hypnogram, night_end)))
with hr_col:
    with st.container(border=True, key="panel-sleep-hr"):
        average = sleep_hr["heart_rate"].mean()
        ui.panel_title(
            "FC durante o sono",
            f"Frequência cardíaca média de {average:.0f} bpm" if len(sleep_hr) else "Sem dados",
            "Costuma cair nas primeiras horas e ficar mais baixa no sono profundo. "
            "Uma FC noturna mais alta que o seu normal pode acompanhar álcool, "
            "refeição tarde, estresse, treino intenso ou início de doença.",
        )
        if len(sleep_hr):
            fig = charts.area(sleep_hr["timestamp"], sleep_hr["heart_rate"], HR_COLOR, "FC",
                              "%{y:.0f} bpm", daily=False, height=280)
            fig.update_xaxes(tickformat="%H:%M")
            charts.show(fig)
