"""Price-threshold signal — the simplest rule there is.

Acts on the raw YES probability (0..1):
  - YES price >= `upper` -> LONG   (market thinks it's likely; ride it)
  - YES price <= `lower` -> SHORT  (market thinks it's unlikely; fade it)
  - in between            -> FLAT

Handy as a sanity-check strategy and an easy first live test.
"""
from __future__ import annotations

from .base import Decision, Signal, SignalContext


class ThresholdSignal(Signal):
    def __init__(self, lower: float = 0.35, upper: float = 0.65):
        if not 0 <= lower < upper <= 1:
            raise ValueError("need 0 <= lower < upper <= 1")
        self.lower = float(lower)
        self.upper = float(upper)

    def evaluate(self, ctx: SignalContext) -> Decision:
        if ctx.yes_price is None:
            return Decision.FLAT
        if ctx.yes_price >= self.upper:
            return Decision.LONG
        if ctx.yes_price <= self.lower:
            return Decision.SHORT
        return Decision.FLAT
