from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime

import pandas as pd

from models.event import EventType
from models.inventory import Inventory


@dataclass(frozen=True)
class TradeLogEntry:
    timestamp: datetime
    price: float
    bin: int | None
    event: str
    action: str
    qty: float
    cash: float
    inventory: float
    equity: float
    realized_pnl: float
    unrealized_pnl: float


@dataclass
class TradeLog:
    entries: list[TradeLogEntry] = field(default_factory=list)

    def append(
        self,
        timestamp: datetime,
        price: float,
        bin_id: int | None,
        event_type: EventType | str,
        action: str,
        qty: float,
        inventory: Inventory,
    ) -> TradeLogEntry:
        event = event_type.value if isinstance(event_type, EventType) else event_type
        entry = TradeLogEntry(
            timestamp=timestamp,
            price=price,
            bin=bin_id,
            event=event,
            action=action,
            qty=qty,
            cash=inventory.cash,
            inventory=inventory.inventory_qty,
            equity=inventory.equity,
            realized_pnl=inventory.realized_pnl,
            unrealized_pnl=inventory.unrealized_pnl,
        )
        self.entries.append(entry)
        return entry

    def to_dataframe(self) -> pd.DataFrame:
        columns = [
            "timestamp",
            "price",
            "bin",
            "event",
            "action",
            "qty",
            "cash",
            "inventory",
            "equity",
            "realized_pnl",
            "unrealized_pnl",
        ]
        return pd.DataFrame([asdict(entry) for entry in self.entries], columns=columns)
