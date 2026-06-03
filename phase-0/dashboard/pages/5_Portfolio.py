from __future__ import annotations

import streamlit as st

from dashboard.state import configure_page, current_portfolio, ensure_replay, initialize_state


configure_page("Portfolio")
initialize_state()
ensure_replay()

st.title("Portfolio")

portfolio = current_portfolio()

cols = st.columns(3)
cols[0].metric("Cash", f"{portfolio['cash']:,.2f}")
cols[1].metric("Inventory", f"{portfolio['inventory']:,.8f}")
cols[2].metric("Average Entry", f"{portfolio['average_entry']:,.2f}")

cols = st.columns(3)
cols[0].metric("Equity", f"{portfolio['equity']:,.2f}")
cols[1].metric("Realized PnL", f"{portfolio['realized_pnl']:,.2f}")
cols[2].metric("Unrealized PnL", f"{portfolio['unrealized_pnl']:,.2f}")
