"""
Valkey conversation context store.
Key pattern: shogun:context:{telegram_user_id}
TTL: 24h idle (reset on every message).
Value: JSON list of {role, content} objects — the conversation history.
"""
import json
import logging
import redis
from app.config import settings

logger = logging.getLogger(__name__)

CONTEXT_TTL = 86400  # 24 hours in seconds
KEY_PREFIX = "shogun:context:"


def _client() -> redis.Redis:
    return redis.Redis(
        host=settings.valkey_host,
        port=settings.valkey_port,
        password=settings.valkey_password,
        decode_responses=True,
        socket_connect_timeout=3,
    )


def get_context(telegram_user_id: int) -> list[dict]:
    """Load conversation history for a user. Returns [] if none or expired."""
    try:
        r = _client()
        raw = r.get(f"{KEY_PREFIX}{telegram_user_id}")
        if not raw:
            return []
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Valkey get_context failed for user %s: %s", telegram_user_id, exc)
        return []


def save_context(telegram_user_id: int, messages: list[dict]) -> None:
    """Persist conversation history and reset the 24h TTL."""
    try:
        r = _client()
        r.setex(
            f"{KEY_PREFIX}{telegram_user_id}",
            CONTEXT_TTL,
            json.dumps(messages),
        )
    except Exception as exc:
        logger.warning("Valkey save_context failed for user %s: %s", telegram_user_id, exc)


def clear_context(telegram_user_id: int) -> None:
    """Delete conversation history for a user."""
    try:
        r = _client()
        r.delete(f"{KEY_PREFIX}{telegram_user_id}")
    except Exception as exc:
        logger.warning("Valkey clear_context failed for user %s: %s", telegram_user_id, exc)
