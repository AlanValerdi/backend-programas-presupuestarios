import logging

import httpx

from app.core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_NOTIFICATIONS_ENABLED

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


def is_telegram_enabled() -> bool:
    return TELEGRAM_NOTIFICATIONS_ENABLED and bool(TELEGRAM_BOT_TOKEN)


def send_message(chat_id: str, text: str, *, parse_mode: str | None = None) -> bool:
    if not is_telegram_enabled():
        logger.debug("Telegram notifications disabled or bot token missing")
        return False

    url = f"{TELEGRAM_API_BASE}/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload: dict = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
        return True
    except Exception as error:
        logger.error("Failed to send Telegram message to chat %s: %s", chat_id, error)
        return False
