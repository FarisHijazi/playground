"""Main loop - one async task per market plus a news poller."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os

import httpx
from dotenv import load_dotenv

from hermes.alerts import fire_alert
from hermes.news import poll_news
from hermes.snapshot import diff, fetch_snapshot
from hermes.whales import detect_whale_moves

load_dotenv()
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
log = logging.getLogger("hermes")

DEFAULT_MARKETS = [
    "will-trump-win-the-2024-us-presidential-election",  # placeholder; override via env
]

TICK = int(os.environ.get("HERMES_TICK_SEC", "180"))
NEWS_TICK = int(os.environ.get("HERMES_NEWS_TICK_SEC", "60"))


async def monitor(slug: str, state: dict, client: httpx.AsyncClient) -> None:
    while True:
        try:
            curr = await fetch_snapshot(client, slug)
            log.info(
                "[%s] yes=%.3f spread=%.3f bid=%.0f ask=%.0f vol24h=%.0f",
                slug,
                curr.yes_price,
                curr.spread,
                curr.bid_size,
                curr.ask_size,
                curr.volume_24h,
            )
            prev = state.get("last")
            if prev:
                d = diff(prev, curr)
                if abs(d["imbalance"]) > 0.6:
                    await fire_alert(
                        "alignment",
                        {
                            "slug": slug,
                            "layers": ["orderbook"],
                            "direction": "YES" if d["imbalance"] > 0 else "NO",
                            "edge": d["imbalance"],
                        },
                    )

            whale_sig = await detect_whale_moves(
                client,
                state.setdefault("whales", {}),
                slug,
            )
            for s in whale_sig:
                await fire_alert("whale_move", s)

            state["last"] = curr
        except Exception as e:  # keep the loop alive
            log.exception("[%s] monitor error: %s", slug, e)

        await asyncio.sleep(TICK)


async def news_loop(client: httpx.AsyncClient) -> None:
    seen: set[str] = set()
    while True:
        try:
            hits = await poll_news(seen)
            for h in hits:
                for m in h["markets"]:
                    await fire_alert(
                        "news_lag",
                        {"market": m, "title": h["title"], "link": h["link"]},
                    )
        except Exception as e:
            log.exception("news loop error: %s", e)
        await asyncio.sleep(NEWS_TICK)


def _markets_from_env() -> list[str]:
    raw = os.environ.get("HERMES_MARKETS")
    if raw:
        return [s.strip() for s in raw.split(",") if s.strip()]
    return DEFAULT_MARKETS


async def run(markets: list[str], once: bool = False) -> None:
    async with httpx.AsyncClient(timeout=15) as client:
        if once:
            for slug in markets:
                try:
                    snap = await fetch_snapshot(client, slug)
                    log.info(
                        "[%s] yes=%.3f spread=%.3f bid=%.0f ask=%.0f vol24h=%.0f",
                        slug,
                        snap.yes_price,
                        snap.spread,
                        snap.bid_size,
                        snap.ask_size,
                        snap.volume_24h,
                    )
                except Exception as e:
                    log.exception("[%s] one-shot fetch failed: %s", slug, e)
            return

        states: dict[str, dict] = {slug: {} for slug in markets}
        await asyncio.gather(
            *[monitor(slug, states[slug], client) for slug in markets],
            news_loop(client),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Hermes Polymarket monitor")
    parser.add_argument(
        "--once",
        action="store_true",
        help="fetch one snapshot per market and exit (smoke test)",
    )
    parser.add_argument(
        "--markets",
        help="comma-separated market slugs; overrides HERMES_MARKETS env",
    )
    args = parser.parse_args()

    markets = (
        [s.strip() for s in args.markets.split(",") if s.strip()]
        if args.markets
        else _markets_from_env()
    )
    if not markets:
        raise SystemExit("no markets configured. Set HERMES_MARKETS or pass --markets.")

    asyncio.run(run(markets, once=args.once))


if __name__ == "__main__":
    main()
