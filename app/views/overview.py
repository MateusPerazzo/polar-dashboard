from datetime import date, datetime, timedelta
from html import escape

import streamlit as st

from app import charts, insights, settings, ui

DELTA_HELP = " A pílula compara com a média dos 7 registros anteriores."

CSS = """
<style>
/* Cabeçalho: a saudação ocupa o que sobra (abaixo de 300px, a coluna da direita quebra para
   baixo); a coluna da direita estica até a altura da saudação, com a barra do topo em cima e
   o período embaixo, na linha da frase. */
.st-key-overview-head { align-items: stretch !important; }
.st-key-overview-head > div:first-child { flex: 1 1 0; min-width: min(100%, 300px); }
.st-key-overview-side { justify-content: space-between; }
/* Frase do topo em 1 linha (limite de caracteres em Configurações); "…" só por proteção. */
.st-key-overview-head .page-subtitle { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.card-head { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.chip {
    width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center; flex: none;
    background: color-mix(in srgb, var(--c) 16%, transparent); color: var(--c);
}
.card-title { font-family: var(--display); font-weight: 700; font-size: 1.05rem; }
.chevron { margin-left: auto; color: var(--muted); }
.card-label { color: var(--muted); font-size: 0.85rem; margin-top: 12px; }
/* Destaque em cima (valor + pílula lado a lado) e sparkline embaixo, na largura toda. */
.card-row { display: flex; flex-direction: column; gap: 16px; margin-top: 16px; }
.card-main { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; }
.card-value { font-family: var(--display); font-size: clamp(2.2rem, 4vw, 2.75rem); font-weight: 700; line-height: 1; letter-spacing: -0.03em; }
.card-value small { font-size: 0.9rem; font-weight: 500; color: var(--muted); margin-left: 4px; letter-spacing: 0; }
.card-row .pill { margin-top: 0; }
.card-ring { display: flex; align-items: center; gap: 14px; }
.card-row .sparkline { display: block; width: 100%; height: 72px; }

/* Cartão inteiro clicável ("stretched link"): o ::after do link cobre o cartão. */
[class*="st-key-card-"] { position: relative; transition: border-color 0.15s, background 0.15s; }
[class*="st-key-card-"]:hover { border-color: var(--border-strong) !important; background: var(--surface-hover); }
[class*="st-key-card-"]:hover .chevron { color: var(--ink); }
[class*="st-key-card-"]:has(a:focus-visible) { outline: 2px solid var(--ink); outline-offset: 2px; }
[class*="st-key-card-"] div, [class*="st-key-card-"] a { position: static; }
[class*="st-key-card-"] [data-testid="stPageLink-NavLink"]::after {
    content: ""; position: absolute; inset: 0; z-index: 1;
}
/* O link fica invisível: a seta e o cartão já mostram que é clicável. */
[class*="st-key-card-"] [data-testid="stPageLink"] { height: 0; overflow: hidden; }

/* Insight do dia: a leitura dos dados vem primeiro; a imagem vem depois, grande, como
   complemento visual. Cada seção tem altura fixa (título: 1 linha; texto: 4; nome: 1; fala: 2)
   e os textos têm limite de caracteres em Configurações (insights.TEXT_LIMITS), então nenhuma
   seção muda de lugar ao trocar de noite. O corte com "…" é só proteção.
   Ritmo: 16px entre seções (o gap do Streamlit entre blocos + as margens abaixo), 8px dentro. */
.st-key-insight-head { row-gap: 8px; }
.insight-title {
    font-family: var(--display); font-size: 1.4rem; font-weight: 700; line-height: 1.25;
    height: 1.25em; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
/* line-clamp: corta na 4ª linha com "…". */
.insight-text {
    color: var(--ink-2); line-height: 1.6; height: 6.4em; margin: 8px 0 0; overflow: hidden;
    display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 4;
}
.readiness {
    display: flex; align-items: center; gap: 16px; margin: 16px 0 0;
    padding: 16px; border-radius: 16px; border: 1px solid var(--border);
}
.readiness strong { display: block; }
/* Setas do Insight: discretas, cinza, sem fundo; setas e selo com a mesma altura, centralizados. */
.st-key-insight-head > div:first-child { flex: 1 1 auto; min-width: 0; }
.st-key-insight-nav > div { display: flex; align-items: center; }
/* O .badge global tem max-width: 55% do pai; aqui o pai é estreito, então o selo fica numa linha. */
.st-key-insight-nav .badge {
    display: inline-flex; align-items: center; height: 26px; line-height: 1;
    max-width: none; white-space: nowrap;
}
.st-key-insight-prev button, .st-key-insight-next button {
    color: var(--muted); min-height: 0; height: 26px; width: 26px; padding: 0;
    display: inline-flex; align-items: center; justify-content: center; line-height: 1;
}
.st-key-insight-prev button p, .st-key-insight-next button p { display: none; }
.st-key-insight-prev button:hover, .st-key-insight-next button:hover { color: var(--ink); }
.st-key-insight-prev button:disabled, .st-key-insight-next button:disabled { opacity: 0.25; }

/* Personagem do status: depois da avaliação. */
.st-key-insight-character { gap: 8px; }
/* Moldura fixa para qualquer imagem (padrão ou recortada em Configurações): formato
   --image-ratio (3:2, de settings.IMAGE_RATIO), largura toda do cartão até 450px (= 300px de
   altura). Limitar a largura, e não a altura, mantém o recorte inteiro quando o insight ocupa
   a linha toda (telas médias). object-fit: cover corta o centro de imagens sem recorte em vez
   de deformar. O !important vence o max-width que o Streamlit põe direto na imagem. */
.st-key-insight-character img, .image-empty {
    display: block; margin: 0 auto; width: 100%; max-width: 450px !important;
    aspect-ratio: var(--image-ratio); object-fit: cover;
    border-radius: 16px; border: 1px solid var(--border);
}
/* Sem o botão de tela cheia que o Streamlit põe nas imagens. */
.st-key-insight-character [data-testid="stElementToolbar"] { display: none; }
/* Os blocos do Streamlit em volta da imagem encolhem até o tamanho dela; quando o cartão é mais
   largo que 450px (telas médias), isto a centraliza. */
.st-key-insight-character [data-testid="stFullScreenFrame"] { display: flex; justify-content: center; }
.character-name {
    font-family: var(--display); font-weight: 700; font-size: 1.15rem; line-height: 1.3; color: var(--accent);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.character-name span { font-family: inherit; font-size: 0.95rem; font-weight: 500; color: var(--muted); }
.character-quote {
    color: var(--ink); font-size: 1.05rem; font-style: italic; line-height: 1.5; height: 3em; margin: 4px 0 0;
    overflow: hidden; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2;
}
.readiness span { color: var(--muted); font-size: 0.8rem; }
/* Celular (cartões empilhados): sem alturas fixas, o texto quebra normalmente. */
@media (max-width: 640px) {
    .st-key-overview-head .page-subtitle { white-space: normal; }
    .insight-title { height: auto; white-space: normal; }
    .insight-text, .character-quote { height: auto; display: block; }
    .character-name { white-space: normal; }
}

/* Alinhamento da grade: as colunas esticam até a altura da mais alta, e dentro
   de cada coluna os cartões ficam numa grade de linhas 1fr. Uma linha 1fr nunca
   fica menor que o conteúdo e todas têm a altura da maior, então os cartões de
   cima (e os de baixo) ficam iguais e o insight termina junto com eles. */
@media (min-width: 641px) {
    .st-key-overview-grid [data-testid="stHorizontalBlock"] { align-items: stretch !important; }
    .st-key-overview-grid [data-testid="stColumn"] > [data-testid="stVerticalBlock"] {
        display: grid; grid-auto-rows: 1fr; height: 100%;
    }
    [class*="st-key-card-"] { min-height: 250px; }
    /* Quando o cartão fica mais alto que o conteúdo, a sparkline cresce e ocupa a sobra:
       bloco do HTML -> .card-row -> imagem da sparkline. */
    [class*="st-key-card-"] [data-testid="stElementContainer"]:has(.card-row) { flex: 1 1 auto; }
    [class*="st-key-card-"] [data-testid="stHtml"]:has(.card-row) {
        height: 100%; display: flex; flex-direction: column;
    }
    [class*="st-key-card-"] .card-row { flex: 1 1 auto; }
    /* Base fixa de 72px (e não height: auto, que segue a proporção do desenho e cresce com a
       largura): assim os cartões laterais não ditam a altura da grade e o Insight não fica
       com sobra no fim; a sparkline só cresce para ocupar o espaço que sobrar. */
    [class*="st-key-card-"] .card-row .sparkline { flex: 1 0 72px; height: auto; min-height: 72px; }
}
/* Telas médias: insight em cima, cartões 2 a 2. */
@media (min-width: 641px) and (max-width: 1100px) {
    .st-key-overview-grid [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    .st-key-overview-grid [data-testid="stColumn"] {
        flex: 1 1 calc(50% - 1rem) !important; min-width: calc(50% - 1rem) !important;
    }
    .st-key-overview-grid [data-testid="stColumn"]:nth-child(2) {
        order: -1; flex-basis: 100% !important; min-width: 100% !important;
    }
    /* Insight na largura toda: o texto mais longo ocupa no máximo 3 linhas. */
    .insight-text { height: 4.8em; -webkit-line-clamp: 3; }
    /* Saudação mais estreita: a frase do topo quebra linha em vez de cortar (ela muda só de um
       dia para o outro, então não empurra nada ao navegar pelas noites). */
    .st-key-overview-head .page-subtitle { white-space: normal; }
}
</style>
"""


