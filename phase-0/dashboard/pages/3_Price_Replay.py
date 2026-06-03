from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import plotly.graph_objects as go
import streamlit as st

from dashboard.state import active_frame, configure_page, ensure_replay, initialize_state, replay_frame


configure_page("Price Replay")
initialize_state()
ensure_replay()

st.title("Price Replay")

price_frame = active_frame().copy()
price_frame["timestamp"] = price_frame["timestamp"].astype(str)
log = replay_frame()

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=price_frame["timestamp"],
        y=price_frame["close"],
        mode="lines",
        name="Close",
        line={"color": "#2563eb", "width": 2},
    )
)

marker_styles = {
    "BUY": {"color": "#16a34a", "symbol": "triangle-up", "label": "BUY"},
    "SELL": {"color": "#dc2626", "symbol": "triangle-down", "label": "SELL"},
    "BUYBACK": {"color": "#0891b2", "symbol": "circle", "label": "BUYBACK"},
}

for action, style in marker_styles.items():
    points = log[log["action"] == action]
    if not points.empty:
        fig.add_trace(
            go.Scatter(
                x=points["timestamp"].astype(str),
                y=points["price"],
                mode="markers",
                name=style["label"],
                marker={"color": style["color"], "symbol": style["symbol"], "size": 10},
            )
        )

trailing = log[log["event"] == "TRAILING_STOP"]
if not trailing.empty:
    fig.add_trace(
        go.Scatter(
            x=trailing["timestamp"].astype(str),
            y=trailing["price"],
            mode="markers",
            name="TRAILING",
            marker={"color": "#7c3aed", "symbol": "x", "size": 11},
        )
    )

fig.update_layout(
    height=620,
    margin={"l": 20, "r": 20, "t": 30, "b": 20},
    xaxis_title="Time",
    yaxis_title="Price",
    hovermode="x unified",
)

st.plotly_chart(fig, use_container_width=True)
