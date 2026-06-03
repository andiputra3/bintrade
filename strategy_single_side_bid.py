"""
Strategy 1: SINGLE SIDE BID
Accumulates inventory as price falls through bins.
Larger position the further price drops from center.
"""
from .event_engine import EventEngine, EventType
from .bin_model import BinGrid, BinState
from .inventory_model import InventoryModel
from .risk_engine import RiskEngine
from .distribution import DistributionMode, compute_allocations


class SingleSideBid:
    """
    Places bids at each lower bin according to the distribution curve.
    When price ENTERS a bid bin → BUY.
    Tracks which bins have been filled to avoid double-buying.
    """

    def __init__(
        self,
        num_bins: int = 10,
        mode: DistributionMode = DistributionMode.METEORA,
        capital_pct: float = 0.8,       # use 80% of capital for bids
    ):
        self.num_bins = num_bins
        self.mode = mode
        self.capital_pct = capital_pct
        self._last_bin: int | None = None

    def initialize(
        self,
        grid: BinGrid,
        inventory: InventoryModel,
        current_price: float,
    ):
        """Set up initial allocations on the bin grid."""
        allocs = compute_allocations(
            total_capital=inventory.initial_capital,
            num_bins=self.num_bins,
            mode=self.mode,
            capital_pct=self.capital_pct,
        )
        grid.set_allocations(allocs)

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
        """
        Called once per candle. Detects ENTER_BIN and executes BUY.
        """
        # Detect bin transition
        if self._last_bin is not None and current_bin != self._last_bin:
            # Emit EXIT_BIN for previous bin
            events.emit(
                EventType.EXIT_BIN,
                candle_idx, timestamp, current_price,
                self._last_bin,
                note=f"→ BIN{current_bin:+d}",
            )
            # Emit ENTER_BIN for new bin
            events.emit(
                EventType.ENTER_BIN,
                candle_idx, timestamp, current_price,
                current_bin,
            )

        self._last_bin = current_bin

        # Only buy if we are entering a LOWER bin (price falling)
        if current_bin >= 0:
            return  # Only bid below current price

        bin_state = grid.get_or_create_bin(current_bin)

        # Skip if already holding in this bin
        if bin_state.inventory > 0:
            return

        # Skip if no allocation set
        if bin_state.allocation <= 0:
            return

        usdt_to_spend = min(bin_state.allocation, inventory.cash)
        if usdt_to_spend < 1.0:
            return  # Too small to bother

        # Risk check
        rejection = risk.check_buy(
            usdt_amount=usdt_to_spend,
            total_capital=inventory.initial_capital,
            current_equity=inventory.equity(current_price),
            peak_equity=inventory.initial_capital,  # simplified for now
            bin_current_allocation=bin_state.allocation,
        )
        if rejection:
            risk.log_rejection(rejection)
            return

        # Execute buy
        actual_cost = inventory.buy(usdt_to_spend / current_price, current_price)
        qty = actual_cost / current_price

        bin_state.inventory += qty
        bin_state.entry_price = current_price
        bin_state.status = "hold"
        bin_state.hit_count += 1
        bin_state.last_event = "BUY"

        events.emit(
            EventType.BUY,
            candle_idx, timestamp, current_price,
            current_bin,
            qty=qty,
            usdt_value=actual_cost,
            note=f"SingleSideBid alloc=${bin_state.allocation:.0f}",
        )
