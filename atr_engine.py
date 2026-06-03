"""
ATR Engine — Dynamic Bin Size Calculator
Spec: bin_size = ATR(14) × atr_multiplier
"""
from collections import deque


class ATREngine:
    """
    Calculates Average True Range (ATR) using Wilder's smoothing method.
    Used to determine dynamic bin size.
    """

    def __init__(self, period: int = 14, atr_multiplier: float = 2.0):
        self.period = period
        self.atr_multiplier = atr_multiplier
        self._highs: deque = deque(maxlen=period + 1)
        self._lows: deque = deque(maxlen=period + 1)
        self._closes: deque = deque(maxlen=period + 1)
        self._true_ranges: deque = deque(maxlen=period)
        self._atr: float | None = None
        self._candle_count: int = 0

    def update(self, high: float, low: float, close: float) -> float | None:
        """
        Feed one candle. Returns current bin_size or None if not enough data.
        """
        prev_close = self._closes[-1] if self._closes else None

        self._highs.append(high)
        self._lows.append(low)
        self._closes.append(close)
        self._candle_count += 1

        # True Range = max(H-L, |H-prevC|, |L-prevC|)
        if prev_close is not None:
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close),
            )
        else:
            tr = high - low

        self._true_ranges.append(tr)

        # Need `period` TRs to compute first ATR
        if len(self._true_ranges) < self.period:
            return None

        if self._atr is None:
            # Initial ATR = simple average of first `period` TRs
            self._atr = sum(self._true_ranges) / self.period
        else:
            # Wilder smoothing: ATR = (prev_ATR * (period-1) + TR) / period
            self._atr = (self._atr * (self.period - 1) + tr) / self.period

        return self.bin_size

    @property
    def atr(self) -> float | None:
        return self._atr

    @property
    def bin_size(self) -> float | None:
        if self._atr is None:
            return None
        return self._atr * self.atr_multiplier

    @property
    def is_ready(self) -> bool:
        return self._atr is not None

    def reset(self):
        self._highs.clear()
        self._lows.clear()
        self._closes.clear()
        self._true_ranges.clear()
        self._atr = None
        self._candle_count = 0
