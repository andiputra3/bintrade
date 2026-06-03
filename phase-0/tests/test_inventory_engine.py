from __future__ import annotations

from core.inventory_engine import InventoryEngine
from models.trade import TradeSide


def test_inventory_buy_updates_cash_inventory_and_average_entry() -> None:
    engine = InventoryEngine.with_cash(1_000.0)

    trade = engine.buy(symbol="BTCUSDT", qty=2.0, price=100.0)

    assert trade.side is TradeSide.BUY
    assert engine.inventory.cash == 800.0
    assert engine.inventory.inventory_qty == 2.0
    assert engine.inventory.average_entry == 100.0
    assert engine.inventory.equity == 1_000.0


def test_inventory_sell_updates_realized_pnl() -> None:
    engine = InventoryEngine.with_cash(1_000.0)
    engine.buy(symbol="BTCUSDT", qty=2.0, price=100.0)

    trade = engine.sell(symbol="BTCUSDT", qty=1.0, price=120.0)

    assert trade.side is TradeSide.SELL
    assert engine.inventory.cash == 920.0
    assert engine.inventory.inventory_qty == 1.0
    assert engine.inventory.realized_pnl == 20.0
    assert engine.inventory.unrealized_pnl == 20.0
    assert engine.inventory.equity == 1_040.0


def test_inventory_buyback_records_buyback_trade() -> None:
    engine = InventoryEngine.with_cash(1_000.0)

    trade = engine.buyback(symbol="BTCUSDT", qty=1.0, price=90.0)

    assert trade.side is TradeSide.BUYBACK
    assert engine.inventory.inventory_qty == 1.0
