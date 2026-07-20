"""Signal interface shared by every indicator."""
from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass


class Decision(enum.Enum):
    """What a signal is telling the bot to do this tick."""

    LONG = "long"    # bullish -> long bot may buy YES
    SHORT = "short"  # bearish -> short bot may buy NO
    FLAT = "flat"    # no edge -> do nothing / stay out

    @classmethod
    def parse(cls, value: str) -> "Decision":
        return cls(str(value).strip().lower())


@dataclass
class SignalContext:
    """Everything a signal needs to make a call, passed in each tick."""

    market_name: str
    yes_price: float | None   # current YES mid price (0..1), None if unavailable
    no_price: float | None    # current NO mid price (0..1)


class Signal(ABC):
    """Base class for all signals. Implement `evaluate`."""

    @abstractmethod
    def evaluate(self, ctx: SignalContext) -> Decision:
        """Return LONG / SHORT / FLAT for the given market snapshot."""

    @property
    def name(self) -> str:
        return self.__class__.__name__
