"""RSI (Relative Strength Index) — a classic momentum/mean-reversion indicator.

RSI measures the speed of recent price moves on a 0..100 scale:
  - RSI <= oversold  (default 30) -> price fell hard, likely to bounce -> LONG
  - RSI >= overbought(default 70) -> price rose hard, likely to fade  -> SHORT
  - in between -> FLAT

This is the mean-reversion reading (buy dips, sell rips). If you'd rather trade
momentum (LONG when strong, SHORT when weak), set `mode: "momentum"`.
"""
from __future__ import annotations

from collections import deque

from .base import Decision, Signal, SignalContext


class RSISignal(Signal):
    def __init__(self, period: int = 14, oversold: float = 30.0,
                 overbought: float = 70.0, mode: str = "reversion"):
        if period < 2:
            raise ValueError("RSI period must be >= 2")
        if not 0 < oversold < overbought < 100:
            raise ValueError("need 0 < oversold < overbought < 100")
        if mode not in ("reversion", "momentum"):
            raise ValueError("mode must be 'reversion' or 'momentum'")
        self.period = int(period)
        self.oversold = float(oversold)
        self.overbought = float(overbought)
        self.mode = mode
        # keep period+1 prices so we have `period` deltas
        self._prices: deque[float] = deque(maxlen=self.period + 1)

    def _rsi(self) -> float | None:
        if len(self._prices) < self.period + 1:
            return None
        prices = list(self._prices)
        gains, losses = 0.0, 0.0
        for prev, cur in zip(prices, prices[1:]):
            change = cur - prev
            if change >= 0:
                gains += change
            else:
                losses -= change
        avg_gain = gains / self.period
        avg_loss = losses / self.period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def evaluate(self, ctx: SignalContext) -> Decision:
        if ctx.yes_price is None:
            return Decision.FLAT
        self._prices.append(ctx.yes_price)
        rsi = self._rsi()
        if rsi is None:  # still warming up
            return Decision.FLAT

        if rsi <= self.oversold:
            return Decision.LONG if self.mode == "reversion" else Decision.SHORT
        if rsi >= self.overbought:
            return Decision.SHORT if self.mode == "reversion" else Decision.LONG
        return Decision.FLAT
