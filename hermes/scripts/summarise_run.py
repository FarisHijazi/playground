"""Read a Hermes paper-trading ledger and print a PnL summary."""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path


def main(path: str = "/tmp/hermes_paper_ledger.jsonl") -> int:
    p = Path(path)
    if not p.exists():
        print(f"no ledger at {path}")
        return 1

    rows = [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    if not rows:
        print("ledger is empty")
        return 1

    starts = [r for r in rows if r["event"] == "start"]
    opens = [r for r in rows if r["event"] == "open"]
    closes = [r for r in rows if r["event"] == "close"]

    starting = starts[-1]["starting_cash"] if starts else 0.0

    realized_pnl = sum(c["pnl"] for c in closes)
    pnls = [c["pnl"] for c in closes]
    winners = [c for c in closes if c["pnl"] > 0]
    losers = [c for c in closes if c["pnl"] < 0]

    by_market_pnl: dict[str, float] = defaultdict(float)
    for c in closes:
        by_market_pnl[c["market"]] += c["pnl"]
    by_reason = Counter(o["reason"].split("=")[0].split("_")[0] for o in opens)

    open_capital = sum(o["size_usd"] for o in opens) - sum(c["size_usd"] for c in closes)
    last_cash = (closes[-1]["cash_after"] if closes else (opens[-1]["cash_after"] if opens else starting))

    print("=" * 64)
    print(f"Hermes paper-trading summary  ({len(rows)} ledger events)")
    print("=" * 64)
    print(f"starting cash      : ${starting:.2f}")
    print(f"trades opened      : {len(opens)}")
    print(f"trades closed      : {len(closes)}")
    print(f"still open         : {len(opens) - len(closes)} (~${open_capital:.2f} tied up)")
    print(f"realised pnl       : ${realized_pnl:+.4f}")
    if pnls:
        print(f"  best trade       : ${max(pnls):+.4f}")
        print(f"  worst trade      : ${min(pnls):+.4f}")
        print(f"  median           : ${statistics.median(pnls):+.4f}")
    if closes:
        print(f"win rate           : {len(winners)}/{len(closes)} = {len(winners)/len(closes):.0%}")
    print(f"final cash         : ${last_cash:.2f}")
    print(f"final equity (cash + open at entry) : ${last_cash + open_capital:.2f}")
    print()
    print("trades by entry reason:")
    for reason, n in by_reason.most_common():
        print(f"  {reason:12s} {n}")
    print()
    print("realised pnl by market:")
    for mkt, pnl in sorted(by_market_pnl.items(), key=lambda kv: kv[1]):
        print(f"  {pnl:+8.4f}  {mkt}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/hermes_paper_ledger.jsonl"))
