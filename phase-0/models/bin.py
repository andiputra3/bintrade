from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Bin:
    index: int
    lower_price: float
    upper_price: float
    atr: float
    atr_multiplier: float
    reference_price: float

    def contains(self, price: float) -> bool:
        return self.lower_price <= price < self.upper_price
