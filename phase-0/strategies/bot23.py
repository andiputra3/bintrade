from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from models.event import EventType


class BotVariant(StrEnum):
    BOT11 = "BOT11"
    BOT22 = "BOT22"
    BOT23 = "BOT23"
    BOT35 = "BOT35"


@dataclass(frozen=True)
class BotAction:
    event_type: EventType
    sell_pct: float | None = None


@dataclass(frozen=True)
class BOT23Strategy:
    """BOT variant strategy for take-profit and buyback bin thresholds."""

    variant: BotVariant | str = BotVariant.BOT23
    sell_pct: float = 20.0

    @property
    def take_profit_bins(self) -> int:
        return self._variant_config()[0]

    @property
    def buyback_bins(self) -> int:
        return self._variant_config()[1]

    def should_take_profit(self, entry_bin: int, current_bin: int) -> bool:
        return current_bin >= entry_bin + self.take_profit_bins

    def should_buyback(self, exit_bin: int, current_bin: int) -> bool:
        return current_bin <= exit_bin - self.buyback_bins

    def generate_action(
        self,
        entry_bin: int,
        current_bin: int,
        last_sell_bin: int | None = None,
    ) -> BotAction | None:
        if last_sell_bin is not None and self.should_buyback(last_sell_bin, current_bin):
            return BotAction(event_type=EventType.BUYBACK)

        if self.should_take_profit(entry_bin, current_bin):
            return BotAction(event_type=EventType.TAKE_PROFIT, sell_pct=self.sell_pct)

        return None

    def _variant_config(self) -> tuple[int, int]:
        variant = BotVariant(self.variant)
        configs: dict[BotVariant, tuple[int, int]] = {
            BotVariant.BOT11: (1, 1),
            BotVariant.BOT22: (2, 2),
            BotVariant.BOT23: (2, 3),
            BotVariant.BOT35: (3, 5),
        }
        return configs[variant]
