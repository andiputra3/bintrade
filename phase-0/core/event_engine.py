from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from models.bin import Bin
from models.event import Event, EventType


@dataclass
class EventEngine:
    """Simple event engine for bin transitions and trade lifecycle actions."""

    current_bin_index: int | None = None
    events: list[Event] = field(default_factory=list)

    def on_bin(self, bin_: Bin | None, price: float, timestamp: datetime | None = None) -> list[Event]:
        """Process a bin observation and return newly generated events."""
        timestamp = timestamp or datetime.now(timezone.utc)
        generated: list[Event] = []

        if bin_ is None:
            if self.current_bin_index is not None:
                generated.append(
                    self._create_event(
                        event_type=EventType.EXIT_BIN,
                        timestamp=timestamp,
                        price=price,
                        bin_index=self.current_bin_index,
                    )
                )
                self.current_bin_index = None
            self.events.extend(generated)
            return generated

        if self.current_bin_index != bin_.bin_id:
            if self.current_bin_index is not None:
                generated.append(
                    self._create_event(
                        event_type=EventType.EXIT_BIN,
                        timestamp=timestamp,
                        price=price,
                        bin_index=self.current_bin_index,
                    )
                )

            generated.append(
                self._create_event(
                    event_type=EventType.ENTER_BIN,
                    timestamp=timestamp,
                    price=price,
                    bin_index=bin_.bin_id,
                )
            )
            self.current_bin_index = bin_.bin_id

        self.events.extend(generated)
        return generated

    def emit_trade_event(
        self,
        event_type: EventType,
        price: float,
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Event:
        """Emit a non-bin event through the event engine."""
        if event_type in {EventType.ENTER_BIN, EventType.EXIT_BIN}:
            raise ValueError(f"Use on_bin for bin transition event: {event_type.value}")

        event = self._create_event(
            event_type=event_type,
            timestamp=timestamp or datetime.now(timezone.utc),
            price=price,
            bin_index=self.current_bin_index,
            metadata=metadata,
        )
        self.events.append(event)
        return event

    @staticmethod
    def _create_event(
        event_type: EventType,
        timestamp: datetime,
        price: float,
        bin_index: int | None,
        metadata: dict[str, Any] | None = None,
    ) -> Event:
        return Event(
            id=str(uuid4()),
            type=event_type,
            timestamp=timestamp,
            price=price,
            bin_index=bin_index,
            metadata=metadata or {},
        )
