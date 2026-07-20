"""Thin wrapper around Polymarket's CLOB client.

Isolates the rest of the bot from the details of `py_clob_client`, and makes the
whole thing importable/testable even when that package (or a private key) is
absent — handy for dry-run and unit tests.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from .config import Secrets

log = logging.getLogger("polybot.clob")


@dataclass
class OrderResult:
    success: bool
    order_id: Optional[str]
    dry_run: bool
    detail: str = ""


class ClobClient:
    """Wraps the Polymarket CLOB REST/signing client.

    Read-only calls (prices) work whenever the network is reachable. Order
    placement is gated by `secrets.dry_run`: in dry-run nothing is signed or
    sent — we log the intended order and return a synthetic result.
    """

    def __init__(self, secrets: Secrets):
        self.secrets = secrets
        self._client = None  # lazily built underlying py_clob_client instance

    # -- underlying client -------------------------------------------------
    def _ensure_client(self):
        if self._client is not None:
            return self._client
        try:
            from py_clob_client.client import ClobClient as _Clob
        except ImportError as exc:  # pragma: no cover - env dependent
            raise RuntimeError(
                "py-clob-client is not installed. Run: pip install -r requirements.txt"
            ) from exc

        s = self.secrets
        s.require_key()
        key = s.private_key if s.private_key.startswith("0x") else "0x" + s.private_key
        funder = s.funder_address or None

        client = _Clob(
            host=s.clob_host,
            key=key,
            chain_id=s.chain_id,
            signature_type=s.signature_type,
            funder=funder,
        )
        # L2 auth: derive (or create) API credentials from the wallet.
        client.set_api_creds(client.create_or_derive_api_creds())
        self._client = client
        log.info("CLOB client ready (host=%s chain=%s)", s.clob_host, s.chain_id)
        return client

    # -- read-only market data --------------------------------------------
    def get_midpoint(self, token_id: str) -> Optional[float]:
        """Current mid price (0..1) for an outcome token, or None on failure."""
        try:
            resp = self._ensure_client().get_midpoint(token_id)
            return float(resp["mid"]) if isinstance(resp, dict) else float(resp)
        except Exception as exc:  # noqa: BLE001 - network/format resilience
            log.warning("get_midpoint(%s) failed: %s", token_id, exc)
            return None

    def get_price(self, token_id: str, side: str) -> Optional[float]:
        """Best price for BUY/SELL of a token, or None on failure."""
        try:
            resp = self._ensure_client().get_price(token_id, side)
            return float(resp["price"]) if isinstance(resp, dict) else float(resp)
        except Exception as exc:  # noqa: BLE001
            log.warning("get_price(%s,%s) failed: %s", token_id, side, exc)
            return None

    # -- order placement ---------------------------------------------------
    def buy(self, token_id: str, price: float, size_shares: float) -> OrderResult:
        """Place a limit BUY for `size_shares` of `token_id` at `price`.

        In dry-run, logs and returns without touching the network.
        """
        intent = f"BUY {size_shares:.4f} shares of {token_id} @ {price:.3f}"
        if self.secrets.dry_run:
            log.info("[DRY-RUN] would place: %s", intent)
            return OrderResult(success=True, order_id=None, dry_run=True, detail=intent)

        try:
            from py_clob_client.clob_types import OrderArgs, OrderType
            from py_clob_client.order_builder.constants import BUY

            client = self._ensure_client()
            args = OrderArgs(
                token_id=token_id,
                price=round(float(price), 3),
                size=round(float(size_shares), 2),
                side=BUY,
            )
            signed = client.create_order(args)
            resp = client.post_order(signed, OrderType.GTC)
            oid = resp.get("orderID") or resp.get("orderId") if isinstance(resp, dict) else None
            log.info("Placed live order %s (%s)", oid, intent)
            return OrderResult(success=True, order_id=oid, dry_run=False, detail=str(resp))
        except Exception as exc:  # noqa: BLE001
            log.error("Order failed (%s): %s", intent, exc)
            return OrderResult(success=False, order_id=None, dry_run=False, detail=str(exc))

    def cancel_all(self) -> None:
        if self.secrets.dry_run:
            log.info("[DRY-RUN] would cancel all open orders")
            return
        try:
            self._ensure_client().cancel_all()
            log.info("Cancelled all open orders")
        except Exception as exc:  # noqa: BLE001
            log.error("cancel_all failed: %s", exc)
