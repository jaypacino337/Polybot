"""Runtime on/off switches, persisted to a small git-ignored JSON file.

This is what makes the bot "turn on and off": the CLI writes flags here, and the
running loop reads them every tick. You can flip a bot from a second terminal
(or a cron job, or later your indicator) without restarting the process.

Keys are per market+side, e.g. "example-market:long".
"""
from __future__ import annotations

import json
from pathlib import Path

STATE_PATH = Path("runtime_state.json")


def _load() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def _key(market: str, side: str) -> str:
    return f"{market}:{side}"


def set_enabled(market: str, side: str, enabled: bool) -> None:
    state = _load()
    state[_key(market, side)] = bool(enabled)
    _save(state)


def is_enabled(market: str, side: str, default: bool = False) -> bool:
    """Runtime flag wins; falls back to `default` (usually the config value)."""
    return bool(_load().get(_key(market, side), default))


def all_flags() -> dict:
    return _load()


def kill_switch() -> None:
    """Turn EVERYTHING off at once."""
    state = _load()
    for k in list(state):
        state[k] = False
    _save(state)
