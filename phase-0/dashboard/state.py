from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import streamlit as st

from core.bin_builder import BinBuilder
from core.replay_engine import ReplayEngine, ReplayResult
from strategies.bot23 import BOT23Strategy
from strategies.single_side_bid import SingleSideBidStrategy
from strategies.trailing import TrailingEngine


@dataclass(frozen=True)
class ReplaySettings:
    capital: float
    atr_multiplier: float
    bot_variant: str
    distribution_mode: str
    trailing_mode: str


def configure_page(title: str) -> None:
    st.set_page_config(page_title=title, page_icon="BIN", layout="wide")


def initialize_state() -> None:
    st.session_state.setdefault("uploaded_frame", None)
    st.session_state.setdefault("replay_result", None)
    st.session_state.setdefault("replay_settings", None)
    st.session_state.setdefault("source_name", "Sample BTCUSDT 1m")


def reset_replay() -> None:
    st.session_state["replay_result"] = None
    st.session_state["replay_settings"] = None


def sample_btcusdt_frame() -> pd.DataFrame:
    prices = [
        100, 99, 98, 97, 96, 95, 94, 93, 92, 91,
        90, 89, 88, 87, 84, 81, 78, 75, 72, 69,
        72, 75, 78, 81, 84, 87, 90, 93, 96, 99,
    ]
    return pd.DataFrame(
        [
            {
                "timestamp": f"2026-01-01 00:{minute:02d}:00",
                "open": close + 0.5,
                "high": close + 1,
                "low": close - 1,
                "close": close,
            }
            for minute, close in enumerate(prices)
        ]
    )


def active_frame() -> pd.DataFrame:
    frame = st.session_state.get("uploaded_frame")
    if frame is None:
        return sample_btcusdt_frame()
    return frame


def set_uploaded_file(uploaded_file: Any | None) -> None:
    if uploaded_file is None:
        return

    st.session_state["uploaded_frame"] = pd.read_csv(uploaded_file)
    st.session_state["source_name"] = uploaded_file.name
    reset_replay()


def run_replay(settings: ReplaySettings) -> ReplayResult:
    engine = ReplayEngine(
        initial_cash=settings.capital,
        bin_builder=BinBuilder(atr_multiplier=settings.atr_multiplier),
        single_side_bid=SingleSideBidStrategy(mode=settings.distribution_mode),
        bot23=BOT23Strategy(variant=settings.bot_variant),
        trailing_engine=TrailingEngine(mode=settings.trailing_mode),
    )
    result = engine.run(active_frame())
    st.session_state["replay_result"] = result
    st.session_state["replay_settings"] = settings
    return result


def replay_result() -> ReplayResult | None:
    return st.session_state.get("replay_result")


def replay_frame() -> pd.DataFrame:
    result = replay_result()
    if result is None:
        return pd.DataFrame()
    return result.trade_log.to_dataframe()


def ensure_replay() -> ReplayResult:
    result = replay_result()
    if result is None:
        st.info("Run replay from Control Center first.")
        st.stop()
    return result


def current_portfolio() -> dict[str, float]:
    frame = replay_frame()
    if frame.empty:
        return {
            "cash": 0.0,
            "inventory": 0.0,
            "average_entry": 0.0,
            "equity": 0.0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
        }

    latest = frame.iloc[-1]
    inventory_qty = float(latest["inventory"])
    price = float(latest["price"])
    unrealized_pnl = float(latest["unrealized_pnl"])
    average_entry = price - (unrealized_pnl / inventory_qty) if inventory_qty else 0.0

    return {
        "cash": float(latest["cash"]),
        "inventory": inventory_qty,
        "average_entry": average_entry,
        "equity": float(latest["equity"]),
        "realized_pnl": float(latest["realized_pnl"]),
        "unrealized_pnl": unrealized_pnl,
    }
