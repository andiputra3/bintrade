from __future__ import annotations

from dataclasses import dataclass

from models.inventory import Inventory
from models.risk import RiskConfig, RiskDecision


@dataclass(frozen=True)
class RiskEngine:
    """Validate proposed orders against Phase 0 risk limits."""

    config: RiskConfig = RiskConfig()

    def validate_order(
        self,
        inventory: Inventory,
        order_value: float,
        bin_allocation: float = 0.0,
        daily_realized_pnl: float = 0.0,
        peak_equity: float | None = None,
        leverage: float = 1.0,
    ) -> RiskDecision:
        if order_value <= 0:
            return RiskDecision.reject_order("order_value must be greater than zero")
        if leverage > self.config.max_leverage:
            return RiskDecision.reject_order("max_leverage exceeded")

        equity = inventory.equity
        if equity <= 0:
            return RiskDecision.reject_order("equity must be greater than zero")

        position_pct = (order_value / equity) * 100
        if position_pct > self.config.max_position_pct:
            return RiskDecision.reject_order("max_position_pct exceeded")

        if self.config.max_capital_per_bin > 0 and bin_allocation > self.config.max_capital_per_bin:
            return RiskDecision.reject_order("max_capital_per_bin exceeded")

        if daily_realized_pnl < 0:
            daily_loss_pct = (abs(daily_realized_pnl) / equity) * 100
            if daily_loss_pct > self.config.max_daily_loss_pct:
                return RiskDecision.reject_order("max_daily_loss_pct exceeded")

        if peak_equity is not None and peak_equity > 0:
            drawdown_pct = ((peak_equity - equity) / peak_equity) * 100
            if drawdown_pct > self.config.max_drawdown_pct:
                return RiskDecision.reject_order("max_drawdown_pct exceeded")

        return RiskDecision.approved_order()
