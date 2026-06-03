from __future__ import annotations

from core.event_engine import EventEngine
from models.event import EventType
from strategies.trailing import TrailingEngine


def test_trailing_percent_works() -> None:
    trailing = TrailingEngine(mode="percent")
    trailing.update_peak(price=100.0, bin_id=0)

    assert trailing.should_exit(price=98.5, bin_id=0)


def test_trailing_bin_works() -> None:
    trailing = TrailingEngine(mode="bin")
    trailing.update_peak(price=100.0, bin_id=5)

    assert trailing.should_exit(price=99.0, bin_id=3)


def test_trailing_hybrid_works() -> None:
    trailing = TrailingEngine()
    trailing.update_peak(price=100.0, bin_id=5)

    assert trailing.should_exit(price=99.0, bin_id=3)
    assert trailing.should_exit(price=98.5, bin_id=5)


def test_generate_exit_event_uses_event_engine() -> None:
    trailing = TrailingEngine(mode="percent")
    trailing.update_peak(price=100.0, bin_id=0)
    event_engine = EventEngine(current_bin_index=0)

    event = trailing.generate_exit_event(event_engine=event_engine, price=98.5, bin_id=0)

    assert event is not None
    assert event.type is EventType.TRAILING_STOP
    assert event in event_engine.events
