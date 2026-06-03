from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class EventType(StrEnum):
    ENTER_BIN = "ENTER_BIN"
    EXIT_BIN = "EXIT_BIN"
    BUY = "BUY"
    SELL = "SELL"
    BUYBACK = "BUYBACK"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"


@dataclass(frozen=True)
class Event:
    id: str
    type: EventType
    timestamp: datetime
    price: float
    bin_index: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
