"""
Valkey store for shogun-core.

Key patterns:
  shogun:context:{uid}   — conversation history (list of {role, content})
  shogun:location:{uid}  — last trigger location {lat, lng, ts}
  shogun:translate:{uid} — translate mode flag (presence = active)
  shogun:social:{uid}    — social capture mode flag (5-min TTL)

All keys use a 24h idle TTL reset on each write (except social: 5-min).
"""
import json
import logging
import redis
from app.config import settings

logger = logging.getLogger(__name__)

CONTEXT_TTL = 86400  # 24 hours in seconds
SOCIAL_TTL = 300  # 5 minutes — social capture mode window
KEY_PREFIX = "shogun:context:"
LOCATION_KEY_PREFIX = "shogun:location:"
TRANSLATE_KEY_PREFIX = "shogun:translate:"
SOCIAL_KEY_PREFIX = "shogun:social:"


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


# ── Location state ─────────────────────────────────────────────────────────

def get_location(telegram_user_id: int) -> dict | None:
    """Return last trigger location {lat, lng, ts} or None."""
    try:
        r = _client()
        raw = r.get(f"{LOCATION_KEY_PREFIX}{telegram_user_id}")
        if not raw:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Valkey get_location failed for user %s: %s", telegram_user_id, exc)
        return None


def save_location(telegram_user_id: int, lat: float, lng: float, ts: int) -> None:
    """Persist last trigger location and reset the 24h TTL."""
    try:
        r = _client()
        r.setex(
            f"{LOCATION_KEY_PREFIX}{telegram_user_id}",
            CONTEXT_TTL,
            json.dumps({"lat": lat, "lng": lng, "ts": ts}),
        )
    except Exception as exc:
        logger.warning("Valkey save_location failed for user %s: %s", telegram_user_id, exc)


# ── Translate mode ──────────────────────────────────────────────────────────

def get_translate_mode(telegram_user_id: int) -> bool:
    """Return True if translate mode is active for this user."""
    try:
        r = _client()
        return r.exists(f"{TRANSLATE_KEY_PREFIX}{telegram_user_id}") > 0
    except Exception as exc:
        logger.warning("Valkey get_translate_mode failed for user %s: %s", telegram_user_id, exc)
        return False


def set_translate_mode(telegram_user_id: int, active: bool) -> None:
    """Enable or disable translate mode. Uses key presence — no value stored."""
    try:
        r = _client()
        key = f"{TRANSLATE_KEY_PREFIX}{telegram_user_id}"
        if active:
            r.setex(key, CONTEXT_TTL, "1")
        else:
            r.delete(key)
    except Exception as exc:
        logger.warning("Valkey set_translate_mode failed for user %s: %s", telegram_user_id, exc)


# ── Social capture mode ───────────────────────────────────────────────────

def get_social_mode(telegram_user_id: int) -> bool:
    """Return True if social capture mode is active for this user."""
    try:
        r = _client()
        return r.exists(f"{SOCIAL_KEY_PREFIX}{telegram_user_id}") > 0
    except Exception as exc:
        logger.warning("Valkey get_social_mode failed for user %s: %s", telegram_user_id, exc)
        return False


def set_social_mode(telegram_user_id: int) -> None:
    """Enter social capture mode with a 5-minute TTL."""
    try:
        r = _client()
        r.setex(f"{SOCIAL_KEY_PREFIX}{telegram_user_id}", SOCIAL_TTL, "1")
    except Exception as exc:
        logger.warning("Valkey set_social_mode failed for user %s: %s", telegram_user_id, exc)


def clear_social_mode(telegram_user_id: int) -> None:
    """Exit social capture mode."""
    try:
        r = _client()
        r.delete(f"{SOCIAL_KEY_PREFIX}{telegram_user_id}")
    except Exception as exc:
        logger.warning("Valkey clear_social_mode failed for user %s: %s", telegram_user_id, exc)
