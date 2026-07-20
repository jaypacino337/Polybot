"""Pluggable trading signals.

A signal looks at market data and returns a Decision: LONG, SHORT, or FLAT.
The bot maps LONG -> buy YES (long bot), SHORT -> buy NO (short bot).

To add your own indicator (the "FSVO" indicator you mentioned), subclass
`Signal`, implement `evaluate`, and register it in `build_signal` below.
"""
from __future__ import annotations

from typing import Any

from .base import Decision, Signal, SignalContext
from .manual import ManualSignal
from .moving_average import MovingAverageSignal

_REGISTRY: dict[str, type[Signal]] = {
    "manual": ManualSignal,
    "moving_average": MovingAverageSignal,
}


def build_signal(signal_type: str, params: dict[str, Any] | None = None) -> Signal:
    params = params or {}
    try:
        cls = _REGISTRY[signal_type]
    except KeyError as exc:
        raise ValueError(
            f"Unknown signal type '{signal_type}'. "
            f"Available: {', '.join(sorted(_REGISTRY))}"
        ) from exc
    return cls(**params)


def register_signal(name: str, cls: type[Signal]) -> None:
    """Register a custom signal class under `name` so config can reference it."""
    _REGISTRY[name] = cls


__all__ = [
    "Decision",
    "Signal",
    "SignalContext",
    "ManualSignal",
    "MovingAverageSignal",
    "build_signal",
    "register_signal",
]
