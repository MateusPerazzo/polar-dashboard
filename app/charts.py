"""Leitura do banco e gráficos plotly no estilo do app."""

from contextlib import closing

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import ui
from polar import db

MONTHS_SHORT = ["jan", "fev", "mar", "abr", "mai", "jun",
                "jul", "ago", "set", "out", "nov", "dez"]
GRID = "#2c2c2a"
HOVER_BG = "#23262b"


def load(query, params=(), dates=("date",)):
    with closing(db.connect()) as conn:
        return pd.read_sql_query(query, conn, params=params, parse_dates=list(dates))


def require_data(df):
    if df.empty:
        st.info("Ainda não há dados. Use o botão Sincronizar no topo da página.")
        st.stop()


def rgba(hex_color, alpha):
    red, green, blue = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({red},{green},{blue},{alpha})"


def style(fig, height=300, y_title=None):
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=ui.TONES["neutral"], size=11),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=HOVER_BG, bordercolor=HOVER_BG, font=dict(color="#f0efec")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(color="#c3c2b7")),
        bargap=0.25,
        barcornerradius=4,
        separators=",.",
    )
    fig.update_xaxes(showgrid=False, showline=False, ticks="", automargin=True)
    fig.update_yaxes(gridcolor=GRID, griddash="dot", zeroline=False, ticks="",
                     title=y_title, automargin=True)
    return fig


def daily_ticks(fig, dates, count=5):
    """Rótulos de data em português ("3 out"), poucos para não poluir."""
    dates = pd.Series(pd.to_datetime(dates)).dropna().sort_values().unique()
    if len(dates) == 0:
        return fig
    step = max(1, len(dates) // count)
    ticks = list(dates[::step])
    fig.update_xaxes(
        tickvals=ticks,
        ticktext=[f"{pd.Timestamp(d).day} {MONTHS_SHORT[pd.Timestamp(d).month - 1]}" for d in ticks],
    )
    return fig


def area(x, y, color, name, hover, daily=True, height=300):
    """Linha com área em degradê; o eixo Y se ajusta aos dados, sem começar no zero."""
    values = pd.Series(y)
    low, high = values.min(), values.max()
    pad = max((high - low) * 0.15, 1)
    floor = low - pad
    fig = go.Figure()
    fig.add_scatter(x=x, y=[floor] * len(values), mode="lines", line=dict(width=0),
                    hoverinfo="skip", showlegend=False)
    fig.add_scatter(
        x=x, y=y, name=name, mode="lines",
        line=dict(color=color, width=2),
        fill="tonexty",
        fillgradient=dict(type="vertical",
                          colorscale=[(0, rgba(color, 0)), (1, rgba(color, 0.28))]),
        hovertemplate=hover, showlegend=False,
    )
    fig.update_yaxes(range=[floor, high + pad])
    style(fig, height)
    return daily_ticks(fig, x) if daily else fig


def bars(x, y, color, name, hover, height=300):
    fig = go.Figure(go.Bar(x=x, y=y, name=name, marker=dict(color=color),
                           hovertemplate=hover, showlegend=False))
    return daily_ticks(style(fig, height), x)


def stacked_bars(x, series, hover, height=300):
    """series: lista de (nome, valores, cor)."""
    fig = go.Figure()
    for name, y, color in series:
        fig.add_bar(x=x, y=y, name=name, hovertemplate=hover,
                    marker=dict(color=color, line=dict(color="#121418", width=1.5)))
    fig.update_layout(barmode="stack")
    return daily_ticks(style(fig, height), x)


def show(fig):
    st.plotly_chart(fig, theme=None, width="stretch", config={"displayModeBar": False})


def day_picker(dates, label, key):
    options = sorted({f"{day:%Y-%m-%d}" for day in dates}, reverse=True)
    return st.selectbox(
        label, options, key=key, label_visibility="collapsed",
        format_func=lambda day: pd.Timestamp(day).strftime("%d/%m/%Y"),
    )


def summarize(df, column):
    """Último valor, variação contra a média dos 7 registros anteriores e a série."""
    values = df[["date", column]].dropna()
    if values.empty:
        return None
    last = values[column].iloc[-1]
    baseline = values[column].iloc[-8:-1].mean()
    return {
        "last": last,
        "baseline": baseline,
        "delta": None if pd.isna(baseline) else last - baseline,
        "date": values["date"].iloc[-1],
        "values": values[column],
    }
