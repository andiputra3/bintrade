"""
Event Engine — all strategy events go through here.
No strategy may bypass this engine (MASTER_SPEC rule).

Allowed events:
  ENTER_BIN, EXIT_BIN, BUY, SELL, BUYBACK,
  TAKE_PROFIT, STOP_LOSS, TRAILING_STOP, TRAILING_TP,
  TRAILING_ARMED, PEAK_UPDATE, BIN_RECENTER
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EventType(str, Enum):
    ENTER_BIN      = "ENTER_BIN"
    EXIT_BIN       = "EXIT_BIN"
    BUY            = "BUY"
    SELL           = "SELL"
    BUYBACK        = "BUYBACK"
    TAKE_PROFIT    = "TAKE_PROFIT"
    STOP_LOSS      = "STOP_LOSS"
    TRAILING_STOP  = "TRAILING_STOP"
    TRAILING_TP    = "TRAILING_TP"
    TRAILING_ARMED = "TRAILING_ARMED"
    PEAK_UPDATE    = "PEAK_UPDATE"
    BIN_RECENTER   = "BIN_RECENTER"


@dataclass
class Event:
    event_type: EventType
    candle_idx: int
    timestamp: int              # epoch ms
    price: float
    bin_id: int
    qty: float = 0.0
    usdt_value: float = 0.0
    pnl: float = 0.0
    note: str = ""

    def __repr__(self):
        parts = [
            f"[{self.candle_idx:05d}]",
            f"{self.event_type.value:<14}",
            f"BIN{self.bin_id:+d}",
            f"@${self.price:,.0f}",
        ]
        if self.qty:
            parts.append(f"qty={self.qty:.4f}")
        if self.pnl:
            sign = "+" if self.pnl >= 0 else ""
            parts.append(f"pnl={sign}${self.pnl:.2f}")
        if self.note:
            parts.append(f"({self.note})")
        return "  ".join(parts)


class EventEngine:
    """
    Central event bus. All strategies emit events here.
    Stores full history for replay, export, and analytics.
    """

    def __init__(self):
        self._log: list[Event] = []
        self._listeners: dict[EventType, list] = {e: [] for e in EventType}

    # ------------------------------------------------------------------
    # Emit
    # ------------------------------------------------------------------

    def emit(
        self,
        event_type: EventType,
        candle_idx: int,
        timestamp: int,
        price: float,
        bin_id: int,
        qty: float = 0.0,
        usdt_value: float = 0.0,
        pnl: float = 0.0,
        note: str = "",
    ) -> Event:
        ev = Event(
            event_type=event_type,
            candle_idx=candle_idx,
            timestamp=timestamp,
            price=price,
            bin_id=bin_id,
            qty=qty,
            usdt_value=usdt_value,
            pnl=pnl,
            note=note,
        )
        self._log.append(ev)
        for fn in self._listeners[event_type]:
            fn(ev)
        return ev

    # ------------------------------------------------------------------
    # Subscribe
    # ------------------------------------------------------------------

    def on(self, event_type: EventType, fn):
        """Register a callback for a specific event type."""
        self._listeners[event_type].append(fn)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_log(self) -> list[Event]:
        return list(self._log)

    def get_trades(self) -> list[Event]:
        trade_types = {
            EventType.BUY,
            EventType.SELL,
            EventType.BUYBACK,
            EventType.TAKE_PROFIT,
            EventType.STOP_LOSS,
            EventType.TRAILING_STOP,
            EventType.TRAILING_TP,
        }
        return [e for e in self._log if e.event_type in trade_types]

    def count(self, event_type: Optional[EventType] = None) -> int:
        if event_type is None:
            return len(self._log)
        return sum(1 for e in self._log if e.event_type == event_type)

    def reset(self):
        self._log.clear()
        self._listeners = {e: [] for e in EventType}
