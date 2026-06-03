"""
Bin Model — BinState and BinGrid
Spec: BIN 0 = current price, BIN+1 above, BIN-1 below
      bin_size = ATR(14) × atr_multiplier
"""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class BinState:
    """Single bin state — tracks all required fields from spec."""
    bin_id: int
    lower_price: float
    upper_price: float
    allocation: float = 0.0        # USDT allocated to this bin
    inventory: float = 0.0        # BTC held in this bin
    status: str = "empty"         # empty | bid | hold | sold
    last_event: str = ""
    hit_count: int = 0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    entry_price: float = 0.0      # avg entry of current inventory

    @property
    def mid_price(self) -> float:
        return (self.lower_price + self.upper_price) / 2

    def update_unrealized(self, current_price: float):
        if self.inventory > 0 and self.entry_price > 0:
            self.unrealized_pnl = (current_price - self.entry_price) * self.inventory
        else:
            self.unrealized_pnl = 0.0

    def __repr__(self):
        inv_str = f" inv={self.inventory:.4f}" if self.inventory > 0 else ""
        return (
            f"BIN[{self.bin_id:+d}] "
            f"${self.lower_price:.0f}-${self.upper_price:.0f} "
            f"alloc=${self.allocation:.0f}{inv_str} "
            f"[{self.status}]"
        )


class BinGrid:
    """
    Dynamic bin grid centered on current price.
    Rebuilds when bin_size changes significantly (>5% drift).
    """

    def __init__(self, center_price: float, bin_size: float, num_bins: int = 10):
        self.center_price = center_price
        self.bin_size = bin_size
        self.num_bins = num_bins          # bins above and below center
        self._bins: Dict[int, BinState] = {}
        self._rebuild(center_price, bin_size)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_bin_id(self, price: float) -> int:
        """Return the bin ID that contains `price`."""
        offset = price - self.center_price
        return int(offset // self.bin_size)

    def get_bin(self, bin_id: int) -> Optional[BinState]:
        return self._bins.get(bin_id)

    def get_or_create_bin(self, bin_id: int) -> BinState:
        if bin_id not in self._bins:
            lower = self.center_price + bin_id * self.bin_size
            upper = lower + self.bin_size
            self._bins[bin_id] = BinState(
                bin_id=bin_id,
                lower_price=lower,
                upper_price=upper,
            )
        return self._bins[bin_id]

    def recenter(self, new_center: float, new_bin_size: float):
        """
        BIN_RECENTER event — called when bin_size drifts >5% or
        price moves far from center.
        Preserves inventory in existing bins.
        """
        old_bins_with_inv = {
            k: v for k, v in self._bins.items() if v.inventory > 0
        }
        self.center_price = round(new_center / new_bin_size) * new_bin_size
        self.bin_size = new_bin_size
        self._rebuild(self.center_price, new_bin_size)

        # Re-attach inventory to new bin IDs
        for old_bin in old_bins_with_inv.values():
            new_id = self.get_bin_id(old_bin.entry_price)
            new_bin = self.get_or_create_bin(new_id)
            new_bin.inventory += old_bin.inventory
            new_bin.entry_price = old_bin.entry_price
            new_bin.allocation += old_bin.allocation
            new_bin.status = "hold"
            new_bin.hit_count = old_bin.hit_count
            new_bin.realized_pnl = old_bin.realized_pnl

    def update_unrealized(self, current_price: float):
        for b in self._bins.values():
            b.update_unrealized(current_price)

    def bins_with_inventory(self) -> list[BinState]:
        return [b for b in self._bins.values() if b.inventory > 0]

    def all_bins(self) -> list[BinState]:
        return sorted(self._bins.values(), key=lambda b: b.bin_id, reverse=True)

    def set_allocations(self, allocations: Dict[int, float]):
        """Set USDT allocation per bin_id (negative = below current price)."""
        for bin_id, amount in allocations.items():
            b = self.get_or_create_bin(bin_id)
            b.allocation = amount
            if b.status == "empty" and amount > 0:
                b.status = "bid"

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _rebuild(self, center: float, bin_size: float):
        existing = dict(self._bins)
        self._bins = {}
        for i in range(-self.num_bins, self.num_bins + 1):
            lower = center + i * bin_size
            upper = lower + bin_size
            if i in existing:
                b = existing[i]
                b.lower_price = lower
                b.upper_price = upper
                self._bins[i] = b
            else:
                self._bins[i] = BinState(
                    bin_id=i,
                    lower_price=lower,
                    upper_price=upper,
                )
