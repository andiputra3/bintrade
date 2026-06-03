from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from dashboard.state import (
    ReplaySettings,
    active_frame,
    configure_page,
    initialize_state,
    replay_result,
    reset_replay,
    run_replay,
    set_uploaded_file,
)


configure_page("BIN Trade Control Center")
initialize_state()

st.title("Control Center")

with st.sidebar:
    uploaded_file = st.file_uploader("BTCUSDT 1m CSV", type=["csv"])
    set_uploaded_file(uploaded_file)

    capital = st.number_input("Capital", min_value=100.0, value=10_000.0, step=100.0)
    atr_multiplier = st.number_input("ATR Multiplier", min_value=0.1, value=2.0, step=0.1)
    bot_variant = st.selectbox("BOT Variant", ["BOT11", "BOT22", "BOT23", "BOT35"], index=2)
    distribution_mode = st.selectbox("Distribution Mode", ["meteora", "linear", "exponential"], index=0)
    trailing_mode = st.selectbox("Trailing Mode", ["hybrid", "percent", "bin"], index=0)

    start = st.button("Start Replay", type="primary", use_container_width=True)
    reset = st.button("Reset Replay", use_container_width=True)

if reset:
    reset_replay()
    st.rerun()

settings = ReplaySettings(
    capital=capital,
    atr_multiplier=atr_multiplier,
    bot_variant=bot_variant,
    distribution_mode=distribution_mode,
    trailing_mode=trailing_mode,
)

if start:
    run_replay(settings)

frame = active_frame()
result = replay_result()

cols = st.columns(4)
cols[0].metric("Source Rows", f"{len(frame):,}")
cols[1].metric("Capital", f"{capital:,.2f}")
cols[2].metric("ATR Multiplier", f"{atr_multiplier:.2f}")
cols[3].metric("Replay", "Ready" if result else "Not Started")

if result is not None:
    metrics = result.metrics
    cols = st.columns(5)
    cols[0].metric("Equity", f"{metrics.equity:,.2f}")
    cols[1].metric("Total PnL", f"{metrics.total_pnl:,.2f}")
    cols[2].metric("Max Drawdown", f"{metrics.max_drawdown:.2f}%")
    cols[3].metric("Win Rate", f"{metrics.win_rate:.2f}%")
    cols[4].metric("Trades", metrics.trade_count)

st.dataframe(frame.tail(50), use_container_width=True, hide_index=True)
