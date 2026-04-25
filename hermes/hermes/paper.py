"""Paper-trading simulator.

Tracks hypothetical positions opened off Hermes signals and computes
mark-to-market PnL using the live mid price. Writes one JSON line per
event to a ledger file so the run can be summarised later.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field

log = logging.getLogger("hermes.paper")


@dataclass
class Position:
    market: str
    side: str  # "YES" or "NO"
    size_usd: float
    entry_price: float
    entry_ts: float
    hold_sec: float
    reason: str

    def fair_value_usd(self, yes_price: float) -> float:
        # 1 YES token resolves to $1 if YES wins. Current mark = size * (curr/entry).
        ref = yes_price if self.side == "YES" else (1.0 - yes_price)
        ref_entry = self.entry_price if self.side == "YES" else (1.0 - self.entry_price)
        return self.size_usd * (ref / max(ref_entry, 1e-6))


@dataclass
class PaperBook:
    starting_cash: float
    cash: float
    positions: list[Position] = field(default_factory=list)
    closed: list[dict] = field(default_factory=list)
    ledger_path: str = "/tmp/hermes_paper_ledger.jsonl"

    def _log(self, event: dict) -> None:
        event["ts"] = time.time()
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def open(
        self,
        market: str,
        side: str,
        size_usd: float,
        yes_price: float,
        hold_sec: float,
        reason: str,
    ) -> Position | None:
        if size_usd > self.cash:
            log.info("paper: insufficient cash for %s %s ($%.2f left)", market, side, self.cash)
            return None
        # avoid stacking duplicate positions on the same market+side
        if any(p.market == market and p.side == side for p in self.positions):
            return None

        pos = Position(
            market=market,
            side=side,
            size_usd=size_usd,
            entry_price=yes_price,
            entry_ts=time.time(),
            hold_sec=hold_sec,
            reason=reason,
        )
        self.cash -= size_usd
        self.positions.append(pos)
        self._log({"event": "open", **asdict(pos), "cash_after": self.cash})
        log.info(
            "paper OPEN %s %s $%.2f @ yes=%.3f (%s) cash=$%.2f",
            market, side, size_usd, yes_price, reason, self.cash,
        )
        return pos

    def expire(self, yes_price_by_market: dict[str, float]) -> None:
        now = time.time()
        still_open: list[Position] = []
        for p in self.positions:
            if now - p.entry_ts >= p.hold_sec and p.market in yes_price_by_market:
                exit_price = yes_price_by_market[p.market]
                value = p.fair_value_usd(exit_price)
                pnl = value - p.size_usd
                self.cash += value
                row = {
                    "event": "close",
                    **asdict(p),
                    "exit_price": exit_price,
                    "exit_value": value,
                    "pnl": pnl,
                    "cash_after": self.cash,
                }
                self.closed.append(row)
                self._log(row)
                log.info(
                    "paper CLOSE %s %s pnl=$%+.3f (entry %.3f -> exit %.3f) cash=$%.2f",
                    p.market, p.side, pnl, p.entry_price, exit_price, self.cash,
                )
            else:
                still_open.append(p)
        self.positions = still_open

    def equity(self, yes_price_by_market: dict[str, float]) -> float:
        marked = 0.0
        for p in self.positions:
            yp = yes_price_by_market.get(p.market, p.entry_price)
            marked += p.fair_value_usd(yp)
        return self.cash + marked

    def summary(self, yes_price_by_market: dict[str, float]) -> dict:
        equity = self.equity(yes_price_by_market)
        wins = sum(1 for c in self.closed if c["pnl"] > 0)
        return {
            "starting_cash": self.starting_cash,
            "cash": self.cash,
            "equity": equity,
            "pnl": equity - self.starting_cash,
            "open_positions": len(self.positions),
            "closed_trades": len(self.closed),
            "winners": wins,
            "win_rate": (wins / len(self.closed)) if self.closed else None,
        }


def make_book(starting_cash: float | None = None) -> PaperBook | None:
    if starting_cash is None:
        raw = os.environ.get("HERMES_PAPER_CASH")
        if not raw:
            return None
        starting_cash = float(raw)
    ledger = os.environ.get("HERMES_PAPER_LEDGER", "/tmp/hermes_paper_ledger.jsonl")
    # truncate ledger at start of run
    open(ledger, "w").close()
    book = PaperBook(starting_cash=starting_cash, cash=starting_cash, ledger_path=ledger)
    book._log({"event": "start", "starting_cash": starting_cash})
    return book
