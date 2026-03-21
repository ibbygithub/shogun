"""
Location handler — Phase 4.
Triggers a proactive recommendation when the user moves ≥150m from the last trigger point
and at least 5 minutes have elapsed since the last trigger.
"""
import logging
import math
import time
from app.models import TelegramEnvelope
from app.services.llm import build_system_prompt
from app.services.tools import location_triggered_places
from app.valkey_client import get_context, save_context, get_location, save_location

logger = logging.getLogger(__name__)

TRIGGER_METERS = 150    # Distance threshold before firing a new recommendation
COOLDOWN_SECONDS = 300  # Minimum seconds between location triggers (5 minutes)


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres between two (lat, lng) points."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def handle(envelope: TelegramEnvelope, user: dict | None, prefs: list[dict]) -> str | None:
    """
    Process a location update.
    Returns a recommendation string if the trigger threshold fires, None otherwise.
    """
    loc = envelope.payload.get("location") or {}
    lat = loc.get("latitude")
    lng = loc.get("longitude")
    if lat is None or lng is None:
        logger.warning("Location envelope missing coordinates for user %s", envelope.from_.user_id)
        return None

    is_live = loc.get("live_period") is not None
    telegram_user_id = envelope.from_.user_id

    if not user:
        logger.info("Location from unregistered user %s — ignoring", telegram_user_id)
        return None

    # Respect the user's notification preference
    if not user.get("notification_active", True):
        logger.info("Notifications off for %s — skipping location trigger", user["display_name"])
        return None

    now = int(time.time())
    last = get_location(telegram_user_id)

    if not last:
        # First location received — store and acknowledge the initial share
        save_location(telegram_user_id, lat, lng, now)
        if not is_live:
            return (
                f"Got your location, {user['display_name']}. "
                "I'll alert you when something interesting is nearby as you explore."
            )
        return None

    distance = _haversine_meters(last["lat"], last["lng"], lat, lng)
    elapsed = now - last["ts"]

    logger.info(
        "Location delta for %s: %.0fm moved, %ds elapsed (thresholds: %dm, %ds)",
        user["display_name"], distance, elapsed, TRIGGER_METERS, COOLDOWN_SECONDS,
    )

    if distance < TRIGGER_METERS or elapsed < COOLDOWN_SECONDS:
        return None  # Not far enough, or too soon since last trigger

    # Threshold crossed — update stored location and generate a recommendation
    save_location(telegram_user_id, lat, lng, now)

    history = get_context(telegram_user_id)
    system_prompt = build_system_prompt(user, prefs)

    # Call Places API with actual GPS coordinates, then synthesise via Gemini
    reply = await location_triggered_places(lat, lng, system_prompt, history)

    # Store the exchange so follow-up questions ("tell me more") work naturally
    history.append({"role": "user", "content": f"[Location update: {lat:.5f}, {lng:.5f}]"})
    history.append({"role": "assistant", "content": reply})
    if len(history) > 20:
        history = history[-20:]
    save_context(telegram_user_id, history)

    return f"📍 {reply}"
