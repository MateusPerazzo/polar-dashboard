import streamlit as st

from app import charts, ui
from app.insights import RECHARGE_STATUS, USUAL_SCALE

COLOR = ui.GROUPS["recovery"]["color"]
HR_COLOR = ui.GROUPS["heart-rate"]["color"]

recharge = charts.load("SELECT * FROM nightly_recharge ORDER BY date")

window = ui.page_header("recovery", "Nightly Recharge",
                        "Como seu corpo se recuperou do treino e do estresse durante a noite.")
charts.require_data(recharge)

recent = recharge.tail(window)
last = recharge.iloc[-1]
hrv = charts.summarize(recharge, "heart_rate_variability_avg")
status = last["nightly_recharge_status"]
if hrv["delta"] is None:
    note = "Ainda não há noites suficientes para comparar."
else:
    note = (f"Seu HRV ficou {abs(hrv['delta']):.0f} ms "
            f"{'acima' if hrv['delta'] >= 0 else 'abaixo'} da sua média das 7 noites anteriores.")

with st.container(key="row-recovery-top"):
    hero_col, chart_col = st.columns([2, 3], gap="medium")
with hero_col:
    ui.hero(
        kicker=f"Última noite · {last['date']:%d/%m}",
        title="Sua recuperação",
        help_text="O anel mostra o status do Nightly Recharge, a avaliação geral da "
                  "Polar de 1 (muito ruim) a 6 (muito boa). O selo compara o seu "
                  "sistema nervoso autônomo (ANS) com o seu padrão.",
        badge=f"ANS {USUAL_SCALE.get(last['ans_charge_status'], '—')}",
        center_html=ui.ring(status / 6, COLOR, f"{status:.0f}/6",
                            ui.capitalize(RECHARGE_STATUS.get(status, ""))),
        stats=[
            ("HRV noturno", f"{last['heart_rate_variability_avg']:.0f} ms"),
            ("ANS charge", f"{ui.format_number(last['ans_charge'], 1)}"),
        ],
        note=note,
    )
with chart_col:
    with st.container(border=True, key="panel-recovery-hrv"):
        ui.panel_title(
            "Evolução do HRV", f"Variabilidade da FC nos últimos {window} dias",
            "HRV é o quanto o intervalo entre batimentos varia. A Polar mede nas "
            "primeiras horas de sono. Em geral, mais alto que o seu normal indica "
            "corpo mais descansado. Compare com você mesmo, não com os outros.",
        )
        charts.show(charts.area(recent["date"], recent["heart_rate_variability_avg"], COLOR,
                                "HRV", "%{y:.0f} ms"))

with st.container(key="row-recovery-trends"):
    ans_col, breath_col = st.columns(2, gap="medium")
with ans_col:
    with st.container(border=True, key="panel-recovery-ans"):
        ui.panel_title(
            "ANS charge", "Sistema nervoso autônomo, de -10 a +10",
            "Pontuação da Polar que junta FC, HRV e respiração e compara com o seu "
            "padrão dos últimos dias: positivo é acima do usual, negativo abaixo.",
        )
        charts.show(charts.area(recent["date"], recent["ans_charge"], COLOR, "ANS charge",
                                "%{y:.1f}", height=260))
with breath_col:
    with st.container(border=True, key="panel-recovery-breathing"):
        ui.panel_title(
            "Respiração", "Média de respirações por minuto durante o sono",
            "Costuma ser bem estável de uma noite para outra, então mudanças "
            "grandes chamam atenção, por exemplo em resfriados ou noites de estresse.",
        )
        charts.show(charts.area(recent["date"], recent["breathing_rate_avg"], COLOR,
                                "Respiração", "%{y:.1f} resp/min", height=260))

with st.container(border=True, key="panel-recovery-night"):
    title_col, picker_col = st.columns([3, 1], vertical_alignment="center")
    with title_col:
        ui.panel_title("Noite selecionada", "Detalhes da recuperação noturna")
    with picker_col:
        day = charts.day_picker(recharge["date"], "Noite", "recovery-night")
    night = recharge[recharge["date"] == day].iloc[0]
    ui.stat_strip([
        ("battery_charging_full", "Recuperação", RECHARGE_STATUS.get(night["nightly_recharge_status"], "—"),
         "Avaliação geral da Polar: muito ruim, ruim, comprometida, OK, boa ou muito boa."),
        ("psychology", "ANS", USUAL_SCALE.get(night["ans_charge_status"], "—"),
         "Como o ANS charge da noite se compara ao seu padrão."),
        ("monitor_heart", "HRV médio", f"{night['heart_rate_variability_avg']:.0f} ms",
         "Média da variabilidade da FC nas primeiras horas de sono."),
        ("favorite", "FC média", f"{night['heart_rate_avg']:.0f} bpm",
         "Média da FC no mesmo período em que o HRV foi medido."),
        ("air", "Respiração", f"{ui.format_number(night['breathing_rate_avg'], 1)} /min",
         "Média de respirações por minuto durante o sono."),
    ])

hrv_samples = charts.load(
    "SELECT timestamp, hrv FROM recharge_hrv WHERE date = ? ORDER BY timestamp",
    (day,), dates=["timestamp"],
)
breathing_samples = charts.load(
    "SELECT timestamp, breathing_rate FROM recharge_breathing WHERE date = ? ORDER BY timestamp",
    (day,), dates=["timestamp"],
)

with st.container(key="row-recovery-night"):
    hrv_col, breath_night_col = st.columns(2, gap="medium")
with hrv_col:
    with st.container(border=True, key="panel-recovery-hrv-night"):
        ui.panel_title(
            "HRV ao longo da noite", f"Noite de {day[8:10]}/{day[5:7]}",
            "As medições que a Polar usou para calcular a média da noite. "
            "Oscilações são normais; o que importa é o nível geral comparado com "
            "outras noites.",
        )
        if len(hrv_samples):
            fig = charts.area(hrv_samples["timestamp"], hrv_samples["hrv"], COLOR, "HRV",
                              "%{y:.0f} ms", daily=False, height=260)
            fig.update_xaxes(tickformat="%H:%M")
            charts.show(fig)
with breath_night_col:
    with st.container(border=True, key="panel-recovery-breathing-night"):
        ui.panel_title(
            "Respiração ao longo da noite", f"Noite de {day[8:10]}/{day[5:7]}",
            "Respirações por minuto ao longo da noite. Picos curtos costumam "
            "coincidir com movimento ou despertares.",
        )
        if len(breathing_samples):
            fig = charts.area(breathing_samples["timestamp"], breathing_samples["breathing_rate"],
                              COLOR, "Respiração", "%{y:.1f} resp/min", daily=False, height=260)
            fig.update_xaxes(tickformat="%H:%M")
            charts.show(fig)
