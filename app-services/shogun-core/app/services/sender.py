"""
Outbound message sender — calls the Telegram gateway POST /send endpoint.
Used for proactive messages (cron jobs, location triggers) where shogun-core
initiates contact rather than replying to an inbound message.
"""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


async def send_photo(chat_id: str | int, photo_url: str, caption: str = "") -> bool:
    """
    Send a photo to a Telegram chat via the Bot API directly.
    photo_url must be a publicly accessible HTTPS image URL.
    Caption is optional (max 1024 chars for Telegram).
    Returns True on success, False on failure.
    """
    from app.config import settings
    token = settings.telegram_bot_token
    caption_trimmed = caption[:1024] if caption else ""
    payload: dict = {"chat_id": str(chat_id), "photo": photo_url}
    if caption_trimmed:
        payload["caption"] = caption_trimmed
        payload["parse_mode"] = "Markdown"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                json=payload,
            )
            data = resp.json()
            if data.get("ok"):
                logger.info("Sent photo to chat_id=%s url=%s", chat_id, photo_url[:80])
                return True
            logger.error("send_photo failed: %s", data.get("description", data))
            return False
    except Exception as exc:
        logger.error("send_photo error chat_id=%s: %s", chat_id, exc)
        return False


async def send_message(chat_id: str | int, text: str, parse_mode: str = "Markdown") -> bool:
    """
    Push a message to a Telegram chat via the gateway send API.
    Returns True on success, False on failure.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.telegram_gateway_url}/send",
                json={"chat_id": str(chat_id), "text": text, "parse_mode": parse_mode},
                headers={"X-Send-Secret": settings.telegram_send_secret},
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("ok"):
                logger.info("Sent message to chat_id=%s message_id=%s", chat_id, data.get("message_id"))
                return True
            logger.error("send_message failed: %s", data)
            return False
    except Exception as exc:
        logger.error("send_message error chat_id=%s: %s", chat_id, exc)
        return False