def sparkline(values, color, uid, width=200, height=64, pad=4):
    values = list(values)
    if len(values) < 2:
        return ""
    low, high = min(values), max(values)
    span = (high - low) or 1
    step = width / (len(values) - 1)
    points = [
        (i * step, pad + (high - value) / span * (height - 2 * pad))
        for i, value in enumerate(values)
    ]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area = f"0,{height} {line} {width},{height}"
    # Degradê da cor até transparente; com quadrados sólidos, as duas paradas iguais = cor lisa.
    top, bottom = (0.14, 0.14) if settings.is_solid() else (0.35, 0)
    return ui.svg_image(f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" preserveAspectRatio="none">
  <defs>
    <linearGradient id="fill-{uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{color}" stop-opacity="{top}"/>
      <stop offset="1" stop-color="{color}" stop-opacity="{bottom}"/>
    </linearGradient>
  </defs>
  <polygon points="{area}" fill="url(#fill-{uid})"/>
  <polyline points="{line}" fill="none" stroke="{color}" stroke-width="2"
            stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/>
</svg>""", "sparkline")


def card(group, help_text, label, df, column, unit, delta_unit, direction, window,
         until=None, ring_total=None):
    """until: última data considerada (a noite escolhida no Insight); None = tudo.
    ring_total: se informado, mostra o valor num anel (valor / ring_total)."""
    info = ui.groups()[group]
    if until is not None and not df.empty:
        df = df[df["date"] <= until]
    stats = charts.summarize(df, column)
    with st.container(border=True, key=f"card-{group}"):
        # --tone: a cor do grupo, que a aparência "Branco com cores" usa para tingir o cartão.
        head = f"""
<style>.st-key-card-{group} {{ --tone: {info['color']}; }}</style>
<div class="card-head">
  <span class="chip" style="--c:{info['color']}">{ui.icon(info['icon'])}</span>
  <span class="card-title">{info['title']}</span>{ui.tip(help_text + DELTA_HELP)}
  <span class="ms chevron" aria-hidden="true">chevron_right</span>
</div>"""
        if stats is None:
            st.html(head + f'<div class="card-label">{label}</div><div class="card-value">—</div>')
        else:
            pill = ui.pill(stats["delta"], delta_unit, direction)
            if ring_total:
                ring = ui.ring(stats["last"] / ring_total, info["color"],
                               f"{stats['last']:.0f}", f"de {ring_total}", size=104, stroke=9)
                value = f'<div class="card-ring">{ring}{pill}</div>'
            else:
                value = (f'<div class="card-value">{ui.format_number(stats["last"])}'
                         f'<small>{unit}</small></div>{pill}')
            st.html(head + f"""
<div class="card-label">{label} · {stats['date']:%d/%m}</div>
<div class="card-row">
  <div class="card-main">{value}</div>
  {sparkline(stats['values'].tail(window), info['color'], group)}
</div>""")
        st.page_link(info["page"], label=f"Abrir {info['title']}")


def greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Bom dia"
    if hour < 18:
        return "Boa tarde"
    return "Boa noite"


sleep = charts.load("SELECT date, sleep_score FROM sleep ORDER BY date")
recharge = charts.load("SELECT * FROM nightly_recharge ORDER BY date")
activity = charts.load(
    "SELECT date, calories FROM daily_activity WHERE date < ? ORDER BY date",
    (str(date.today()),),
)
levels = ui.levels()
today = insights.build_insight(sleep, recharge, levels=levels)

# Noite mostrada no Insight: deslocamento a partir da mais recente (0 = última noite),
# guardado na sessão para as setas ‹ › funcionarem entre recargas.
nights = list(recharge["date"]) if not recharge.empty else []
offset = min(st.session_state.get("insight_offset", 0), max(len(nights) - 1, 0))
st.session_state["insight_offset"] = offset


def shift_night(step):
    st.session_state["insight_offset"] += step


insight = insights.build_insight(sleep, recharge, nights[-1 - offset], levels) if nights else None
# Cor do Insight pelo resultado da recuperação (baixa, normal ou boa), personalizável em Configurações.
state = insight["state"] if insight else "neutral"
accent = ui.insight_colors()[f"insight-{state}"]["color"]

st.html(CSS)
ui.set_accent(accent)

# Cabeçalho: saudação à esquerda; à direita, a barra do topo (status, engrenagem, Sincronizar)
# em cima e o período embaixo. A barra divide a linha com a saudação para não sobrar uma
# linha vazia no topo; nas outras páginas, o dashboard.py a desenha com o link de voltar.
with st.container(horizontal=True, key="overview-head"):
    st.html(f"""
<div class="eyebrow" style="color:var(--muted)">{ui.long_date(date.today())}</div>
<div class="page-title">{greeting()}</div>
<div class="page-subtitle">{escape(today['summary']) if today else 'Sincronize para ver seus dados.'}</div>""")
    with st.container(width="content", key="overview-side"):
        ui.top_actions(gear=True)
        window = ui.period_control("overview")

if sleep.empty and recharge.empty and activity.empty:
    charts.require_data(sleep)

# Os cartões acompanham a noite escolhida no Insight. A atividade é a do dia anterior
# à noite (o dia que influenciou o sono), o mesmo padrão do "último dia completo".
night = insight["date"] if insight else None
activity_day = night - timedelta(days=1) if night is not None else None

with st.container(key="overview-grid"):
    # Coluna do centro mais larga: a imagem do Insight é 16:9, então só cresce se o cartão alargar.
    left, center, right = st.columns([1, 1.4, 1], gap="medium")

with left:
    card("sleep",
         "Nota de 1 a 100 da noite, calculada pela Polar a partir da "
         "duração, da continuidade e da parte regeneradora do sono.",
         "Nota do sono", sleep, "sleep_score", "/100", (" ponto", " pontos"), "up", window,
         until=night, ring_total=100)
    card("heart-rate",
         "FC média nas primeiras horas de sono, uma boa aproximação da sua FC de "
         "repouso. Mais baixa que o seu normal costuma indicar boa recuperação.",
         "FC média noturna", recharge, "heart_rate_avg", " bpm", " bpm", "down", window,
         until=night)

with center:
    with st.container(border=True, key="insight"):
        with st.container(horizontal=True, vertical_alignment="center", key="insight-head"):
            st.html(f"""
<div class="card-head">
  <span class="chip" style="--c:var(--accent)">{ui.icon('auto_awesome')}</span>
  <span class="card-title">Insight do dia</span>
  {ui.tip("Gerado por regras simples a partir do status do Nightly Recharge da Polar, "
          "do seu HRV comparado com a média dos últimos 7 dias e da nota do sono. "
          "Use as setas para ver as noites anteriores. "
          "Nada é enviado para fora do seu computador. Não é orientação médica.")}
</div>""")
            if insight:
                with st.container(horizontal=True, vertical_alignment="center", gap=None,
                                  width="content", key="insight-nav"):
                    st.button("", icon=":material/chevron_left:", type="tertiary",
                              key="insight-prev", disabled=offset >= len(nights) - 1,
                              on_click=shift_night, args=(1,))
                    st.html(f'<span class="badge">Noite de {insight["date"]:%d/%m}</span>',
                            width="content")
                    st.button("", icon=":material/chevron_right:", type="tertiary",
                              key="insight-next", disabled=offset == 0,
                              on_click=shift_night, args=(-1,))
        if insight is None:
            st.html('<p class="insight-text">Sincronize para ver o insight do dia.</p>')
        else:
            readiness = ""
            if insight["status"] is not None:
                readiness = f"""
<div class="readiness">
  {ui.ring(insight['status'] / 6, accent, f"{insight['status']}/6", size=64, stroke=6)}
  <div><strong>Recuperação {insight['status_label']}</strong>
  <span>Status do Nightly Recharge da Polar</span></div>
</div>"""
            # Os textos podem ter sido editados em Configurações: escape evita que "<" ou "&" quebrem o HTML.
            st.html(f"""
<div class="insight-title">{escape(insight['headline'])}</div>
<p class="insight-text">{escape(insight['text'])}</p>
{readiness}""")
            if insight["character"]:
                image = ui.level_image(insight["status"])
                with st.container(key="insight-character"):
                    if image is not None:
                        st.image(image, width="stretch")
                    else:  # mesmo espaço da imagem, para as seções abaixo não subirem
                        st.html('<div class="image-empty"></div>')
                    st.html(f"""
<div class="character">
  <div class="character-name">{escape(insight['character'])}
    <span>· {escape(insight['mood'])}</span></div>
  <p class="character-quote">“{escape(insight['quote'].strip().strip('"“”'))}”</p>
</div>""")

with right:
    card("recovery",
         "HRV noturno: o quanto o intervalo entre batimentos varia nas primeiras "
         "horas de sono. Mais alto que o seu normal costuma indicar corpo mais "
         "descansado. Compare com você mesmo, não com os outros.",
         "HRV noturno", recharge, "heart_rate_variability_avg", " ms", " ms", "up", window,
         until=night)
    card("activity",
         "Calorias totais gastas no dia anterior à noite mostrada (por padrão, o último "
         "dia completo, já que hoje ainda está em andamento), somando metabolismo basal "
         "e movimento.",
         "Calorias · dia anterior", activity, "calories", " kcal", " kcal", "off",
         window, until=activity_day)
