"""Identidade visual do app: cores, CSS global e componentes em HTML."""

import base64
from datetime import date, datetime
from html import escape

import pandas as pd
import streamlit as st

from polar import db

# Uma cor por grupo, usada em todo o app (cartões, páginas e gráficos).
GROUPS = {
    "sleep": {"title": "Sono", "color": "#eda100", "icon": "bedtime", "page": "app/views/sleep.py"},
    "recovery": {"title": "Recuperação", "color": "#199e70", "icon": "monitor_heart", "page": "app/views/recovery.py"},
    "heart-rate": {"title": "Frequência cardíaca", "color": "#e66767", "icon": "favorite", "page": "app/views/heart_rate.py"},
    "activity": {"title": "Atividade", "color": "#3987e5", "icon": "local_fire_department", "page": "app/views/activity.py"},
}
# Séries categóricas (slots 1-3 da paleta de referência, validados para daltonismo).
SERIES = ["#3987e5", "#d95926", "#199e70"]
CONTEXT_GRAY = "#4a4a46"
# Estágios do sono, iguais no hipnograma e no gráfico de estágios.
SLEEP_STAGES = {
    "Profundo": "#9085e9",
    "Leve": "#3987e5",
    "REM": "#199e70",
    "Acordado": "#d95926",
}
TONES = {"good": "#0ca30c", "bad": "#ec835a", "neutral": "#898781"}

WEEKDAYS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
            "sexta-feira", "sábado", "domingo"]
MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
          "agosto", "setembro", "outubro", "novembro", "dezembro"]
PERIODS = {"7 dias": 7, "28 dias": 28}

