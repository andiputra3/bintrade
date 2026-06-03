from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Inventory:
    cash: float
    inventory_qty: float = 0.0
    inventory_value: float = 0.0
    average_entry: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    equity: float = 0.0

    def __post_init__(self) -> None:
        if self.equity == 0.0:
            self.equity = self.cash + self.inventory_value
