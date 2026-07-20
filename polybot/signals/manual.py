"""Manual signal: you decide. Useful for testing the plumbing end-to-end.

Set `decision: long|short|flat` in config, or flip it at runtime by editing the
config and restarting, or by driving it from your own code.
"""
from __future__ import annotations

from .base import Decision, Signal, SignalContext


class ManualSignal(Signal):
    def __init__(self, decision: str = "flat"):
        self._decision = Decision.parse(decision)

    def evaluate(self, ctx: SignalContext) -> Decision:  # noqa: ARG002
        return self._decision
