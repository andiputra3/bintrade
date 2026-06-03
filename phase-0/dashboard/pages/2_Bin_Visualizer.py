from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from dashboard.state import configure_page, ensure_replay, initialize_state, replay_frame


configure_page("BIN Visualizer")
initialize_state()
ensure_replay()

st.title("Bin Visualizer")

log = replay_frame()
active = log.iloc[-1]
active_bin = active["bin"] if pd.notna(active["bin"]) else None

cols = st.columns(3)
cols[0].metric("Current Price", f"{float(active['price']):,.2f}")
cols[1].metric("Current Bin", "N/A" if active_bin is None else int(active_bin))
cols[2].metric("Events", len(log))

summary = (
    log.dropna(subset=["bin"])
    .assign(bin=lambda frame: frame["bin"].astype(int))
    .groupby("bin", as_index=False)
    .agg(
        allocation=("qty", lambda values: float(values.sum())),
        inventory=("inventory", "last"),
        hit_count=("event", "count"),
        last_event=("event", "last"),
    )
    .sort_values("bin")
)
summary["active"] = summary["bin"].eq(active_bin)


def highlight_active(row: pd.Series) -> list[str]:
    return ["background-color: #fff3bf" if row["active"] else "" for _ in row]


st.dataframe(summary.style.apply(highlight_active, axis=1), use_container_width=True, hide_index=True)
