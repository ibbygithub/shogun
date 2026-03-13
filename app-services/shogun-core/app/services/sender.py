"""
Outbound message sender — calls the Telegram gateway POST /send endpoint.
Used for proactive messages (cron jobs, location triggers) where shogun-core
initiates contact rather than replying to an inbound message.
"""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


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
