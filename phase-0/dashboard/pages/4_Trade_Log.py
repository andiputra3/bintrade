from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from dashboard.state import configure_page, ensure_replay, initialize_state, replay_frame


configure_page("Trade Log")
initialize_state()
ensure_replay()

st.title("Trade Log")

log = replay_frame()
actions = ["ALL"] + sorted(action for action in log["action"].dropna().unique().tolist())
selected = st.selectbox("Filter by action", actions)

filtered = log if selected == "ALL" else log[log["action"] == selected]
view = filtered.rename(
    columns={
        "timestamp": "Time",
        "price": "Price",
        "bin": "Bin",
        "action": "Action",
        "realized_pnl": "Realized PnL",
        "unrealized_pnl": "Unrealized PnL",
    }
)[["Time", "Price", "Bin", "Action", "Realized PnL", "Unrealized PnL"]]

st.dataframe(view, use_container_width=True, hide_index=True)
