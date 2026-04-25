"""Layer 03 - news-to-price lag watcher."""

from __future__ import annotations

import asyncio
import time

import feedparser

FEEDS: list[str] = [
    "https://feeds.reuters.com/reuters/topNews",
    "https://www.whitehouse.gov/feed/",
    "https://www.federalreserve.gov/feeds/press_all.xml",
]

# keyword tuple -> list of market slugs the headline likely affects
TAGS: dict[tuple[str, ...], list[str]] = {
    ("iran", "tehran"): ["iran-strike-2026", "iran-nuclear-deal"],
    ("fed", "powell", "fomc"): ["fed-rate-cut-may", "fed-hike-2026"],
    ("ceasefire",): ["peace-agreement-0422"],
}


def match_markets(headline: str) -> list[str]:
    h = headline.lower()
    hits: set[str] = set()
    for keys, markets in TAGS.items():
        if any(k in h for k in keys):
            hits.update(markets)
    return list(hits)


def _parse_feed(url: str):
    return feedparser.parse(url)


async def poll_news(seen: set[str]) -> list[dict]:
    fresh: list[dict] = []
    for url in FEEDS:
        try:
            feed = await asyncio.to_thread(_parse_feed, url)
        except Exception:
            continue
        for entry in feed.entries[:20]:
            entry_id = getattr(entry, "id", None) or getattr(entry, "link", None)
            if not entry_id or entry_id in seen:
                continue
            seen.add(entry_id)
            markets = match_markets(getattr(entry, "title", ""))
            if markets:
                fresh.append(
                    {
                        "ts": time.time(),
                        "title": entry.title,
                        "link": getattr(entry, "link", ""),
                        "markets": markets,
                    }
                )
    return fresh