GLOBAL_CSS = """
<style>
:root {
    --surface: #121418;
    --surface-hover: #15181d;
    --border: rgba(255, 255, 255, 0.08);
    --border-strong: rgba(255, 255, 255, 0.22);
    --ink: #f0efec;
    --ink-2: #c3c2b7;
    --muted: #898781;
    --good: #0ca30c;
    --bad: #ec835a;
    --accent: #3987e5;
    --display: "Space Grotesk", "Inter", system-ui, sans-serif;
}

.block-container { max-width: 1320px; padding: 1rem clamp(1rem, 4vw, 3rem) 3rem; }
header[data-testid="stHeader"] { background: transparent; }

/* Ícones do Material Symbols, a mesma fonte que o Streamlit já carrega. */
.ms {
    font-family: "Material Symbols Rounded";
    font-weight: normal; font-style: normal; font-size: 1.15em; line-height: 1;
    display: inline-block; vertical-align: -0.2em; letter-spacing: normal;
    text-transform: none; white-space: nowrap; font-feature-settings: "liga";
}

/* "?" com explicação: abre no hover e no foco (toque no celular). */
.tip {
    position: relative; z-index: 2; cursor: help; color: var(--muted);
    font-size: 1.05rem; outline: none;
}
.tip:hover, .tip:focus { color: var(--ink); }
.tip::after {
    content: attr(data-tip);
    position: absolute; left: 50%; bottom: calc(100% + 8px); transform: translateX(-50%);
    width: max-content; max-width: min(260px, 70vw);
    padding: 8px 12px; border-radius: 10px;
    background: #23262b; color: var(--ink); border: 1px solid var(--border);
    font: 400 0.8rem/1.45 "Inter", sans-serif; letter-spacing: normal;
    text-transform: none; white-space: normal; text-align: left;
    opacity: 0; pointer-events: none; transition: opacity 0.15s; z-index: 10;
}
.tip:hover::after, .tip:focus::after { opacity: 1; }

/* Painéis: todo container com key começando por panel-, card-, hero ou insight. */
[class*="st-key-panel-"], [class*="st-key-card-"], .st-key-hero, .st-key-insight {
    background: var(--surface);
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
    padding: clamp(16px, 2vw, 24px);
}
.st-key-hero, .st-key-insight {
    background: linear-gradient(160deg, color-mix(in srgb, var(--accent) 16%, transparent), var(--surface) 55%);
    border-color: color-mix(in srgb, var(--accent) 40%, transparent) !important;
}

/* Linhas de painéis quebram quando a coluna ficaria estreita demais. */
[class*="st-key-row-"] [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
[class*="st-key-row-"] [data-testid="stColumn"] { min-width: min(100%, 340px); }

/* Cabeçalhos */
.topbar { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 0.85rem; }
.topbar .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--good); }
.eyebrow {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.75rem; font-weight: 600; letter-spacing: 0.18em; text-transform: uppercase;
    color: var(--accent);
}
.page-title {
    font-family: var(--display); font-size: clamp(2rem, 5vw, 2.8rem); font-weight: 700;
    letter-spacing: -0.03em; line-height: 1.1; margin: 8px 0 6px;
}
.page-subtitle { color: var(--muted); }
.panel-head { display: flex; align-items: center; gap: 8px; }
.panel-title { font-family: var(--display); font-size: 1.15rem; font-weight: 700; }
.panel-subtitle { color: var(--muted); font-size: 0.85rem; margin-top: 2px; }

/* Destaque (hero) */
.hero-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.hero-top > div { min-width: 0; }
.hero-kicker { color: var(--muted); font-size: 0.85rem; }
.hero-title { font-family: var(--display); font-size: 1.3rem; font-weight: 700; display: flex; gap: 8px; align-items: center; }
.hero-body {
    display: flex; flex-wrap: wrap; align-items: center; justify-content: center;
    gap: 24px 40px; margin: 28px 0;
}
.hero-stats { display: grid; gap: 18px; }
.hero-note { color: var(--ink-2); font-size: 0.9rem; margin: 0; }
.big-number { font-family: var(--display); font-size: clamp(3rem, 6vw, 4rem); font-weight: 700; letter-spacing: -0.03em; line-height: 1; }
.big-number small { font-size: 1rem; font-weight: 500; color: var(--muted); margin-left: 6px; letter-spacing: 0; }
.badge {
    padding: 4px 12px; border-radius: 999px; max-width: 55%; text-align: center; line-height: 1.4;
    background: color-mix(in srgb, var(--accent) 18%, transparent); color: var(--accent);
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
}

/* Faixa de estatísticas: quebra sozinha conforme a largura. */
.stat-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }
/* min-width: 0 deixa o quadrado encolher; sem isso o conteúdo largo o estoura. */
.stat { min-width: 0; padding: 16px 18px; border: 1px solid var(--border); border-radius: 16px; }
.stat-label {
    display: flex; align-items: center; gap: 6px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted);
}
.stat-value {
    font-family: var(--display); font-size: clamp(1.3rem, 2.2vw, 1.7rem); font-weight: 700;
    line-height: 1.15; margin-top: 8px; overflow-wrap: anywhere;
}
/* Valores em texto ("Fragmentado", "Muito acima do usual") usam fonte menor. */
.stat-value.is-text { font-size: clamp(1.05rem, 1.6vw, 1.25rem); line-height: 1.3; overflow-wrap: break-word; }

/* Anel: conic-gradient pinta a fração; a máscara radial esvazia o centro. */
.ring, [class*="st-key-card-"] div.ring {
    position: relative; flex: none; width: var(--size); height: var(--size);
    display: grid; place-content: center; justify-items: center; text-align: center;
}
.ring::before {
    content: ""; position: absolute; inset: 0; border-radius: 50%;
    background: conic-gradient(var(--color) var(--p), color-mix(in srgb, var(--color) 18%, transparent) 0);
    -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - var(--stroke)), #000 calc(100% - var(--stroke) + 1px));
    mask: radial-gradient(farthest-side, transparent calc(100% - var(--stroke)), #000 calc(100% - var(--stroke) + 1px));
}
.ring-value { font-family: var(--display); font-weight: 700; line-height: 1; letter-spacing: -0.03em; }
.ring-caption { color: var(--muted); font-size: max(10px, calc(var(--size) * 0.08)); margin-top: 4px; }

.pill { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.8rem; font-weight: 600; }
.pill-good { color: var(--good); background: color-mix(in srgb, var(--good) 15%, transparent); }
.pill-bad { color: var(--bad); background: color-mix(in srgb, var(--bad) 15%, transparent); }
.pill-neutral { color: var(--ink-2); background: rgba(255, 255, 255, 0.08); }
</style>
"""


def inject_global_css():
    st.html(GLOBAL_CSS)


def set_accent(color):
    st.html(f"<style>:root {{ --accent: {color}; }}</style>")


def icon(name, color=None):
    style = f' style="color:{color}"' if color else ""
    return f'<span class="ms" aria-hidden="true"{style}>{name}</span>'


def tip(text):
    return f'<span class="tip ms" tabindex="0" role="img" aria-label="{escape(text)}" data-tip="{escape(text)}">help</span>'


