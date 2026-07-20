"""Polybot command-line interface.

    python -m polybot.cli generate-wallet     # make a fresh key (writes to .env)
    python -m polybot.cli status              # show config + on/off state + mode
    python -m polybot.cli on   <market> both  # turn a bot ON  (long/short/both)
    python -m polybot.cli off  <market> both  # turn a bot OFF
    python -m polybot.cli kill                # emergency: turn EVERYTHING off
    python -m polybot.cli run                 # start the trading loop
"""
from __future__ import annotations

import logging

import click

from . import control, wallet
from .bot import Bot
from .config import Config, Secrets

SIDES = ("long", "short", "both")


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Debug logging.")
def cli(verbose: bool) -> None:
    """Polybot — a toggleable Polymarket long/short trading bot."""
    _setup_logging(verbose)


@cli.command("generate-wallet")
@click.option("--write/--no-write", default=True, help="Write the key into .env (git-ignored).")
def generate_wallet(write: bool) -> None:
    """Create a brand-new wallet key. FUND the printed address before trading."""
    w = wallet.generate()
    click.echo("")
    click.secho("  New wallet created", fg="green", bold=True)
    click.echo(f"  Address     : {w.address}")
    click.secho(f"  Private key : {w.private_key}", fg="yellow")
    click.echo("")
    click.secho(
        "  ^ SAVE THE PRIVATE KEY SOMEWHERE SAFE AND NEVER SHARE IT.\n"
        "    Anyone with this key controls the wallet's funds.",
        fg="red",
        bold=True,
    )
    if write:
        path = wallet.write_key_to_env(w.private_key)
        click.echo(f"\n  Written to {path} (git-ignored). Ready to use.")
    click.echo(
        "\n  Next: send USDC (on Polygon) to the address above to fund trading,"
        "\n  then edit config.yaml with the market you want to trade."
    )


@cli.command()
def status() -> None:
    """Show the mode, wallet, and each bot's on/off state."""
    secrets = Secrets.from_env()
    mode = "DRY-RUN (paper, no real orders)" if secrets.dry_run else "LIVE (real money!)"
    click.echo(f"Mode           : {mode}")
    if secrets.private_key:
        addr = wallet.address_for_key(secrets.private_key)
        click.echo(f"Wallet address : {addr}")
    else:
        click.secho("Wallet address : (no key set — run generate-wallet)", fg="yellow")

    try:
        cfg = Config.load()
    except FileNotFoundError as exc:
        click.secho(f"\n{exc}", fg="yellow")
        return

    click.echo(f"Poll interval  : {cfg.poll_interval_seconds}s")
    click.echo("\nBots:")
    for m in cfg.markets:
        long_on = control.is_enabled(m.name, "long", m.long.enabled)
        short_on = control.is_enabled(m.name, "short", m.short.enabled)
        click.echo(f"  {m.name}  (signal: {m.signal.type})")
        click.echo(f"      long  : {_onoff(long_on)}   size ${m.long.order_size_usd}")
        click.echo(f"      short : {_onoff(short_on)}   size ${m.short.order_size_usd}")


@cli.command()
@click.argument("market")
@click.argument("side", type=click.Choice(SIDES))
def on(market: str, side: str) -> None:
    """Turn a bot ON for MARKET. SIDE is long, short, or both."""
    _toggle(market, side, True)


@cli.command()
@click.argument("market")
@click.argument("side", type=click.Choice(SIDES))
def off(market: str, side: str) -> None:
    """Turn a bot OFF for MARKET. SIDE is long, short, or both."""
    _toggle(market, side, False)


@cli.command()
def kill() -> None:
    """EMERGENCY STOP: turn every bot off immediately."""
    control.kill_switch()
    click.secho("All bots turned OFF.", fg="red", bold=True)


@cli.command()
def run() -> None:
    """Start the trading loop (Ctrl-C to stop)."""
    bot = Bot.from_files()
    bot.run()


def _toggle(market: str, side: str, enabled: bool) -> None:
    sides = ("long", "short") if side == "both" else (side,)
    for s in sides:
        control.set_enabled(market, s, enabled)
    word = "ON" if enabled else "OFF"
    click.secho(f"{market}:{side} -> {word}", fg="green" if enabled else "yellow")


def _onoff(v: bool) -> str:
    return "ON " if v else "off"


if __name__ == "__main__":
    cli()
