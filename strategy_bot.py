"""
Strategy 2: BOT variants (BOT11, BOT22, BOT23, BOT35, Custom)

BOT23 default:
  TP +2 BIN  → SELL 20% of inventory
  BUYBACK -3 BIN  → re-buy if price drops 3 bins from last TP

Execution priority (from spec):
  1. Emergency Stop Loss
  2. Trailing Stop
  3. Trailing Take Profit
  4. BOT Strategy          ← this module
  5. Buyback
"""
from dataclasses import dataclass, field
from .event_engine import EventEngine, EventType
from .bin_model import BinGrid
from .inventory_model import InventoryModel
from .risk_engine import RiskEngine


@dataclass
class BotConfig:
    """Defines a BOT variant."""
    name: str = "BOT23"
    tp_bins: int = 2            # take profit every N bins UP
    buyback_bins: int = 3       # buyback if price drops N bins from last TP
    sell_pct: float = 20.0      # % of inventory to sell per TP trigger

    @classmethod
    def bot11(cls): return cls("BOT11", tp_bins=1, buyback_bins=1, sell_pct=50.0)
    @classmethod
    def bot22(cls): return cls("BOT22", tp_bins=2, buyback_bins=2, sell_pct=20.0)
    @classmethod
    def bot23(cls): return cls("BOT23", tp_bins=2, buyback_bins=3, sell_pct=20.0)
    @classmethod
    def bot35(cls): return cls("BOT35", tp_bins=3, buyback_bins=5, sell_pct=20.0)


class BotStrategy:
    """
    BOT23 (and variants).

    Tracks:
      - Each bin's entry price
      - Last TP price (to calculate buyback trigger)
      - Partial sell count per bin
    """

    def __init__(self, config: BotConfig | None = None):
        self.config = config or BotConfig.bot23()
        # {bin_id: {"entry_bin": int, "last_tp_bin": int|None, "tp_count": int}}
        self._bin_state: dict[int, dict] = {}
        self._last_tp_bin: int | None = None
        self._all_time_entry_bin: int | None = None

    # ------------------------------------------------------------------
    # Core logic — called in execution priority slot 4
    # ------------------------------------------------------------------

    def on_candle(
        self,
        candle_idx: int,
        timestamp: int,
        current_price: float,
        current_bin: int,
        grid: BinGrid,
        inventory: InventoryModel,
        risk: RiskEngine,
        events: EventEngine,
    ):
        if inventory.inventory_qty <= 0:
            return

        cfg = self.config
        avg_entry = inventory.average_entry
        if avg_entry <= 0:
            return

        # --- TAKE PROFIT check ---
        # Determine the entry bin at average_entry price
        entry_bin = grid.get_bin_id(avg_entry)
        tp_trigger_bin = entry_bin + cfg.tp_bins

        if current_bin >= tp_trigger_bin:
            # How many TP intervals have been crossed?
            intervals_up = (current_bin - entry_bin) // cfg.tp_bins
            expected_tp_count = self._bin_state.get("tp_count", 0)

            if intervals_up > expected_tp_count:
                self._bin_state["tp_count"] = intervals_up
                self._last_tp_bin = current_bin

                # Risk check (sell-side)
                qty_to_sell = inventory.inventory_qty * (cfg.sell_pct / 100)
                rejection = risk.check_sell(qty_to_sell, inventory.inventory_qty)
                if rejection:
                    risk.log_rejection(rejection)
                    return

                qty_sold, proceeds, pnl = inventory.sell_pct(cfg.sell_pct, current_price)

                # Update bin inventory
                bins_with_inv = grid.bins_with_inventory()
                if bins_with_inv:
                    # Reduce inventory proportionally from all held bins
                    total_bin_inv = sum(b.inventory for b in bins_with_inv)
                    for b in bins_with_inv:
                        share = b.inventory / total_bin_inv
                        b.inventory -= qty_sold * share
                        if b.inventory < 1e-8:
                            b.inventory = 0.0
                            b.status = "sold"
                        b.realized_pnl += pnl * share
                        b.last_event = "TAKE_PROFIT"

                events.emit(
                    EventType.TAKE_PROFIT,
                    candle_idx, timestamp, current_price,
                    current_bin,
                    qty=qty_sold,
                    usdt_value=proceeds,
                    pnl=pnl,
                    note=(
                        f"{cfg.name} TP interval {intervals_up} "
                        f"sell {cfg.sell_pct:.0f}%"
                    ),
                )
                return  # one action per candle

        # --- BUYBACK check (priority 5) ---
        if self._last_tp_bin is not None:
            buyback_trigger_bin = self._last_tp_bin - cfg.buyback_bins
            if current_bin <= buyback_trigger_bin:
                self._do_buyback(
                    candle_idx, timestamp, current_price, current_bin,
                    grid, inventory, risk, events
                )

    def _do_buyback(
        self,
        candle_idx, timestamp, current_price, current_bin,
        grid, inventory, risk, events
    ):
        """Re-buy after a price drop of `buyback_bins` from last TP."""
        # Use 10% of remaining cash as buyback size
        usdt_amount = inventory.cash * 0.10
        if usdt_amount < 1.0:
            return

        bin_state = grid.get_or_create_bin(current_bin)
        rejection = risk.check_buy(
            usdt_amount=usdt_amount,
            total_capital=inventory.initial_capital,
            current_equity=inventory.equity(current_price),
            peak_equity=inventory.initial_capital,
            bin_current_allocation=bin_state.allocation,
        )
        if rejection:
            risk.log_rejection(rejection)
            return

        qty = usdt_amount / current_price
        actual_cost = inventory.buy(qty, current_price)

        bin_state.inventory += actual_cost / current_price
        bin_state.entry_price = current_price
        bin_state.status = "hold"
        bin_state.hit_count += 1
        bin_state.last_event = "BUYBACK"

        # Reset TP tracking after buyback
        self._last_tp_bin = None
        self._bin_state["tp_count"] = 0

        events.emit(
            EventType.BUYBACK,
            candle_idx, timestamp, current_price,
            current_bin,
            qty=actual_cost / current_price,
            usdt_value=actual_cost,
            note=f"{self.config.name} buyback after -{self.config.buyback_bins} bins",
        )

    def reset(self):
        self._bin_state.clear()
        self._last_tp_bin = None
        self._all_time_entry_bin = None
