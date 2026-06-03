from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class DistributionMode(StrEnum):
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    METEORA = "meteora"


@dataclass(frozen=True)
class SingleSideBidStrategy:
    """Build bid allocations for bins below the current price."""

    mode: DistributionMode | str = DistributionMode.METEORA
    levels: int = 10
    base_allocation: float = 10.0
    meteora_distribution: list[float] = field(
        default_factory=lambda: [10, 15, 20, 30, 40, 55, 75, 100, 140, 200]
    )

    def build_distribution(self) -> dict[int, float]:
        mode = DistributionMode(self.mode)
        if self.levels <= 0:
            raise ValueError("levels must be greater than zero")

        if mode is DistributionMode.METEORA:
            values = self.meteora_distribution[: self.levels]
        elif mode is DistributionMode.LINEAR:
            values = [self.base_allocation * level for level in range(1, self.levels + 1)]
        elif mode is DistributionMode.EXPONENTIAL:
            values = [self.base_allocation * (2 ** (level - 1)) for level in range(1, self.levels + 1)]
        else:
            raise ValueError(f"Unsupported distribution mode: {mode}")

        return {-level: allocation for level, allocation in enumerate(values, start=1)}

    def get_allocation_for_bin(self, bin_id: int) -> float:
        return self.build_distribution().get(bin_id, 0.0)
