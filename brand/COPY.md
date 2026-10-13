# Robin Hood V2 — launch pack

Everything needed to launch, copy-paste ready. Assets live in this folder:
`logo.svg` (source), plus rendered PNGs: `logo-1000.png` (pump.fun coin image /
X avatar), `pfp-400.png` (small avatar), `banner-1500x500.png` (X header).

---

## Identity

| | |
|---|---|
| **Name** | Robin Hood V2 |
| **Ticker** | `$HOODV2` (alternates: `$ROBIN`, `$ARROW`) |
| **One-liner** | The people's trading bot — prediction markets on autopilot. |
| **Colors** | Forest `#123A23` / Hood green `#37C275` / Gold `#FFC93C` / Cream `#FFF7EC` |
| **Font** | Bricolage Grotesque (display), JetBrains Mono (code) |

> ⚠️ **Naming note:** "Robin Hood" here is the public-domain folk hero — two
> words, bow-and-arrow iconography. Do **not** use Robinhood Markets' feather
> logo, their green (#00C805), or the single-word "Robinhood" spelling, and
> keep the "not affiliated" line (already in the site footer) everywhere. That
> keeps the brand on the right side of their trademark.

---

## X (Twitter) bio — 133 chars

> 🏹 The people's trading bot. Open-source long/short bots for Polymarket —
> your keys, your wallet, dry-run by default. $HOODV2

**Profile setup:** avatar = `logo-1000.png`, header = `banner-1500x500.png`,
pinned link = the Vercel site URL, then pin the launch thread.

## pump.fun description

> The people's trading bot 🏹 Not just a ticker — a working product: an
> open-source engine that longs and shorts Polymarket prediction markets with
> the flip of a switch. Your keys, your wallet, your alpha. Dry-run by default
> so nobody gets wrecked by accident. Code, site, and docs are live. The suits
> had V1. This one's ours.

*(pump.fun fields: name `Robin Hood V2`, ticker `HOODV2`, image
`logo-1000.png`, website = Vercel URL, twitter = your handle, telegram =
optional.)*

## Launch tweet (thread starter)

> The suits built trading bots for hedge funds.
> We built one for everyone. 🏹
>
> Robin Hood V2 — the people's trading bot for Polymarket.
> ✅ working open-source bot, live today
> ✅ long + short with a flip of a switch
> ✅ your keys, your wallet, dry-run by default
>
> $HOODV2 · site + code below 👇

---

## Live thesis

**The market.** Prediction markets went mainstream: elections, rates, sports,
weather — Polymarket now clears billions in volume and the order books are
thin, retail-driven, and inefficient. The pros already run bots against them.
Retail mostly clicks buttons and hopes.

**The gap.** Every serious trading bot for these markets is closed-source,
paywalled, or a Discord "signal group." There is no honest, open, self-custody
tool a normal person can run.

**The product (already live).** Robin Hood V2 ships the Polybot engine — real,
working, tested code, not a promise:

- A **long bot** (buys YES) and a **short bot** (buys NO) you toggle on and off
  at runtime — from a second terminal, no restarts, with a one-command kill
  switch.
- A **pluggable signal system**: threshold, moving-average crossover, momentum,
  and RSI ship today; your own indicator is one Python class away. Bots enter
  *and* exit automatically when the signal flips.
- **Self-custody by design**: your key lives in a local git-ignored file, and
  the bot paper-trades until you deliberately flip it live.
- **Deploy in minutes**: static site on Vercel, worker on Railway or Docker —
  no database, no API keys, no middlemen.

**The token.** $HOODV2 is the community flag planted on top of that code — a
fair pump.fun launch, no presale, no team allocation games. It confers no
equity, revenue share, or promise of profit; it exists because open tools
deserve a community, and communities deserve a token that points at something
real. The code stays free either way.

**Why we win.** Most launches are a logo in search of a product. This is a
product in search of nothing — it already runs. Every improvement to the bot
is public, verifiable, and shipped in the open.

**Risks, stated plainly.** Trading is risky and prediction markets can go to
zero. The built-in signals are reference strategies, not guaranteed alpha.
$HOODV2 is a memecoin and can also go to zero. Only trade — and only ape —
what you can afford to lose. DYOR.

---

## Launch-day checklist

1. **Repo public** on GitHub (the "open source" claim must be true).
2. **Merge the PR**, then import the repo on **Vercel** → site is live (~2 min,
   zero config — `vercel.json` handles it).
3. *(Optional but strong)* **Railway** worker running in dry-run, streaming
   `[DRY-RUN] would place:` logs — screenshot it for the thread.
4. **X profile** dressed: avatar, banner, bio, site link.
5. **pump.fun create** (needs a Solana wallet with a little SOL): fill the
   fields above, launch, then immediately pin the launch thread with the site +
   GitHub links.
6. Add the pump.fun link to the site + X bio (one-line edit; ask and it ships).
