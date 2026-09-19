# Deploying Robin Hood V2 (Polybot engine)

Two pieces, deployed separately:

| Piece | What it is | Where it goes |
|---|---|---|
| **Site** (`site/`) | The landing page — one static HTML file, no build step | **Vercel** (or Netlify / GitHub Pages) |
| **Bot** (`polybot/`) | The trading loop — a Python worker, no web server | **Railway** (or any Docker host) |

**No database is needed.** There is no Supabase/Postgres in this stack — the
bot keeps its on/off switches in a local `runtime_state.json` file.

---

## 1. Site → Vercel (~2 minutes)

1. Go to [vercel.com/new](https://vercel.com/new) → **Import** this GitHub repo.
2. Framework preset: **Other**. Leave everything default — `vercel.json` in the
   repo root already points the deployment at the `site/` folder with no build
   step.
3. Deploy. Done. Add your custom domain under Project → Settings → Domains.

Nothing else is required: no env vars, no build command, no install command.

## 2. Bot → Railway (~5 minutes)

1. Go to [railway.app](https://railway.app) → **New Project → Deploy from
   GitHub repo** → pick this repo.
2. Railway reads `railway.toml` automatically (start command:
   `python -m polybot.cli run`).
3. Add **Variables** on the service:

   | Variable | Value | Required |
   |---|---|---|
   | `POLYBOT_PRIVATE_KEY` | your wallet's private key | ✅ for live, optional for paper |
   | `POLYBOT_DRY_RUN` | `true` (paper) → flip to `false` to go live | ✅ start with `true` |
   | `POLYBOT_FUNDER_ADDRESS` | Polymarket proxy/deposit wallet, if you use one | only if applicable |
   | `POLYBOT_SIGNATURE_TYPE` | `0` EOA / `1` Magic / `2` Metamask proxy | defaults to `0` |
   | `POLYBOT_CONFIG` | alternate config path | defaults to `config.yaml` |

4. Edit `config.yaml` (committed in the repo, holds **no secrets**) with the
   market you want: run `python -m polybot.cli list-markets --config-for <slug>`
   locally and paste the block in. Push — Railway redeploys.
5. Watch the logs. In dry-run you'll see `[DRY-RUN] would place: ...` lines.

> **Note:** Railway's ephemeral filesystem resets `runtime_state.json` on
> redeploy, so bot on/off toggles reset to the `enabled:` values in
> `config.yaml`. Set those to what you want as the boot state.

Docker alternative (any host):

```bash
docker build -t polybot .
docker run -e POLYBOT_PRIVATE_KEY=... -e POLYBOT_DRY_RUN=true polybot
```

## 3. Going live — the money checklist

Nothing trades real money until **all** of these are true:

- [ ] `POLYBOT_DRY_RUN=false` is set (deliberately, by you)
- [ ] The wallet holds **USDC on Polygon** (that's what Polymarket trades in)
- [ ] The wallet holds a little **POL** for gas (a few dollars' worth)
- [ ] `config.yaml` has real `yes_token_id`/`no_token_id` values and sane
      `order_size_usd` / `max_price` / risk limits
- [ ] You watched a full dry-run session and the `would place:` lines look right

## 4. What is NOT needed

- ❌ Supabase / any database
- ❌ Redis / queues
- ❌ A paid API key — Polymarket's CLOB + Gamma APIs are keyless (auth is your
  wallet signature)
- ❌ A server for the site — it's static
