from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskConfig:
    max_position_pct: float = 100.0
    max_capital_per_bin: float = 0.0
    max_daily_loss_pct: float = 100.0
    max_drawdown_pct: float = 100.0
    max_leverage: float = 1.0


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    action: str | None = None
    reason: str | None = None

    @classmethod
    def approved_order(cls) -> RiskDecision:
        return cls(approved=True)

    @classmethod
    def reject_order(cls, reason: str) -> RiskDecision:
        return cls(approved=False, action="REJECT_ORDER", reason=reason)
