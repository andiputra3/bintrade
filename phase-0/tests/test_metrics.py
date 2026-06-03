from __future__ import annotations

from datetime import datetime, timezone

from core.metrics import MetricsCalculator
from core.trade_log import TradeLog
from models.inventory import Inventory
from models.event import EventType


def test_metrics_generated_from_trade_log() -> None:
    trade_log = TradeLog()
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    trade_log.append(
        timestamp=timestamp,
        price=100.0,
        bin_id=-1,
        event_type=EventType.BUY,
        action="BUY",
        qty=1.0,
        inventory=Inventory(cash=900.0, inventory_qty=1.0, inventory_value=100.0, equity=1_000.0),
    )
    trade_log.append(
        timestamp=timestamp,
        price=120.0,
        bin_id=1,
        event_type=EventType.TAKE_PROFIT,
        action="SELL",
        qty=0.2,
        inventory=Inventory(
            cash=924.0,
            inventory_qty=0.8,
            inventory_value=96.0,
            realized_pnl=4.0,
            unrealized_pnl=16.0,
            equity=1_020.0,
        ),
    )
    trade_log.append(
        timestamp=timestamp,
        price=110.0,
        bin_id=0,
        event_type=EventType.TRAILING_STOP,
        action="SELL",
        qty=0.8,
        inventory=Inventory(cash=1_012.0, realized_pnl=12.0, equity=1_012.0),
    )

    metrics = MetricsCalculator().calculate(trade_log)

    assert metrics.total_pnl == 12.0
    assert metrics.equity == 1_012.0
    assert metrics.trade_count == 3
    assert metrics.buy_count == 1
    assert metrics.sell_count == 2
    assert metrics.tp_count == 1
    assert metrics.trailing_exit_count == 1
    assert metrics.win_rate == 100.0
    assert metrics.profit_factor == 12.0
