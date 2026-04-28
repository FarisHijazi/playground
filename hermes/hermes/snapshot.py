"""Layer 01 - order book snapshot and diff engine."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"


@dataclass
class MarketSnapshot:
    slug: str
    ts: float
    yes_price: float
    no_price: float
    bid_size: float
    ask_size: float
    spread: float
    volume_24h: float


async def fetch_snapshot(client: httpx.AsyncClient, slug: str) -> MarketSnapshot:
    resp = await client.get(f"{GAMMA}/markets", params={"slug": slug})
    resp.raise_for_status()
    markets = resp.json()
    if not markets:
        raise LookupError(f"market {slug!r} not found on gamma-api")
    m = markets[0]

    token_ids = m.get("clobTokenIds")
    if isinstance(token_ids, str):
        # gamma sometimes returns this as a JSON-encoded string
        import json

        token_ids = json.loads(token_ids)
    if not token_ids:
        raise LookupError(f"market {slug!r} has no clobTokenIds")
    yes_token = token_ids[0]

    book_resp = await client.get(f"{CLOB}/book", params={"token_id": yes_token})
    book_resp.raise_for_status()
    book = book_resp.json()

    bids = book.get("bids") or []
    asks = book.get("asks") or []
    best_bid = float(bids[0]["price"]) if bids else 0.0
    best_ask = float(asks[0]["price"]) if asks else 1.0
    bid_sz = sum(float(b["size"]) for b in bids[:5])
    ask_sz = sum(float(a["size"]) for a in asks[:5])

    mid = (best_bid + best_ask) / 2
    return MarketSnapshot(
        slug=slug,
        ts=time.time(),
        yes_price=mid,
        no_price=1 - mid,
        bid_size=bid_sz,
        ask_size=ask_sz,
        spread=best_ask - best_bid,
        volume_24h=float(m.get("volume24hr", 0) or 0),
    )


def diff(prev: MarketSnapshot, curr: MarketSnapshot) -> dict:
    # Require both sides of the book to have meaningful size before we
    # treat (bid - ask) as an imbalance. A book with one side empty looks
    # like a +/-1.0 imbalance every tick but conveys no directional pressure.
    MIN_SIDE_SIZE = 100.0
    has_two_sided_book = (
        curr.bid_size >= MIN_SIDE_SIZE and curr.ask_size >= MIN_SIDE_SIZE
    )
    if has_two_sided_book:
        imbalance = (curr.bid_size - curr.ask_size) / (curr.bid_size + curr.ask_size)
    else:
        imbalance = 0.0
    return {
        "dt_sec": curr.ts - prev.ts,
        "price_delta": curr.yes_price - prev.yes_price,
        "price_pct": (curr.yes_price - prev.yes_price) / max(prev.yes_price, 1e-6),
        "bid_delta": curr.bid_size - prev.bid_size,
        "ask_delta": curr.ask_size - prev.ask_size,
        "imbalance": imbalance,
        "two_sided_book": has_two_sided_book,
        "vol_delta": curr.volume_24h - prev.volume_24h,
    }
