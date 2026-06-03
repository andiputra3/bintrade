from __future__ import annotations

from core.risk_engine import RiskEngine
from models.inventory import Inventory
from models.risk import RiskConfig


def test_risk_approves_order_within_limits() -> None:
    inventory = Inventory(cash=1_000.0, equity=1_000.0)
    risk = RiskEngine(config=RiskConfig(max_position_pct=50.0, max_leverage=2.0))

    decision = risk.validate_order(inventory=inventory, order_value=400.0, leverage=1.5)

    assert decision.approved
    assert decision.action is None


def test_risk_rejects_order_above_position_limit() -> None:
    inventory = Inventory(cash=1_000.0, equity=1_000.0)
    risk = RiskEngine(config=RiskConfig(max_position_pct=25.0))

    decision = risk.validate_order(inventory=inventory, order_value=300.0)

    assert not decision.approved
    assert decision.action == "REJECT_ORDER"
    assert decision.reason == "max_position_pct exceeded"


def test_risk_rejects_drawdown_limit() -> None:
    inventory = Inventory(cash=800.0, equity=800.0)
    risk = RiskEngine(config=RiskConfig(max_drawdown_pct=10.0))

    decision = risk.validate_order(inventory=inventory, order_value=100.0, peak_equity=1_000.0)

    assert not decision.approved
    assert decision.reason == "max_drawdown_pct exceeded"
