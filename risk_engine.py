"""
Risk Engine — mandatory, runs before every order.
Spec: REJECT_ORDER if any limit is violated.

Tracked limits:
  max_position_pct    — max % of capital in any single bin
  max_capital_per_bin — max USDT per bin
  max_daily_loss_pct  — max % loss in one session
  max_drawdown_pct    — max total drawdown before halt
  max_leverage        — futures only (Phase 1)
"""
from dataclasses import dataclass


@dataclass
class RiskConfig:
    max_position_pct: float = 20.0      # % of total capital per bin
    max_capital_per_bin: float = 2000.0 # absolute USDT cap per bin
    max_daily_loss_pct: float = 5.0     # % of starting capital
    max_drawdown_pct: float = 15.0      # % from peak equity
    max_leverage: float = 1.0           # 1x = spot, >1 = futures


@dataclass
class RejectionReason:
    rule: str
    detail: str

    def __str__(self):
        return f"REJECT [{self.rule}]: {self.detail}"


class RiskEngine:
    """
    Stateless checker — call check_buy() or check_sell() before any order.
    Returns None on pass, RejectionReason on block.
    """

    def __init__(self, config: RiskConfig | None = None):
        self.config = config or RiskConfig()
        self._session_start_equity: float | None = None
        self._violations: list[RejectionReason] = []

    def set_session_start(self, equity: float):
        self._session_start_equity = equity

    # ------------------------------------------------------------------
    # Order checks
    # ------------------------------------------------------------------

    def check_buy(
        self,
        usdt_amount: float,
        total_capital: float,
        current_equity: float,
        peak_equity: float,
        bin_current_allocation: float = 0.0,
    ) -> RejectionReason | None:
        cfg = self.config

        # 1. Max position per bin (% of total capital)
        new_bin_total = bin_current_allocation + usdt_amount
        if new_bin_total > total_capital * (cfg.max_position_pct / 100):
            return RejectionReason(
                rule="max_position_pct",
                detail=(
                    f"Bin would hold ${new_bin_total:,.0f} "
                    f"({new_bin_total/total_capital*100:.1f}% > {cfg.max_position_pct}%)"
                ),
            )

        # 2. Hard cap per bin
        if new_bin_total > cfg.max_capital_per_bin:
            return RejectionReason(
                rule="max_capital_per_bin",
                detail=(
                    f"Bin total ${new_bin_total:,.0f} > "
                    f"cap ${cfg.max_capital_per_bin:,.0f}"
                ),
            )

        # 3. Daily loss limit
        if self._session_start_equity:
            session_loss_pct = (
                (self._session_start_equity - current_equity)
                / self._session_start_equity * 100
            )
            if session_loss_pct >= cfg.max_daily_loss_pct:
                return RejectionReason(
                    rule="max_daily_loss_pct",
                    detail=(
                        f"Session loss {session_loss_pct:.1f}% >= "
                        f"limit {cfg.max_daily_loss_pct}%"
                    ),
                )

        # 4. Max drawdown halt
        if peak_equity > 0:
            drawdown_pct = (peak_equity - current_equity) / peak_equity * 100
            if drawdown_pct >= cfg.max_drawdown_pct:
                return RejectionReason(
                    rule="max_drawdown_pct",
                    detail=(
                        f"Drawdown {drawdown_pct:.1f}% >= "
                        f"limit {cfg.max_drawdown_pct}%"
                    ),
                )

        return None  # PASS

    def check_sell(
        self,
        qty: float,
        available_qty: float,
    ) -> RejectionReason | None:
        if qty > available_qty + 1e-8:
            return RejectionReason(
                rule="insufficient_inventory",
                detail=f"Requested {qty:.6f} > available {available_qty:.6f}",
            )
        return None

    def violations(self) -> list[RejectionReason]:
        return list(self._violations)

    def log_rejection(self, reason: RejectionReason):
        self._violations.append(reason)

    def reset_session(self, equity: float):
        self._session_start_equity = equity
        self._violations.clear()
