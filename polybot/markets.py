"""Discover live Polymarket markets and their YES/NO token ids.

Uses Polymarket's public Gamma API (no key required) so you can find the
`yes_token_id` / `no_token_id` values that go into config.yaml.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import requests

log = logging.getLogger("polybot.markets")

GAMMA_API = "https://gamma-api.polymarket.com/markets"


@dataclass
class Market:
    question: str
    slug: str
    yes_token_id: str
    no_token_id: str
    outcomes: list[str]
    volume: float
    active: bool
    closed: bool

    def config_block(self) -> str:
        """A ready-to-paste config.yaml market entry."""
        return (
            f'  - name: "{self.slug}"\n'
            f'    yes_token_id: "{self.yes_token_id}"\n'
            f'    no_token_id: "{self.no_token_id}"\n'
            f"    long:  {{ enabled: false, order_size_usd: 5.0, max_price: 0.95 }}\n"
            f"    short: {{ enabled: false, order_size_usd: 5.0, max_price: 0.95 }}\n"
            f"    signal:\n"
            f'      type: "moving_average"\n'
            f"      params: {{ fast: 5, slow: 20 }}"
        )


def _parse(raw: dict) -> Market | None:
    """Turn one Gamma API market dict into a Market, or None if unusable."""
    token_ids = raw.get("clobTokenIds")
    if isinstance(token_ids, str):
        try:
            token_ids = json.loads(token_ids)
        except json.JSONDecodeError:
            token_ids = []
    if not token_ids or len(token_ids) < 2:
        return None  # not a standard binary YES/NO market

    outcomes = raw.get("outcomes")
    if isinstance(outcomes, str):
        try:
            outcomes = json.loads(outcomes)
        except json.JSONDecodeError:
            outcomes = ["Yes", "No"]

    try:
        volume = float(raw.get("volumeNum") or raw.get("volume") or 0)
    except (TypeError, ValueError):
        volume = 0.0

    return Market(
        question=raw.get("question", "(no title)"),
        slug=raw.get("slug", "unknown"),
        yes_token_id=str(token_ids[0]),
        no_token_id=str(token_ids[1]),
        outcomes=outcomes or ["Yes", "No"],
        volume=volume,
        active=bool(raw.get("active", False)),
        closed=bool(raw.get("closed", True)),
    )


def list_markets(query: str | None = None, limit: int = 20) -> list[Market]:
    """Fetch open, active markets, optionally filtered by a text query.

    Sorted by 24h/total volume (most liquid first) so the top results are the
    ones actually worth trading.
    """
    params = {
        "closed": "false",
        "active": "true",
        "limit": max(limit * 5, 100),  # over-fetch, we filter + trim locally
        "order": "volume",
        "ascending": "false",
    }
    resp = requests.get(GAMMA_API, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    markets: list[Market] = []
    for raw in data:
        m = _parse(raw)
        if m is None or m.closed or not m.active:
            continue
        if query and query.lower() not in m.question.lower():
            continue
        markets.append(m)

    markets.sort(key=lambda m: m.volume, reverse=True)
    return markets[:limit]
