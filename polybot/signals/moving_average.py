"""Example momentum indicator: fast vs. slow moving-average crossover.

This is a *demonstration* of how an indicator drives the long/short bots — not
financial advice or a tuned strategy. Replace it (or add alongside it) with
your real indicator; the interface is the only thing that matters.

Each tick we record the latest YES price. Once we have enough samples:
    fast MA > slow MA   -> upward momentum -> LONG  (buy YES)
    fast MA < slow MA   -> downward momentum -> SHORT (buy NO)
    otherwise / warming up -> FLAT
"""
from __future__ import annotations

from collections import deque

from .base import Decision, Signal, SignalContext


class MovingAverageSignal(Signal):
    def __init__(self, fast: int = 5, slow: int = 20):
        if fast >= slow:
            raise ValueError("`fast` window must be smaller than `slow` window")
        self.fast = int(fast)
        self.slow = int(slow)
        self._prices: deque[float] = deque(maxlen=self.slow)

    def _ma(self, window: int) -> float:
        pts = list(self._prices)[-window:]
        return sum(pts) / len(pts)

    def evaluate(self, ctx: SignalContext) -> Decision:
        if ctx.yes_price is None:
            return Decision.FLAT
        self._prices.append(ctx.yes_price)

        # Warm-up: need a full slow window before trusting the crossover.
        if len(self._prices) < self.slow:
            return Decision.FLAT

        fast_ma = self._ma(self.fast)
        slow_ma = self._ma(self.slow)
        if fast_ma > slow_ma:
            return Decision.LONG
        if fast_ma < slow_ma:
            return Decision.SHORT
        return Decision.FLAT
