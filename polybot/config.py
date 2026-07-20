"""Configuration loading for Polybot.

Secrets come from environment (`.env`); strategy/market config comes from
`config.yaml`. Keeping them separate means you can commit your strategy without
ever risking your private key.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Load .env once, on import. Values already in the real environment win.
load_dotenv(override=False)

DEFAULT_CONFIG_PATH = Path(os.getenv("POLYBOT_CONFIG", "config.yaml"))


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Secrets:
    """Sensitive values, sourced only from the environment / .env file."""

    private_key: str
    funder_address: str
    signature_type: int
    clob_host: str
    chain_id: int
    dry_run: bool

    @classmethod
    def from_env(cls) -> "Secrets":
        pk = (os.getenv("POLYBOT_PRIVATE_KEY") or "").strip()
        funder = (os.getenv("POLYBOT_FUNDER_ADDRESS") or "").strip()
        return cls(
            private_key=pk,
            funder_address=funder,
            signature_type=int(os.getenv("POLYBOT_SIGNATURE_TYPE", "0")),
            clob_host=os.getenv("POLYBOT_CLOB_HOST", "https://clob.polymarket.com"),
            chain_id=int(os.getenv("POLYBOT_CHAIN_ID", "137")),
            dry_run=_get_bool("POLYBOT_DRY_RUN", True),
        )

    def require_key(self) -> None:
        if not self.private_key:
            raise RuntimeError(
                "No private key configured. Set POLYBOT_PRIVATE_KEY in .env "
                "(generate one with: python -m polybot.cli generate-wallet)."
            )


@dataclass
class BotSideConfig:
    enabled: bool = False
    order_size_usd: float = 5.0
    max_price: float = 0.95


@dataclass
class SignalConfig:
    type: str = "manual"
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketConfig:
    name: str
    yes_token_id: str
    no_token_id: str
    long: BotSideConfig = field(default_factory=BotSideConfig)
    short: BotSideConfig = field(default_factory=BotSideConfig)
    signal: SignalConfig = field(default_factory=SignalConfig)


@dataclass
class RiskConfig:
    max_open_orders: int = 10
    max_daily_orders: int = 50


@dataclass
class Config:
    poll_interval_seconds: int = 30
    markets: list[MarketConfig] = field(default_factory=list)
    risk: RiskConfig = field(default_factory=RiskConfig)

    @classmethod
    def load(cls, path: Path | str = DEFAULT_CONFIG_PATH) -> "Config":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"Config file '{path}' not found. Copy config.yaml.example to "
                f"config.yaml and edit it."
            )
        data = yaml.safe_load(path.read_text()) or {}
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        markets = []
        for m in data.get("markets", []) or []:
            markets.append(
                MarketConfig(
                    name=m["name"],
                    yes_token_id=str(m["yes_token_id"]),
                    no_token_id=str(m["no_token_id"]),
                    long=_side(m.get("long")),
                    short=_side(m.get("short")),
                    signal=SignalConfig(
                        type=(m.get("signal") or {}).get("type", "manual"),
                        params=(m.get("signal") or {}).get("params", {}) or {},
                    ),
                )
            )
        risk_raw = data.get("risk", {}) or {}
        return cls(
            poll_interval_seconds=int(data.get("poll_interval_seconds", 30)),
            markets=markets,
            risk=RiskConfig(
                max_open_orders=int(risk_raw.get("max_open_orders", 10)),
                max_daily_orders=int(risk_raw.get("max_daily_orders", 50)),
            ),
        )


def _side(raw: dict[str, Any] | None) -> BotSideConfig:
    raw = raw or {}
    return BotSideConfig(
        enabled=bool(raw.get("enabled", False)),
        order_size_usd=float(raw.get("order_size_usd", 5.0)),
        max_price=float(raw.get("max_price", 0.95)),
    )
