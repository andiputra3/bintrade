from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from models.inventory import Inventory
from models.trade import Trade, TradeSide


@dataclass
class InventoryEngine:
    """Track cash, inventory, average entry, equity, and PnL."""

    inventory: Inventory
    trades: list[Trade]

    @classmethod
    def with_cash(cls, cash: float) -> InventoryEngine:
        if cash < 0:
            raise ValueError("cash must be greater than or equal to zero")
        return cls(inventory=Inventory(cash=cash, equity=cash), trades=[])

    def buy(
        self,
        symbol: str,
        qty: float,
        price: float,
        timestamp: datetime | None = None,
        fee: float = 0.0,
        side: TradeSide = TradeSide.BUY,
    ) -> Trade:
        self._validate_order(qty=qty, price=price, fee=fee)
        cost = (qty * price) + fee
        if cost > self.inventory.cash:
            raise ValueError("insufficient cash")

        previous_cost_basis = self.inventory.average_entry * self.inventory.inventory_qty
        new_qty = self.inventory.inventory_qty + qty
        self.inventory.average_entry = (previous_cost_basis + (qty * price)) / new_qty
        self.inventory.inventory_qty = new_qty
        self.inventory.cash -= cost
        self.mark_to_market(price)

        trade = self._create_trade(symbol=symbol, side=side, qty=qty, price=price, timestamp=timestamp, fee=fee)
        self.trades.append(trade)
        return trade

    def sell(
        self,
        symbol: str,
        qty: float,
        price: float,
        timestamp: datetime | None = None,
        fee: float = 0.0,
    ) -> Trade:
        self._validate_order(qty=qty, price=price, fee=fee)
        if qty > self.inventory.inventory_qty:
            raise ValueError("insufficient inventory")

        proceeds = (qty * price) - fee
        self.inventory.cash += proceeds
        self.inventory.inventory_qty -= qty
        self.inventory.realized_pnl += ((price - self.inventory.average_entry) * qty) - fee

        if self.inventory.inventory_qty == 0:
            self.inventory.average_entry = 0.0

        self.mark_to_market(price)

        trade = self._create_trade(
            symbol=symbol,
            side=TradeSide.SELL,
            qty=qty,
            price=price,
            timestamp=timestamp,
            fee=fee,
        )
        self.trades.append(trade)
        return trade

    def buyback(
        self,
        symbol: str,
        qty: float,
        price: float,
        timestamp: datetime | None = None,
        fee: float = 0.0,
    ) -> Trade:
        return self.buy(
            symbol=symbol,
            qty=qty,
            price=price,
            timestamp=timestamp,
            fee=fee,
            side=TradeSide.BUYBACK,
        )

    def mark_to_market(self, price: float) -> Inventory:
        if price <= 0:
            raise ValueError("price must be greater than zero")

        self.inventory.inventory_value = self.inventory.inventory_qty * price
        self.inventory.unrealized_pnl = (
            (price - self.inventory.average_entry) * self.inventory.inventory_qty
            if self.inventory.inventory_qty > 0
            else 0.0
        )
        self.inventory.equity = self.inventory.cash + self.inventory.inventory_value
        return self.inventory

    @staticmethod
    def _validate_order(qty: float, price: float, fee: float) -> None:
        if qty <= 0:
            raise ValueError("qty must be greater than zero")
        if price <= 0:
            raise ValueError("price must be greater than zero")
        if fee < 0:
            raise ValueError("fee must be greater than or equal to zero")

    @staticmethod
    def _create_trade(
        symbol: str,
        side: TradeSide,
        qty: float,
        price: float,
        timestamp: datetime | None,
        fee: float,
    ) -> Trade:
        return Trade(
            id=str(uuid4()),
            symbol=symbol,
            side=side,
            quantity=qty,
            price=price,
            timestamp=timestamp or datetime.now(timezone.utc),
            fee=fee,
        )
