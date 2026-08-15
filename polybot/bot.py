"""The bot engine: one loop, two bots per market (long + short).

Each tick, for every configured market:
  1. Read current YES/NO prices.
  2. Ask the market's signal for a Decision (LONG / SHORT / FLAT).
  3. If the LONG bot is enabled AND decision == LONG  -> buy YES.
     If the SHORT bot is enabled AND decision == SHORT -> buy NO.

"Enabled" is the runtime on/off switch (polybot.control), which defaults to the
`enabled` value in config.yaml but can be flipped live via the CLI.
"""
from __future__ import annotations

import logging
import signal as _signal
import time
from dataclasses import dataclass, field

from . import control
from .clob import ClobClient
from .config import Config, MarketConfig, Secrets
from .signals import Decision, Signal, SignalContext, build_signal

log = logging.getLogger("polybot.bot")


@dataclass
class _MarketRuntime:
    cfg: MarketConfig
    signal: Signal
    # simple local position memory so we don't re-buy the same side every tick,
    # and so we know how many shares to sell when closing.
    long_open: bool = False
    short_open: bool = False
    long_shares: float = 0.0
    short_shares: float = 0.0


@dataclass
class Bot:
    config: Config
    secrets: Secrets
    clob: ClobClient
    _markets: list[_MarketRuntime] = field(default_factory=list)
    _stop: bool = False
    _orders_today: int = 0

    def __post_init__(self) -> None:
        for m in self.config.markets:
            self._markets.append(
                _MarketRuntime(cfg=m, signal=build_signal(m.signal.type, m.signal.params))
            )

    @classmethod
    def from_files(cls) -> "Bot":
        cfg = Config.load()
        secrets = Secrets.from_env()
        return cls(config=cfg, secrets=secrets, clob=ClobClient(secrets))

    # -- main loop ---------------------------------------------------------
    def run(self) -> None:
        mode = "DRY-RUN (paper)" if self.secrets.dry_run else "LIVE (real money)"
        log.info("Starting Polybot — mode=%s, %d market(s)", mode, len(self._markets))
        if not self.secrets.dry_run:
            log.warning("LIVE TRADING is ON. Real orders will be placed.")

        self._install_signal_handlers()
        while not self._stop:
            try:
                self.tick()
            except Exception as exc:  # noqa: BLE001 - keep the loop alive
                log.exception("tick failed: %s", exc)
            self._sleep(self.config.poll_interval_seconds)
        log.info("Polybot stopped.")

    def tick(self) -> None:
        for rt in self._markets:
            self._tick_market(rt)

    def _tick_market(self, rt: _MarketRuntime) -> None:
        cfg = rt.cfg
        yes_price = self.clob.get_midpoint(cfg.yes_token_id)
        no_price = self.clob.get_midpoint(cfg.no_token_id)
        ctx = SignalContext(market_name=cfg.name, yes_price=yes_price, no_price=no_price)
        decision = rt.signal.evaluate(ctx)

        long_on = control.is_enabled(cfg.name, "long", cfg.long.enabled)
        short_on = control.is_enabled(cfg.name, "short", cfg.short.enabled)

        log.info(
            "[%s] yes=%s no=%s signal=%s long=%s short=%s",
            cfg.name,
            _fmt(yes_price),
            _fmt(no_price),
            decision.value,
            "on" if long_on else "off",
            "on" if short_on else "off",
        )

        # --- LONG side: enter on LONG, exit (sell YES) when signal leaves LONG ---
        if long_on and decision == Decision.LONG and not rt.long_open:
            shares = self._enter(cfg.yes_token_id, yes_price, cfg.long)
            if shares > 0:
                rt.long_open = True
                rt.long_shares = shares
        elif rt.long_open and decision != Decision.LONG:
            if self._exit(cfg.yes_token_id, yes_price, rt.long_shares):
                rt.long_open = False
                rt.long_shares = 0.0

        # --- SHORT side: enter on SHORT, exit (sell NO) when signal leaves SHORT ---
        if short_on and decision == Decision.SHORT and not rt.short_open:
            shares = self._enter(cfg.no_token_id, no_price, cfg.short)
            if shares > 0:
                rt.short_open = True
                rt.short_shares = shares
        elif rt.short_open and decision != Decision.SHORT:
            if self._exit(cfg.no_token_id, no_price, rt.short_shares):
                rt.short_open = False
                rt.short_shares = 0.0

    def _enter(self, token_id: str, price: float | None, side_cfg) -> float:
        """Open a position. Returns shares bought (0.0 if nothing happened)."""
        if price is None:
            log.warning("no price for %s; skipping entry", token_id)
            return 0.0
        if price > side_cfg.max_price:
            log.info("price %.3f > max_price %.3f; skipping entry", price, side_cfg.max_price)
            return 0.0
        if self._orders_today >= self.config.risk.max_daily_orders:
            log.warning("daily order cap (%d) reached; skipping", self.config.risk.max_daily_orders)
            return 0.0

        size_shares = side_cfg.order_size_usd / price  # USDC / price = shares
        result = self.clob.buy(token_id, price, size_shares)
        if result.success:
            self._orders_today += 1
            return size_shares
        return 0.0

    def _exit(self, token_id: str, price: float | None, shares: float) -> bool:
        """Close a position by selling `shares`. Returns True if it closed."""
        if shares <= 0:
            return True  # nothing to sell; treat as closed
        if price is None:
            log.warning("no price for %s; cannot exit yet", token_id)
            return False
        log.info("signal flipped; closing position in %s", token_id)
        result = self.clob.sell(token_id, price, shares)
        if result.success:
            self._orders_today += 1
        return result.success

    # -- lifecycle ---------------------------------------------------------
    def stop(self) -> None:
        self._stop = True

    def _install_signal_handlers(self) -> None:
        def _handler(signum, _frame):  # noqa: ANN001
            log.info("received signal %s; shutting down", signum)
            self._stop = True

        try:
            _signal.signal(_signal.SIGINT, _handler)
            _signal.signal(_signal.SIGTERM, _handler)
        except ValueError:
            pass  # not in main thread (e.g. tests)

    def _sleep(self, seconds: float) -> None:
        # sleep in small slices so Ctrl-C / stop is responsive
        end = seconds
        step = 0.5
        elapsed = 0.0
        while elapsed < end and not self._stop:
            time.sleep(min(step, end - elapsed))
            elapsed += step


def _fmt(x: float | None) -> str:
    return f"{x:.3f}" if isinstance(x, (int, float)) else "n/a"
