from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PositionSide(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class Position:
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float
    opened_at: datetime
    current_price: float | None = None
    closed_at: datetime | None = None

    @property
    def is_open(self) -> bool:
        return self.closed_at is None
