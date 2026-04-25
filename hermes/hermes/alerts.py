"""Alert sink. Falls back to stdout when no Telegram credentials are set."""

from __future__ import annotations

import logging
import os

log = logging.getLogger("hermes.alerts")

_token = os.environ.get("TELEGRAM_BOT_TOKEN")
_chat = os.environ.get("TELEGRAM_CHAT_ID")
_bot = None
if _token and _chat:
    try:
        from telegram import Bot

        _bot = Bot(token=_token)
    except Exception as e:  # missing optional dep
        log.warning("telegram bot disabled: %s", e)
        _bot = None


def _format(kind: str, payload: dict) -> str | None:
    if kind == "whale_move":
        return (
            f"🐋 {payload['tag'].upper()}\n"
            f"wallet: {payload['wallet'][:8]}...\n"
            f"win rate: {payload['win_rate']:.0%}\n"
            f"action: {payload['action']} ${payload['size_usd']:,.0f}\n"
            f"conviction: {payload['conviction']:.2f}"
        )
    if kind == "news_lag":
        return (
            f"📰 NEWS → {payload['market']}\n"
            f"{payload['title']}\n"
            f"market hasn't repriced yet.\n"
            f"{payload['link']}"
        )
    if kind == "alignment":
        return (
            f"⚡ ALIGNMENT\n"
            f"market: {payload['slug']}\n"
            f"layers: {payload['layers']}\n"
            f"direction: {payload['direction']}\n"
            f"edge: {payload['edge']:.2f}"
        )
    return None


async def fire_alert(kind: str, payload: dict) -> None:
    msg = _format(kind, payload)
    if msg is None:
        return
    if _bot is not None:
        try:
            await _bot.send_message(chat_id=_chat, text=msg)
            return
        except Exception as e:
            log.warning("telegram send failed, falling back to log: %s", e)
    log.info("ALERT[%s]\n%s", kind, msg)
