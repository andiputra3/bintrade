from __future__ import annotations

from core.bin_builder import BinBuilder
from core.event_engine import EventEngine
from models.event import EventType


def test_dynamic_atr_bins_are_built_from_atr() -> None:
    builder = BinBuilder(atr_multiplier=2.0)
    bins = builder.build_bins(reference_price=100.0, atr=5.0)

    assert len(bins) == 41
    assert bins[0].index == -20
    assert bins[-1].index == 20
    assert bins[20].index == 0
    assert bins[20].lower_price == 100.0
    assert bins[20].upper_price == 110.0


def test_locate_bin_and_event_engine_emit_enter_bin() -> None:
    builder = BinBuilder(atr_multiplier=1.0)
    bin_ = builder.locate_bin(price=106.0, reference_price=100.0, atr=5.0)

    assert bin_ is not None
    assert bin_.index == 1

    engine = EventEngine()
    events = engine.on_bin(bin_=bin_, price=106.0)

    assert len(events) == 1
    assert events[0].type is EventType.ENTER_BIN
    assert events[0].bin_index == 1
