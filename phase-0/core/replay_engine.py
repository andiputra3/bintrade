from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from core.atr_engine import ATREngine
from core.bin_builder import BinBuilder
from core.event_engine import EventEngine
from core.inventory_engine import InventoryEngine
from core.metrics import Metrics, MetricsCalculator
from core.trade_log import TradeLog
from models.event import EventType
from strategies.bot23 import BOT23Strategy
from strategies.single_side_bid import SingleSideBidStrategy
from strategies.trailing import TrailingEngine


@dataclass(frozen=True)
class ReplayResult:
    trade_log: TradeLog
    metrics: Metrics


@dataclass
class ReplayEngine:
    symbol: str = "BTCUSDT"
    initial_cash: float = 10_000.0
    atr_engine: ATREngine = ATREngine()
    bin_builder: BinBuilder = BinBuilder()
    event_engine: EventEngine | None = None
    inventory_engine: InventoryEngine | None = None
    single_side_bid: SingleSideBidStrategy = SingleSideBidStrategy()
    bot23: BOT23Strategy = BOT23Strategy()
    trailing_engine: TrailingEngine | None = None
    metrics_calculator: MetricsCalculator = MetricsCalculator()

    def run_csv(self, csv_path: str | Path) -> ReplayResult:
        frame = pd.read_csv(csv_path)
        return self.run(frame)

    def run(self, candles: pd.DataFrame) -> ReplayResult:
        self._validate_candles(candles)

        event_engine = self.event_engine or EventEngine()
        inventory_engine = self.inventory_engine or InventoryEngine.with_cash(self.initial_cash)
        trailing_engine = self.trailing_engine or TrailingEngine()
        trade_log = TradeLog()

        reference_price = float(candles.iloc[0]["close"])
        entry_bin: int | None = None
        last_sell_bin: int | None = None

        for index, candle in candles.iterrows():
            current_slice = candles.iloc[: index + 1]
            atr = self.atr_engine.calculate(current_slice).iloc[-1]
            timestamp = pd.to_datetime(candle["timestamp"]).to_pydatetime()
            price = float(candle["close"])

            if pd.isna(atr):
                inventory_engine.mark_to_market(price)
                continue

            current_bin = self.bin_builder.locate_bin(price=price, reference_price=reference_price, atr=float(atr))
            generated_events = event_engine.on_bin(current_bin, price=price, timestamp=timestamp)
            bin_id = current_bin.bin_id if current_bin is not None else None

            for event in generated_events:
                trade_log.append(
                    timestamp=timestamp,
                    price=price,
                    bin_id=event.bin_index,
                    event_type=event.type,
                    action="NONE",
                    qty=0.0,
                    inventory=inventory_engine.inventory,
                )

            if bin_id is not None and bin_id < 0:
                allocation = self.single_side_bid.get_allocation_for_bin(bin_id)
                if allocation > 0 and inventory_engine.inventory.cash >= allocation:
                    buy_event = event_engine.emit_trade_event(
                        event_type=EventType.BUY,
                        price=price,
                        timestamp=timestamp,
                        metadata={"strategy": "single_side_bid", "allocation": allocation},
                    )
                    qty = allocation / price
                    inventory_engine.buy(symbol=self.symbol, qty=qty, price=price, timestamp=timestamp)
                    entry_bin = bin_id if entry_bin is None else entry_bin
                    trailing_engine.update_peak(price=price, bin_id=bin_id)
                    trade_log.append(
                        timestamp=timestamp,
                        price=price,
                        bin_id=bin_id,
                        event_type=buy_event.type,
                        action="BUY",
                        qty=qty,
                        inventory=inventory_engine.inventory,
                    )

            if entry_bin is not None and bin_id is not None and inventory_engine.inventory.inventory_qty > 0:
                bot_action = self.bot23.generate_action(
                    entry_bin=entry_bin,
                    current_bin=bin_id,
                    last_sell_bin=last_sell_bin,
                )
                if bot_action is not None:
                    action_event = event_engine.emit_trade_event(
                        event_type=bot_action.event_type,
                        price=price,
                        timestamp=timestamp,
                        metadata={"strategy": "bot23"},
                    )
                    if bot_action.event_type is EventType.TAKE_PROFIT:
                        qty = inventory_engine.inventory.inventory_qty * ((bot_action.sell_pct or 0.0) / 100)
                        if qty > 0:
                            inventory_engine.sell(symbol=self.symbol, qty=qty, price=price, timestamp=timestamp)
                            last_sell_bin = bin_id
                            trade_log.append(
                                timestamp=timestamp,
                                price=price,
                                bin_id=bin_id,
                                event_type=action_event.type,
                                action="SELL",
                                qty=qty,
                                inventory=inventory_engine.inventory,
                            )
                    elif bot_action.event_type is EventType.BUYBACK:
                        allocation = min(20.0, inventory_engine.inventory.cash)
                        if allocation > 0:
                            qty = allocation / price
                            inventory_engine.buyback(symbol=self.symbol, qty=qty, price=price, timestamp=timestamp)
                            trade_log.append(
                                timestamp=timestamp,
                                price=price,
                                bin_id=bin_id,
                                event_type=action_event.type,
                                action="BUYBACK",
                                qty=qty,
                                inventory=inventory_engine.inventory,
                            )
                            last_sell_bin = None

            if bin_id is not None:
                exit_event = trailing_engine.generate_exit_event(
                    event_engine=event_engine,
                    price=price,
                    bin_id=bin_id,
                )
                if exit_event is not None and inventory_engine.inventory.inventory_qty > 0:
                    qty = inventory_engine.inventory.inventory_qty
                    inventory_engine.sell(symbol=self.symbol, qty=qty, price=price, timestamp=timestamp)
                    trade_log.append(
                        timestamp=timestamp,
                        price=price,
                        bin_id=bin_id,
                        event_type=exit_event.type,
                        action="SELL",
                        qty=qty,
                        inventory=inventory_engine.inventory,
                    )
                    entry_bin = None
                    last_sell_bin = bin_id
                trailing_engine.update_peak(price=price, bin_id=bin_id)

            inventory_engine.mark_to_market(price)

        metrics = self.metrics_calculator.calculate(trade_log)
        return ReplayResult(trade_log=trade_log, metrics=metrics)

    @staticmethod
    def _validate_candles(candles: pd.DataFrame) -> None:
        required_columns = {"timestamp", "open", "high", "low", "close"}
        missing_columns = required_columns.difference(candles.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSV missing required columns: {missing}")
        if candles.empty:
            raise ValueError("candles cannot be empty")