def capitalize(text):
    """Primeira letra maiúscula sem mexer no resto ("OK" continua "OK")."""
    text = str(text)
    return text[:1].upper() + text[1:]


def format_number(value, decimals=0):
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def format_duration(seconds):
    minutes = round(seconds / 60)
    return f"{minutes // 60}h {minutes % 60:02d}min"


def pill(delta, unit, direction):
    """direction: "up" (subir é bom), "down" (descer é bom) ou "off" (neutro)."""
    if delta is None or pd.isna(delta):
        return ""
    arrow = "↑" if delta >= 0 else "↓"
    if direction == "off" or round(delta) == 0:
        tone = "neutral"
    elif (delta > 0) == (direction == "up"):
        tone = "good"
    else:
        tone = "bad"
    return f'<span class="pill pill-{tone}">{arrow} {format_number(abs(delta))}{unit}</span>'


def ring(fraction, color, center, caption="", size=150, stroke=12):
    """Anel de progresso em CSS puro (o st.html remove <svg>)."""
    percent = max(0.0, min(1.0, fraction)) * 100
    caption_html = f'<span class="ring-caption">{caption}</span>' if caption else ""
    return (
        f'<div class="ring" style="--size:{size}px; --stroke:{stroke}px; '
        f'--color:{color}; --p:{percent:.1f}%">'
        f'<span class="ring-value" style="font-size:{size * 0.28:.0f}px">{center}</span>'
        f'{caption_html}</div>'
    )


def svg_image(svg, css_class):
    """Embute um SVG como <img>, que o sanitizador do st.html permite."""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<img class="{css_class}" src="data:image/svg+xml;base64,{encoded}" alt="">'


def stat_strip(items):
    """items: lista de (ícone, rótulo, valor, explicação)."""
    cells = "".join(
        f'<div class="stat"><div class="stat-label">{icon(symbol)} {label} {tip(help_text)}</div>'
        f'<div class="stat-value{"" if any(c.isdigit() for c in str(value)) else " is-text"}">'
        f'{capitalize(value)}</div></div>'
        for symbol, label, value, help_text in items
    )
    st.html(f'<div class="stat-strip">{cells}</div>')


def panel_title(title, subtitle="", help_text=""):
    st.html(
        f'<div class="panel-head"><span class="panel-title">{title}</span>'
        f'{tip(help_text) if help_text else ""}</div>'
        f'<div class="panel-subtitle">{subtitle}</div>'
    )


def hero(kicker, title, help_text, badge, center_html, stats, note):
    """Cartão de destaque: anel ou número grande ao centro, estatísticas ao lado."""
    stats_html = "".join(
        f'<div><div class="stat-label">{label}</div><div class="stat-value">{capitalize(value)}</div></div>'
        for label, value in stats
    )
    badge_html = f'<span class="badge">{capitalize(badge)}</span>' if badge else ""
    with st.container(border=True, key="hero"):
        st.html(f"""
<div class="hero-top">
  <div><div class="hero-kicker">{kicker}</div>
  <div class="hero-title">{title} {tip(help_text)}</div></div>
  {badge_html}
</div>
<div class="hero-body">{center_html}<div class="hero-stats">{stats_html}</div></div>
<p class="hero-note">{note}</p>""")


def period_control(key):
    current = st.session_state.get("period_days", 7)
    default = next(label for label, days in PERIODS.items() if days == current)
    choice = st.segmented_control(
        "Período", list(PERIODS), default=default, key=f"period-{key}",
        label_visibility="collapsed",
    )
    days = PERIODS.get(choice, current)
    st.session_state["period_days"] = days
    return days


def page_header(group, eyebrow, subtitle):
    info = GROUPS[group]
    set_accent(info["color"])
    text, control = st.columns([4, 1], vertical_alignment="bottom")
    text.html(f"""
<div class="eyebrow">{icon(info['icon'])} {eyebrow}</div>
<div class="page-title">{info['title']}</div>
<div class="page-subtitle">{subtitle}</div>""")
    with control:
        return period_control(group)


def synced_at():
    if not db.DB_FILE.exists():
        return "Ainda não sincronizado"
    moment = datetime.fromtimestamp(db.DB_FILE.stat().st_mtime)
    day = "hoje" if moment.date() == date.today() else f"{moment:%d/%m}"
    return f"Dados atualizados {day}, {moment:%H:%M}"


def long_date(day):
    return f"{WEEKDAYS[day.weekday()]}, {day.day} de {MONTHS[day.month - 1]}"
