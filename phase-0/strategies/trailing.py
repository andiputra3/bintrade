from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from core.event_engine import EventEngine
from models.event import Event, EventType


class TrailingMode(StrEnum):
    PERCENT = "percent"
    BIN = "bin"
    HYBRID = "hybrid"


@dataclass
class TrailingEngine:
    """Track peak price/bin and emit trailing stop exits."""

    mode: TrailingMode | str = TrailingMode.HYBRID
    trail_peak_pct: float = 1.5
    trail_peak_bin: int = 2
    highest_price: float | None = None
    highest_bin: int | None = None

    def update_peak(self, price: float, bin_id: int) -> None:
        if self.highest_price is None or price > self.highest_price:
            self.highest_price = price

        if self.highest_bin is None or bin_id > self.highest_bin:
            self.highest_bin = bin_id

    def should_exit(self, price: float, bin_id: int) -> bool:
        mode = TrailingMode(self.mode)
        if self.highest_price is None or self.highest_bin is None:
            return False

        percent_exit = self._percent_exit(price)
        bin_exit = self._bin_exit(bin_id)

        if mode is TrailingMode.PERCENT:
            return percent_exit
        if mode is TrailingMode.BIN:
            return bin_exit
        if mode is TrailingMode.HYBRID:
            return percent_exit or bin_exit

        raise ValueError(f"Unsupported trailing mode: {mode}")

    def generate_exit_event(
        self,
        event_engine: EventEngine,
        price: float,
        bin_id: int,
    ) -> Event | None:
        if not self.should_exit(price=price, bin_id=bin_id):
            return None

        return event_engine.emit_trade_event(
            event_type=EventType.TRAILING_STOP,
            price=price,
            metadata={
                "mode": TrailingMode(self.mode).value,
                "bin_id": bin_id,
                "highest_price": self.highest_price,
                "highest_bin": self.highest_bin,
            },
        )

    def _percent_exit(self, price: float) -> bool:
        if self.highest_price is None:
            return False
        drawdown_pct = ((self.highest_price - price) / self.highest_price) * 100
        return drawdown_pct >= self.trail_peak_pct

    def _bin_exit(self, bin_id: int) -> bool:
        if self.highest_bin is None:
            return False
        return bin_id <= self.highest_bin - self.trail_peak_bin
