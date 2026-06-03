from __future__ import annotations

from models.event import EventType
from strategies.bot23 import BOT23Strategy


def test_bot23_take_profit_works() -> None:
    strategy = BOT23Strategy()

    assert strategy.should_take_profit(entry_bin=-1, current_bin=1)
    action = strategy.generate_action(entry_bin=-1, current_bin=1)

    assert action is not None
    assert action.event_type is EventType.TAKE_PROFIT
    assert action.sell_pct == 20.0


def test_bot23_buyback_works() -> None:
    strategy = BOT23Strategy()

    assert strategy.should_buyback(exit_bin=1, current_bin=-2)
    action = strategy.generate_action(entry_bin=-1, current_bin=-2, last_sell_bin=1)

    assert action is not None
    assert action.event_type is EventType.BUYBACK


def test_supported_bot_variants() -> None:
    assert BOT23Strategy(variant="BOT11").take_profit_bins == 1
    assert BOT23Strategy(variant="BOT22").buyback_bins == 2
    assert BOT23Strategy(variant="BOT23").buyback_bins == 3
    assert BOT23Strategy(variant="BOT35").take_profit_bins == 3
