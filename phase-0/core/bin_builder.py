from __future__ import annotations

from dataclasses import dataclass

from models.bin import Bin


@dataclass(frozen=True)
class BinBuilder:
    """Build dynamic ATR bins centered around a reference price."""

    atr_multiplier: float = 1.0
    min_bin: int = -20
    max_bin: int = 20

    def __post_init__(self) -> None:
        if self.atr_multiplier <= 0:
            raise ValueError("atr_multiplier must be greater than zero")
        if self.min_bin >= self.max_bin:
            raise ValueError("min_bin must be less than max_bin")

    def build_bins(self, reference_price: float, atr: float) -> list[Bin]:
        """Build bins from ``min_bin`` to ``max_bin`` using ATR step size."""
        self._validate_inputs(reference_price, atr)
        step = atr * self.atr_multiplier

        return [
            Bin(
                index=index,
                lower_price=reference_price + (index * step),
                upper_price=reference_price + ((index + 1) * step),
                atr=atr,
                atr_multiplier=self.atr_multiplier,
                reference_price=reference_price,
            )
            for index in range(self.min_bin, self.max_bin + 1)
        ]

    def locate_bin(self, price: float, reference_price: float, atr: float) -> Bin | None:
        """Return the bin containing ``price``, or ``None`` outside configured range."""
        self._validate_inputs(reference_price, atr)
        step = atr * self.atr_multiplier
        raw_index = int((price - reference_price) // step)

        if raw_index < self.min_bin or raw_index > self.max_bin:
            return None

        return Bin(
            index=raw_index,
            lower_price=reference_price + (raw_index * step),
            upper_price=reference_price + ((raw_index + 1) * step),
            atr=atr,
            atr_multiplier=self.atr_multiplier,
            reference_price=reference_price,
        )

    @staticmethod
    def _validate_inputs(reference_price: float, atr: float) -> None:
        if reference_price <= 0:
            raise ValueError("reference_price must be greater than zero")
        if atr <= 0:
            raise ValueError("atr must be greater than zero")
