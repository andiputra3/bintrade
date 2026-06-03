"""
Trailing Engine — locks profit as market reverses.
Modes: PERCENT | BIN | HYBRID (default) | PARTIAL

PERCENT:  exit when price <= peak × (1 - trail_pct)
BIN:      exit when price drops > trail_bin bins from peak
HYBRID:   either PERCENT or BIN trigger fires → exit
PARTIAL:  staged exits at configurable trigger levels
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TrailingMode(str, Enum):
    PERCENT = "PERCENT"
    BIN     = "BIN"
    HYBRID  = "HYBRID"
    PARTIAL = "PARTIAL"


@dataclass
class PartialLevel:
    """One trigger level for PARTIAL trailing."""
    trigger_pct: float          # drop % from peak to trigger
    sell_pct: float             # % of inventory to sell
    triggered: bool = False


@dataclass
class TrailingState:
    """Tracks the trailing stop position for an open position."""
    highest_price: float = 0.0
    highest_bin: int = 0
    trailing_price: float = 0.0
    trailing_bin: int = 0
    active: bool = False
    armed: bool = False

    def reset(self):
        self.highest_price = 0.0
        self.highest_bin = 0
        self.trailing_price = 0.0
        self.trailing_bin = 0
        self.active = False
        self.armed = False


@dataclass
class TrailingConfig:
    mode: TrailingMode = TrailingMode.HYBRID
    trail_peak_pct: float = 1.5             # PERCENT / HYBRID param
    trail_peak_bin: int = 2                 # BIN / HYBRID param
    arm_after_pct: float = 0.5             # arm after price rises this % from entry
    partial_levels: list[PartialLevel] = field(default_factory=lambda: [
        PartialLevel(trigger_pct=1.0, sell_pct=25.0),
        PartialLevel(trigger_pct=2.0, sell_pct=25.0),
        PartialLevel(trigger_pct=3.5, sell_pct=50.0),
    ])


class TrailingEngine:
    """
    Stateful trailing stop engine.
    Call update() every candle, it returns actions to execute.
    """

    def __init__(self, config: TrailingConfig | None = None):
        self.config = config or TrailingConfig()
        self.state = TrailingState()
        self._entry_price: float = 0.0
        self._partial_levels: list[PartialLevel] = []

    # ------------------------------------------------------------------
    # Position lifecycle
    # ------------------------------------------------------------------

    def open_position(self, entry_price: float, entry_bin: int):
        """Call when inventory is first acquired (or averaged)."""
        self._entry_price = entry_price
        self.state.highest_price = entry_price
        self.state.highest_bin = entry_bin
        self.state.trailing_price = entry_price * (1 - self.config.trail_peak_pct / 100)
        self.state.trailing_bin = entry_bin - self.config.trail_peak_bin
        self.state.active = True
        self.state.armed = False
        # Reset partial levels
        self._partial_levels = [
            PartialLevel(l.trigger_pct, l.sell_pct)
            for l in self.config.partial_levels
        ]

    def close_position(self):
        self.state.reset()
        self._entry_price = 0.0

    # ------------------------------------------------------------------
    # Update — call once per candle close
    # ------------------------------------------------------------------

    def update(self, current_price: float, current_bin: int) -> list[dict]:
        """
        Returns a list of actions to execute:
          [{"action": "TRAILING_STOP"|"TRAILING_TP"|"TRAILING_ARMED"|"PEAK_UPDATE",
            "sell_pct": float, "reason": str}]
        Empty list = no action.
        """
        if not self.state.active:
            return []

        actions = []
        cfg = self.config

        # --- Arm the trailing stop once price rises enough ---
        if not self.state.armed:
            if current_price >= self._entry_price * (1 + cfg.arm_after_pct / 100):
                self.state.armed = True
                actions.append({
                    "action": "TRAILING_ARMED",
                    "sell_pct": 0.0,
                    "reason": f"Armed at ${current_price:,.0f}",
                })

        # --- Update peak ---
        if current_price > self.state.highest_price:
            self.state.highest_price = current_price
            self.state.highest_bin = current_bin
            # Recalculate trailing levels
            self.state.trailing_price = (
                self.state.highest_price * (1 - cfg.trail_peak_pct / 100)
            )
            self.state.trailing_bin = (
                self.state.highest_bin - cfg.trail_peak_bin
            )
            actions.append({
                "action": "PEAK_UPDATE",
                "sell_pct": 0.0,
                "reason": (
                    f"New peak ${self.state.highest_price:,.0f} | "
                    f"trail=${self.state.trailing_price:,.0f}"
                ),
            })

        if not self.state.armed:
            return actions

        # --- Check exit conditions (only after armed) ---
        if cfg.mode == TrailingMode.PERCENT:
            if current_price <= self.state.trailing_price:
                actions.append(self._exit_action(current_price, "PERCENT"))

        elif cfg.mode == TrailingMode.BIN:
            if current_bin <= self.state.trailing_bin:
                actions.append(self._exit_action(current_price, "BIN"))

        elif cfg.mode == TrailingMode.HYBRID:
            percent_hit = current_price <= self.state.trailing_price
            bin_hit = current_bin <= self.state.trailing_bin
            if percent_hit or bin_hit:
                reason = "HYBRID-PERCENT" if percent_hit else "HYBRID-BIN"
                actions.append(self._exit_action(current_price, reason))

        elif cfg.mode == TrailingMode.PARTIAL:
            for level in self._partial_levels:
                if level.triggered:
                    continue
                drop_pct = (self.state.highest_price - current_price) / self.state.highest_price * 100
                if drop_pct >= level.trigger_pct:
                    level.triggered = True
                    actions.append({
                        "action": "TRAILING_TP",
                        "sell_pct": level.sell_pct,
                        "reason": (
                            f"PARTIAL -{drop_pct:.1f}% from peak → sell {level.sell_pct:.0f}%"
                        ),
                    })

        return actions

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _exit_action(self, price: float, reason: str) -> dict:
        return {
            "action": "TRAILING_STOP",
            "sell_pct": 100.0,
            "reason": (
                f"{reason} exit @${price:,.0f} "
                f"(peak=${self.state.highest_price:,.0f} "
                f"trail=${self.state.trailing_price:,.0f})"
            ),
        }

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def snapshot(self) -> dict:
        return {
            "mode": self.config.mode.value,
            "active": self.state.active,
            "armed": self.state.armed,
            "highest_price": self.state.highest_price,
            "trailing_price": self.state.trailing_price,
            "highest_bin": self.state.highest_bin,
            "trailing_bin": self.state.trailing_bin,
        }
