from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.replay_engine import ReplayEngine


def test_replay_can_process_sample_btcusdt_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "BTCUSDT-1m.csv"
    rows = []
    prices = [
        100,
        99,
        98,
        97,
        96,
        95,
        94,
        93,
        92,
        91,
        90,
        89,
        88,
        87,
        84,
        81,
        78,
        75,
        72,
        69,
        72,
        75,
        78,
        81,
        84,
        87,
        90,
        93,
        96,
        99,
    ]
    for minute, close in enumerate(prices):
        rows.append(
            {
                "timestamp": f"2026-01-01 00:{minute:02d}:00",
                "open": close + 0.5,
                "high": close + 1,
                "low": close - 1,
                "close": close,
            }
        )
    pd.DataFrame(rows).to_csv(csv_path, index=False)

    result = ReplayEngine(initial_cash=1_000.0).run_csv(csv_path)
    log_frame = result.trade_log.to_dataframe()

    assert not log_frame.empty
    assert set(log_frame.columns) == {
        "timestamp",
        "price",
        "bin",
        "event",
        "action",
        "qty",
        "cash",
        "inventory",
        "equity",
        "realized_pnl",
        "unrealized_pnl",
    }
    assert "ENTER_BIN" in set(log_frame["event"])
    assert result.metrics.trade_count > 0
    assert result.metrics.equity > 0
