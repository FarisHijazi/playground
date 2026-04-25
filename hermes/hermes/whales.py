"""Layer 02 - on-chain whale tracker.

The single biggest quality driver of the whole bot is the whale list.
Curate it from data-api.polymarket.com/leaderboards: keep wallets with
>=50 resolved markets and >=65% accuracy. Rebuild weekly.
"""

from __future__ import annotations

import httpx

DATA = "https://data-api.polymarket.com"

# Replace these with real curated addresses. Stub entries kept here so the
# bot ships with a working shape; they will simply produce zero signals.
WHALES: dict[str, dict] = {
    # "0x7f3e000000000000000000000000000000000ae1c": {
    #     "win_rate": 0.81, "tag": "geopolitics-specialist",
    # },
}


async def get_positions(client: httpx.AsyncClient, address: str) -> list:
    resp = await client.get(f"{DATA}/positions", params={"user": address})
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, list) else data.get("positions", [])


async def detect_whale_moves(
    client: httpx.AsyncClient,
    prev_state: dict,
    market_slug: str,
    *,
    min_size_usd: float = 500.0,
) -> list[dict]:
    signals: list[dict] = []
    for addr, meta in WHALES.items():
        try:
            positions = await get_positions(client, addr)
        except httpx.HTTPError:
            continue
        curr = {p.get("market", p.get("slug")): float(p.get("size", 0)) for p in positions}
        prev = prev_state.get(addr, {})

        curr_size = curr.get(market_slug, 0.0)
        prev_size = prev.get(market_slug, 0.0)
        delta = curr_size - prev_size

        if abs(delta) >= min_size_usd:
            conviction = meta["win_rate"] * min(abs(delta) / 10_000, 1)
            signals.append(
                {
                    "wallet": addr,
                    "win_rate": meta["win_rate"],
                    "tag": meta["tag"],
                    "action": "ADD" if delta > 0 else "TRIM",
                    "size_usd": delta,
                    "conviction": conviction,
                }
            )
        prev_state[addr] = curr

    signals.sort(key=lambda s: -s["conviction"])
    return signals
