from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Bin:
    bin_id: int
    lower_price: float
    upper_price: float
    allocation: float = 0.0
    inventory: float = 0.0
    hit_count: int = 0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    last_event: str | None = None

    def contains(self, price: float) -> bool:
        return self.lower_price <= price < self.upper_price
