"""Momentum (rate-of-change) indicator.

Compares the current YES price to its price `lookback` samples ago:
  - up more than `threshold` (fraction) -> LONG
  - down more than `threshold`          -> SHORT
  - otherwise                           -> FLAT

`threshold` is a fraction of price, e.g. 0.02 = 2% move required to act.
"""
from __future__ import annotations

from collections import deque

from .base import Decision, Signal, SignalContext


class MomentumSignal(Signal):
    def __init__(self, lookback: int = 10, threshold: float = 0.02):
        if lookback < 1:
            raise ValueError("lookback must be >= 1")
        if threshold < 0:
            raise ValueError("threshold must be >= 0")
        self.lookback = int(lookback)
        self.threshold = float(threshold)
        self._prices: deque[float] = deque(maxlen=self.lookback + 1)

    def evaluate(self, ctx: SignalContext) -> Decision:
        if ctx.yes_price is None:
            return Decision.FLAT
        self._prices.append(ctx.yes_price)
        if len(self._prices) < self.lookback + 1:
            return Decision.FLAT

        past = self._prices[0]
        now = self._prices[-1]
        if past <= 0:
            return Decision.FLAT
        change = (now - past) / past
        if change > self.threshold:
            return Decision.LONG
        if change < -self.threshold:
            return Decision.SHORT
        return Decision.FLAT
