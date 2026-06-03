from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TradeSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    BUYBACK = "BUYBACK"


@dataclass(frozen=True)
class Trade:
    id: str
    symbol: str
    side: TradeSide
    quantity: float
    price: float
    timestamp: datetime
    fee: float = 0.0
