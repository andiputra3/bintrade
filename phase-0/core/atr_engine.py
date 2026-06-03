from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ATREngine:
    """Pandas-based Average True Range calculator."""

    period: int = 14

    def calculate(self, ohlc: pd.DataFrame) -> pd.Series:
        """Calculate ATR from an OHLC dataframe.

        The dataframe must include ``high``, ``low``, and ``close`` columns.
        Extra columns such as timestamp, open, or volume are ignored.
        """
        if self.period <= 0:
            raise ValueError("ATR period must be greater than zero")

        required_columns = {"high", "low", "close"}
        missing_columns = required_columns.difference(ohlc.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"OHLC dataframe missing required columns: {missing}")

        high = pd.to_numeric(ohlc["high"], errors="raise")
        low = pd.to_numeric(ohlc["low"], errors="raise")
        close = pd.to_numeric(ohlc["close"], errors="raise")
        previous_close = close.shift(1)

        true_range = pd.concat(
            [
                high - low,
                (high - previous_close).abs(),
                (low - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)

        atr = true_range.rolling(window=self.period, min_periods=self.period).mean()
        atr.name = f"ATR_{self.period}"
        return atr

    def add_atr(self, ohlc: pd.DataFrame, column_name: str | None = None) -> pd.DataFrame:
        """Return a dataframe copy with an ATR column appended."""
        result = ohlc.copy()
        result[column_name or f"atr_{self.period}"] = self.calculate(ohlc)
        return result
