from __future__ import annotations

from dataclasses import dataclass

from core.trade_log import TradeLog, TradeLogEntry


@dataclass(frozen=True)
class Metrics:
    total_pnl: float
    equity: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    trade_count: int
    buy_count: int
    sell_count: int
    buyback_count: int
    tp_count: int
    trailing_exit_count: int


class MetricsCalculator:
    def calculate(self, trade_log: TradeLog) -> Metrics:
        entries = trade_log.entries
        if not entries:
            return Metrics(
                total_pnl=0.0,
                equity=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                trade_count=0,
                buy_count=0,
                sell_count=0,
                buyback_count=0,
                tp_count=0,
                trailing_exit_count=0,
            )

        trade_entries = [entry for entry in entries if entry.action in {"BUY", "SELL", "BUYBACK"}]
        sell_entries = [entry for entry in trade_entries if entry.action == "SELL"]
        realized_deltas = self._realized_pnl_deltas(sell_entries)
        wins = [delta for delta in realized_deltas if delta > 0]
        losses = [abs(delta) for delta in realized_deltas if delta < 0]

        gross_profit = sum(wins)
        gross_loss = sum(losses)
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit

        return Metrics(
            total_pnl=entries[-1].realized_pnl + entries[-1].unrealized_pnl,
            equity=entries[-1].equity,
            max_drawdown=self._max_drawdown(entries),
            win_rate=(len(wins) / len(realized_deltas)) * 100 if realized_deltas else 0.0,
            profit_factor=profit_factor,
            trade_count=len(trade_entries),
            buy_count=sum(1 for entry in trade_entries if entry.action == "BUY"),
            sell_count=sum(1 for entry in trade_entries if entry.action == "SELL"),
            buyback_count=sum(1 for entry in trade_entries if entry.action == "BUYBACK"),
            tp_count=sum(1 for entry in entries if entry.event == "TAKE_PROFIT"),
            trailing_exit_count=sum(1 for entry in entries if entry.event == "TRAILING_STOP"),
        )

    @staticmethod
    def _max_drawdown(entries: list[TradeLogEntry]) -> float:
        peak = entries[0].equity
        max_drawdown = 0.0
        for entry in entries:
            peak = max(peak, entry.equity)
            if peak > 0:
                drawdown = ((peak - entry.equity) / peak) * 100
                max_drawdown = max(max_drawdown, drawdown)
        return max_drawdown

    @staticmethod
    def _realized_pnl_deltas(entries: list[TradeLogEntry]) -> list[float]:
        deltas: list[float] = []
        previous_realized = 0.0
        for entry in entries:
            delta = entry.realized_pnl - previous_realized
            if delta != 0:
                deltas.append(delta)
            previous_realized = entry.realized_pnl
        return deltas
