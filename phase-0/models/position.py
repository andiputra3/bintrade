from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PositionStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class Position:
    position_id: str
    entry_price: float
    entry_bin: int
    qty: float
    remaining_qty: float
    realized_pnl: float = 0.0
    status: PositionStatus = PositionStatus.OPEN

    @property
    def is_open(self) -> bool:
        return self.status is PositionStatus.OPEN
