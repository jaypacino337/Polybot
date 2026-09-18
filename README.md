# Polybot — a toggleable Polymarket trading bot

> 🌐 **Website:** a landing page for the project lives in [`site/index.html`](site/index.html) —
> a single self-contained file (no build step). Open it locally in a browser, or serve the
> `site/` folder with GitHub Pages (Settings → Pages → deploy from branch, `/site` folder).

A small, safe-by-default bot that can automatically place orders on
[Polymarket](https://polymarket.com) from a wallet you control. It has a
**long bot** (buys the YES outcome) and a **short bot** (buys the NO outcome),
and you can turn each one **on and off** independently. A pluggable **signal**
system decides when to trade — today it ships with a demo moving-average
indicator, and it's built so you can drop in your own indicator later to flip
the bots on and off automatically.

> **Safety first:** the bot starts in **DRY-RUN (paper) mode**. It runs, logs
> exactly what it *would* do, and places **no real orders** until you
> deliberately switch to live trading. Nothing can spend real money until you
> set `POLYBOT_DRY_RUN=false` **and** fund the wallet.

---

## 🔑 About your private key — read this first

**Never paste your private key into a chat, email, issue, or commit.** Anyone
who has it controls your money.

This bot is designed so you're the only one who ever handles the key:

- You generate (or import) the key **locally** with the command below.
- It's stored in a file called `.env`, which is **git-ignored** — it never gets
  committed or pushed.
- The bot reads the key only from that local file, at runtime.

---

## Quick start

### 1. Install

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create your config files

```bash
cp .env.example .env               # secrets (git-ignored)
cp config.yaml.example config.yaml # your strategy / markets
```

### 3. Make a wallet (or use your own)

Generate a fresh wallet — this writes the key into your local `.env`:

```bash
python -m polybot.cli generate-wallet
```

It prints an **address** and a **private key**. Save the private key somewhere
safe (a password manager). Then **send USDC on the Polygon network** to that
address to fund trading.

Already have a wallet? Skip the command and just paste your key into `.env` as
`POLYBOT_PRIVATE_KEY=...`.

### 4. Pick a market to trade

Edit `config.yaml` and fill in the `yes_token_id` / `no_token_id` for the market
you want (see **Finding a market** below), plus how much to trade.

### 5. Check everything

```bash
python -m polybot.cli status
```

You'll see the mode (DRY-RUN vs LIVE), your wallet address, and each bot's
on/off state.

### 6. Turn bots on and run

```bash
python -m polybot.cli on  example-market both   # turn long + short ON
python -m polybot.cli run                         # start the loop (Ctrl-C to stop)
```

Watch the logs. Because you're in dry-run, you'll see lines like
`[DRY-RUN] would place: BUY ... ` — real prices, no real orders.

When you're happy and the wallet is funded, set `POLYBOT_DRY_RUN=false` in
`.env` and run again to trade for real.

---

## Turning it on and off

The whole point: flip bots without editing code.

```bash
python -m polybot.cli on   example-market long    # long bot ON
python -m polybot.cli off  example-market long    # long bot OFF
python -m polybot.cli on   example-market short   # short bot ON
python -m polybot.cli on   example-market both    # both ON
python -m polybot.cli kill                          # EMERGENCY: everything OFF
```

These flags are read live by a running bot (they're stored in
`runtime_state.json`), so you can toggle from a second terminal — no restart
needed. `kill` is your panic button.

---

## The signal system (your future "indicator")

Each market has a **signal** that returns `LONG`, `SHORT`, or `FLAT` every tick:

- `LONG`  → the long bot (if enabled) buys **YES**
- `SHORT` → the short bot (if enabled) buys **NO**
- `FLAT`  → do nothing

When the signal flips **away** from a side, the bot **closes** that position
(sells the shares it bought) — so the long and short bots both enter *and* exit
automatically. Turning a bot off stops new entries.

Built-in signals (set `signal.type` in `config.yaml`):

| type             | params                                   | what it does                                             |
|------------------|------------------------------------------|----------------------------------------------------------|
| `manual`         | `decision: long/short/flat`              | you drive it. Great for testing.                         |
| `threshold`      | `lower`, `upper` (0..1)                   | YES price above `upper` → LONG, below `lower` → SHORT.   |
| `moving_average` | `fast`, `slow` (windows)                 | fast MA vs slow MA crossover (trend following).          |
| `momentum`       | `lookback`, `threshold` (fraction)       | price up >threshold → LONG, down → SHORT.                |
| `rsi`            | `period`, `oversold`, `overbought`, `mode` | RSI mean-reversion (default) or momentum.              |

Example — trade the RSI indicator:

```yaml
signal:
  type: rsi
  params: { period: 14, oversold: 30, overbought: 70, mode: reversion }
```

**Adding your own indicator** is the intended path — this is where your
"FSVO"/custom indicator goes. Create a class in `polybot/signals/`, implement
`evaluate(ctx) -> Decision`, and register it:

```python
# polybot/signals/my_indicator.py
from .base import Decision, Signal, SignalContext

class MyIndicator(Signal):
    def __init__(self, threshold=0.6):
        self.threshold = threshold

    def evaluate(self, ctx: SignalContext) -> Decision:
        if ctx.yes_price is None:
            return Decision.FLAT
        return Decision.LONG if ctx.yes_price > self.threshold else Decision.SHORT
```

```python
# register it in polybot/signals/__init__.py
from .my_indicator import MyIndicator
register_signal("my_indicator", MyIndicator)
```

```yaml
# then use it in config.yaml
signal:
  type: my_indicator
  params: { threshold: 0.65 }
```

`SignalContext` currently gives you live YES/NO prices. Tell me what your
indicator needs (order-book depth, external data feed, time-series history) and
I'll wire that into the context.

---

## Finding a market (token ids)

Polymarket markets are identified by two ERC-1155 **token ids** — one for YES,
one for NO. The bot has a built-in finder so you don't have to hunt them down:

```bash
# List the most-traded open markets (optionally filter by text)
python -m polybot.cli list-markets
python -m polybot.cli list-markets -q "election" -n 10

# Print a ready-to-paste config block for one market (use its slug)
python -m polybot.cli list-markets --config-for will-it-rain-tomorrow
```

The `--config-for` output drops straight under `markets:` in `config.yaml` with
the correct `yes_token_id` / `no_token_id` already filled in — no manual copying
of raw ids.

> Uses Polymarket's public Gamma API (no key needed). If your network blocks it,
> the same data is at `https://gamma-api.polymarket.com/markets`.

---

## How it works

```
config.yaml ──► Config ──┐
.env (secrets) ─► Secrets ─► ClobClient (Polymarket)
                          │        ▲
runtime_state.json ─► control      │ prices / orders
                          │        │
                          ▼        │
                    Bot loop ── every N seconds:
                      1. read YES/NO prices
                      2. signal.evaluate() -> LONG/SHORT/FLAT
                      3. if bot enabled & decision matches -> place BUY
```

- `polybot/config.py`  — loads `.env` (secrets) + `config.yaml` (strategy)
- `polybot/wallet.py`  — generate keys / derive address (never commits keys)
- `polybot/clob.py`    — wrapper over Polymarket's CLOB client (dry-run aware)
- `polybot/signals/`   — pluggable indicators (LONG/SHORT/FLAT)
- `polybot/control.py` — the on/off switches (persisted)
- `polybot/bot.py`     — the trading loop
- `polybot/cli.py`     — the commands you run

---

## Testing

```bash
pip install pytest
python -m pytest
```

The tests run fully offline with a fake exchange — no keys, no network, no
orders.

---

## ⚠️ Disclaimers

- Trading is risky; prediction markets can go to 0. **Only trade what you can
  afford to lose.** Start in dry-run.
- The `moving_average` signal is a **demo**, not a profitable strategy.
- Check that automated trading and Polymarket are permitted in your
  jurisdiction.
- This software is provided as-is, with no warranty.
