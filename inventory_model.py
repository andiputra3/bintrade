"""
Inventory Model — tracks all financial state.
Spec fields: cash, inventory_qty, inventory_value,
             average_entry, realized_pnl, unrealized_pnl, equity
"""
from dataclasses import dataclass, field


@dataclass
class InventoryModel:
    initial_capital: float

    # State (mutated by engine)
    cash: float = field(init=False)
    inventory_qty: float = 0.0
    average_entry: float = 0.0
    realized_pnl: float = 0.0

    # Internal tracking
    _peak_equity: float = field(init=False, repr=False)
    _max_drawdown: float = 0.0
    _total_buy_value: float = 0.0
    _total_sell_value: float = 0.0

    def __post_init__(self):
        self.cash = self.initial_capital
        self._peak_equity = self.initial_capital

    # ------------------------------------------------------------------
    # Derived properties
    # ------------------------------------------------------------------

    def inventory_value(self, current_price: float) -> float:
        return self.inventory_qty * current_price

    def unrealized_pnl(self, current_price: float) -> float:
        if self.inventory_qty <= 0 or self.average_entry <= 0:
            return 0.0
        return (current_price - self.average_entry) * self.inventory_qty

    def equity(self, current_price: float) -> float:
        return self.cash + self.inventory_value(current_price)

    def total_pnl(self, current_price: float) -> float:
        return self.realized_pnl + self.unrealized_pnl(current_price)

    def max_drawdown(self, current_price: float) -> float:
        eq = self.equity(current_price)
        if eq > self._peak_equity:
            self._peak_equity = eq
        if self._peak_equity > 0:
            dd = (self._peak_equity - eq) / self._peak_equity * 100
            if dd > self._max_drawdown:
                self._max_drawdown = dd
        return self._max_drawdown

    def profit_factor(self) -> float:
        if self._total_sell_value <= 0:
            return 0.0
        return self._total_sell_value / max(self._total_buy_value, 1e-9)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def buy(self, qty: float, price: float) -> float:
        """
        Execute a buy. Returns actual cost in USDT.
        Updates average_entry using weighted average.
        """
        cost = qty * price
        if cost > self.cash:
            qty = self.cash / price
            cost = self.cash

        if qty <= 0:
            return 0.0

        # Weighted average entry
        if self.inventory_qty > 0:
            self.average_entry = (
                (self.average_entry * self.inventory_qty + price * qty)
                / (self.inventory_qty + qty)
            )
        else:
            self.average_entry = price

        self.inventory_qty += qty
        self.cash -= cost
        self._total_buy_value += cost
        return cost

    def sell(self, qty: float, price: float) -> tuple[float, float]:
        """
        Execute a sell. Returns (proceeds, realized_pnl).
        qty is clamped to available inventory.
        """
        qty = min(qty, self.inventory_qty)
        if qty <= 0:
            return 0.0, 0.0

        proceeds = qty * price
        cost_basis = qty * self.average_entry
        pnl = proceeds - cost_basis

        self.inventory_qty -= qty
        self.cash += proceeds
        self.realized_pnl += pnl
        self._total_sell_value += proceeds

        if self.inventory_qty < 1e-8:
            self.inventory_qty = 0.0
            self.average_entry = 0.0

        return proceeds, pnl

    def sell_pct(self, pct: float, price: float) -> tuple[float, float, float]:
        """
        Sell a percentage (0-100) of current inventory.
        Returns (qty_sold, proceeds, realized_pnl).
        """
        qty = self.inventory_qty * (pct / 100)
        proceeds, pnl = self.sell(qty, price)
        return qty, proceeds, pnl

    def sell_all(self, price: float) -> tuple[float, float]:
        """Liquidate entire position. Returns (proceeds, realized_pnl)."""
        return self.sell(self.inventory_qty, price)

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def snapshot(self, current_price: float) -> dict:
        return {
            "cash": round(self.cash, 4),
            "inventory_qty": round(self.inventory_qty, 6),
            "inventory_value": round(self.inventory_value(current_price), 4),
            "average_entry": round(self.average_entry, 2),
            "realized_pnl": round(self.realized_pnl, 4),
            "unrealized_pnl": round(self.unrealized_pnl(current_price), 4),
            "total_pnl": round(self.total_pnl(current_price), 4),
            "equity": round(self.equity(current_price), 4),
            "max_drawdown_pct": round(self.max_drawdown(current_price), 4),
        }

    def reset(self):
        self.cash = self.initial_capital
        self.inventory_qty = 0.0
        self.average_entry = 0.0
        self.realized_pnl = 0.0
        self._peak_equity = self.initial_capital
        self._max_drawdown = 0.0
        self._total_buy_value = 0.0
        self._total_sell_value = 0.0
