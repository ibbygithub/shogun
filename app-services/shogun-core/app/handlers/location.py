"""
Location handler — Phase 3: acknowledge receipt.
Phase 4 will add: 150m radius trigger, 5-minute cooldown, POI proximity alerts.
"""
import logging
from app.models import TelegramEnvelope

logger = logging.getLogger(__name__)


async def handle(envelope: TelegramEnvelope, user: dict | None, prefs: list[dict]) -> str | None:
    """
    Process a location update.
    Returns reply_text for initial shares; None for live location updates (silent).
    Phase 4 will add proximity trigger logic here.
    """
    loc = envelope.payload.get("location") or {}
    lat = loc.get("latitude")
    lng = loc.get("longitude")
    is_live = loc.get("live_period") is not None

    if user:
        logger.info(
            "Location from %s: lat=%.5f lng=%.5f live=%s",
            user["display_name"], lat or 0, lng or 0, is_live,
        )
    else:
        logger.info("Location from unregistered user %s", envelope.from_.user_id)

    # Silent on live updates — don't spam the user as they move
    if is_live:
        return None

    # Acknowledge initial location share only
    if not user:
        return None

    name = user["display_name"]
    return f"Got your location, {name}. Location alerts are coming in Phase 4."
