from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.atr_engine import ATREngine


def test_atr_14_can_be_calculated_from_btcusdt_1m_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "BTCUSDT-1m.csv"
    rows = [
        {
            "timestamp": f"2026-01-01 00:{minute:02d}:00",
            "open": 100 + minute,
            "high": 102 + minute,
            "low": 99 + minute,
            "close": 101 + minute,
            "volume": 10 + minute,
        }
        for minute in range(20)
    ]
    pd.DataFrame(rows).to_csv(csv_path, index=False)

    ohlc = pd.read_csv(csv_path)
    atr = ATREngine(period=14).calculate(ohlc)

    assert atr.name == "ATR_14"
    assert atr.iloc[:13].isna().all()
    assert atr.iloc[13:].notna().all()
    assert atr.iloc[13] == 3.0


def test_atr_requires_ohlc_columns() -> None:
    frame = pd.DataFrame({"high": [1.0], "low": [0.5]})

    try:
        ATREngine().calculate(frame)
    except ValueError as exc:
        assert "close" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing close column")
