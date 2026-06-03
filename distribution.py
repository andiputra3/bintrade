"""
Distribution Engine — allocates capital across bins.
Modes: LINEAR, EXPONENTIAL, METEORA (default)
Returns: dict {bin_id: usdt_amount}
"""
from enum import Enum
from typing import Dict


class DistributionMode(str, Enum):
    LINEAR      = "LINEAR"
    EXPONENTIAL = "EXPONENTIAL"
    METEORA     = "METEORA"


# METEORA reference weights (from spec)
_METEORA_WEIGHTS = [10, 12, 15, 20, 28, 40, 55, 75, 100, 145, 180, 220, 270, 320, 380]


def compute_allocations(
    total_capital: float,
    num_bins: int,
    mode: DistributionMode = DistributionMode.METEORA,
    capital_pct: float = 1.0,   # fraction of capital to deploy (0-1)
) -> Dict[int, float]:
    """
    Returns {bin_id: usdt_allocation} for bins -1 to -num_bins.
    Bin -1 is closest to current price (smallest allocation).
    Bin -N is furthest (largest allocation) — buys more as price falls.

    Args:
        total_capital: total USDT
        num_bins: how many bins below current price to deploy into
        mode: distribution curve shape
        capital_pct: fraction of capital to use (default 100%)
    """
    deployable = total_capital * capital_pct
    weights = _get_weights(num_bins, mode)

    total_weight = sum(weights)
    allocations: Dict[int, float] = {}

    for i, w in enumerate(weights):
        bin_id = -(i + 1)           # BIN -1, -2, -3 ...
        allocations[bin_id] = round(deployable * w / total_weight, 4)

    return allocations


def _get_weights(num_bins: int, mode: DistributionMode) -> list[float]:
    if mode == DistributionMode.LINEAR:
        # 10, 20, 30, ... 10*n
        return [10 * (i + 1) for i in range(num_bins)]

    elif mode == DistributionMode.EXPONENTIAL:
        # 10, 20, 40, 80, 160 ...
        weights = [10.0]
        for _ in range(num_bins - 1):
            weights.append(weights[-1] * 2)
        return weights

    else:  # METEORA (default)
        if num_bins <= len(_METEORA_WEIGHTS):
            return _METEORA_WEIGHTS[:num_bins]
        # extend with exponential growth beyond known weights
        extended = list(_METEORA_WEIGHTS)
        last = extended[-1]
        while len(extended) < num_bins:
            last = round(last * 1.4)
            extended.append(last)
        return extended[:num_bins]


def allocation_table(
    total_capital: float,
    num_bins: int,
    mode: DistributionMode = DistributionMode.METEORA,
    capital_pct: float = 1.0,
) -> str:
    """Pretty-print the allocation table (for debugging / dashboard)."""
    allocs = compute_allocations(total_capital, num_bins, mode, capital_pct)
    lines = [
        f"{'Mode':<14} {mode.value}",
        f"{'Capital':<14} ${total_capital:,.0f}",
        f"{'Deploy':<14} ${total_capital * capital_pct:,.0f} ({capital_pct*100:.0f}%)",
        f"{'Bins':<14} {num_bins}",
        "",
        f"  {'BIN':>5}  {'USDT':>10}  {'PCT':>6}  {'BAR'}",
        "  " + "-" * 45,
    ]
    deployed = sum(allocs.values())
    for bin_id in sorted(allocs):
        amt = allocs[bin_id]
        pct = amt / deployed * 100
        bar = "█" * int(pct / 2)
        lines.append(f"  BIN {bin_id:>3}  ${amt:>9,.0f}  {pct:>5.1f}%  {bar}")
    return "\n".join(lines)
