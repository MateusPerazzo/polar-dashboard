from datetime import date

import streamlit as st

from app import charts, ui

COLOR = ui.GROUPS["activity"]["color"]

activity = charts.load("SELECT * FROM daily_activity ORDER BY date")

window = ui.page_header("activity", "Movimento",
                        "Quanto você se movimentou e quanta energia gastou a cada dia.")
charts.require_data(activity)

complete = activity[activity["date"] < str(date.today())]
calories = charts.summarize(complete, "calories")
last = complete.iloc[-1] if len(complete) else activity.iloc[-1]
recent = activity.tail(window)

with st.container(key="row-activity-top"):
    hero_col, chart_col = st.columns([2, 3], gap="medium")
with hero_col:
    if calories is None:
        center, note = '<div class="big-number">—</div>', "Ainda não há um dia completo."
    else:
        center = (f'<div><div class="big-number">{ui.format_number(calories["last"])}<small>kcal</small></div>'
                  f'<div style="margin-top:12px">{ui.pill(calories["delta"], " kcal", "off")}</div></div>')
        note = "A pílula compara com a média dos 7 dias anteriores."
    ui.hero(
        kicker=f"Último dia completo · {last['date']:%d/%m}",
        title="Seu gasto do dia",
        help_text="Calorias totais do último dia completo, somando metabolismo basal "
                  "e movimento. O dia de hoje fica de fora porque ainda está em andamento.",
        badge="",
        center_html=center,
        stats=[
            ("Passos", ui.format_number(last["steps"])),
            ("Tempo ativo", ui.format_duration(last["active_duration_s"])),
        ],
        note=note,
    )
with chart_col:
    with st.container(border=True, key="panel-activity-calories"):
        ui.panel_title(
            "Calorias por dia", f"Gasto de energia nos últimos {window} dias",
            "Ativas: calorias gastas em movimento e exercício. Demais: o que o corpo "
            "gasta para se manter funcionando (metabolismo basal) e o restante do "
            "dia. A altura total é o gasto total. O dia de hoje é parcial.",
        )
        charts.show(charts.stacked_bars(
            recent["date"],
            [
                ("Ativas", recent["active_calories"], COLOR),
                ("Demais", recent["calories"] - recent["active_calories"], ui.CONTEXT_GRAY),
            ],
            "%{y:.0f} kcal",
        ))

with st.container(key="row-activity-trends"):
    steps_col, active_col = st.columns(2, gap="medium")
with steps_col:
    with st.container(border=True, key="panel-activity-steps"):
        ui.panel_title("Passos", "Passos contados pelo Loop a cada dia",
                       "Contados a partir do movimento do pulso. O dia de hoje é parcial.")
        charts.show(charts.bars(recent["date"], recent["steps"], COLOR, "Passos",
                                "%{y:,.0f} passos", height=260))
with active_col:
    with st.container(border=True, key="panel-activity-active"):
        ui.panel_title("Tempo ativo", "Horas em movimento a cada dia",
                       "Tempo em que você se movimentou acima do nível que a Polar "
                       "considera atividade (por exemplo, caminhar). Ficar sentado ou "
                       "parado não conta.")
        charts.show(charts.bars(recent["date"], recent["active_duration_s"] / 3600, COLOR,
                                "Tempo ativo", "%{y:.1f} h", height=260))

with st.container(border=True, key="panel-activity-day"):
    title_col, picker_col = st.columns([3, 1], vertical_alignment="center")
    with title_col:
        ui.panel_title("Dia selecionado", "Resumo completo da atividade do dia")
    with picker_col:
        day = charts.day_picker(activity["date"], "Dia", "activity-day")
    selected = activity[activity["date"] == day].iloc[0]
    ui.stat_strip([
        ("local_fire_department", "Calorias", f"{ui.format_number(selected['calories'])} kcal",
         "Gasto total do dia, somando metabolismo basal e movimento."),
        ("bolt", "Ativas", f"{ui.format_number(selected['active_calories'])} kcal",
         "Calorias gastas em movimento e exercício."),
        ("directions_walk", "Passos", ui.format_number(selected["steps"]),
         "Passos contados pelo Loop."),
        ("straighten", "Distância", f"{ui.format_number(selected['distance_from_steps'] / 1000, 1)} km",
         "Distância estimada pela Polar a partir dos passos."),
        ("timer", "Tempo ativo", ui.format_duration(selected["active_duration_s"]),
         "Tempo em movimento acima do nível de atividade."),
        ("event_seat", "Alertas de inatividade", f"{selected['inactivity_alert_count']:.0f}",
         "Quantas vezes o Loop avisou que você estava parado havia muito tempo."),
    ])
