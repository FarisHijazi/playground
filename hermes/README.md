# Hermes

Minimal 4-layer Polymarket monitoring bot. Reads order book, on-chain wallet
moves, news-to-price lag, and position deltas every few minutes and pings
Telegram (or stdout) when smart money moves.

Built from the spec described in
[adiix_official's playbook](https://x.com/adiix_official/status/2047218648293442010).

## Quick start

```bash
cd hermes
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env to add Telegram creds and a comma-separated HERMES_MARKETS list

# one-shot smoke test (no creds required)
python -m hermes.main --once --markets some-active-market-slug

# 24/7 monitoring loop
python -m hermes.main
```

If `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` are unset, alerts are logged to
stdout instead of being pushed to Telegram, so you can run the bot in pure
observation mode while you tune thresholds.

## Layers

1. **Order book** (`hermes/snapshot.py`) - bid/ask depth + imbalance.
2. **On-chain wallets** (`hermes/whales.py`) - position deltas of curated
   high-accuracy wallets. Drop your own list into `WHALES`.
3. **News-to-price lag** (`hermes/news.py`) - RSS poller tagged to markets.
4. **Position delta** - emerges from diffing snapshots stored in `state`.

## Deploy

A `systemd/hermes.service` unit is included. Drop the project at `/opt/hermes`,
create the venv there, drop your `.env`, then:

```bash
sudo cp systemd/hermes.service /etc/systemd/system/
sudo systemctl enable --now hermes.service
```

## Curating the whale list

The single biggest quality driver of the bot. Pull the top wallets from
`https://data-api.polymarket.com/leaderboards`, keep only those with >=50
resolved markets and >=65% accuracy, and paste them into `WHALES` in
`hermes/whales.py`. Rebuild weekly.
