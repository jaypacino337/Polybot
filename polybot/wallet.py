"""Wallet helpers: generate a fresh key, or derive the address of an existing one.

The private key is NEVER written to the repo. `generate` prints the key and
(optionally) writes it into the git-ignored `.env` file only.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from eth_account import Account


@dataclass
class NewWallet:
    address: str
    private_key: str


def generate() -> NewWallet:
    """Create a brand-new random wallet. Fund the returned address to trade."""
    acct = Account.create()
    return NewWallet(address=acct.address, private_key=acct.key.hex())


def address_for_key(private_key: str) -> str:
    """Return the checksummed address that owns `private_key`."""
    key = private_key if private_key.startswith("0x") else "0x" + private_key
    return Account.from_key(key).address


def write_key_to_env(private_key: str, env_path: Path | str = ".env") -> Path:
    """Insert/replace POLYBOT_PRIVATE_KEY in the local .env file (git-ignored).

    Creates .env from nothing if needed. Never touches any other file.
    """
    env_path = Path(env_path)
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text().splitlines()

    key_line = f"POLYBOT_PRIVATE_KEY={private_key}"
    replaced = False
    for i, line in enumerate(lines):
        if line.strip().startswith("POLYBOT_PRIVATE_KEY="):
            lines[i] = key_line
            replaced = True
            break
    if not replaced:
        lines.append(key_line)

    env_path.write_text("\n".join(lines) + "\n")
    return env_path
