"""
shogun-core — Japan trip AI concierge
FastAPI application on brainnode-01, port 8082.
Receives Telegram envelopes from platform-telegram-gateway and returns reply_text.
"""
import logging
import time
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import TelegramEnvelope
from app import db, valkey_client
from app.handlers import text as text_handler
from app.handlers import location as location_handler
from app.handlers import voice as voice_handler
from app.handlers import photo as photo_handler
from app.handlers import media as media_handler
from app.services.brief import send_morning_brief

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("shogun-core starting on port %s", settings.app_port)
    # Smoke-test DB connection at startup — fail fast if misconfigured
    try:
        conn = db.get_connection()
        conn.close()
        logger.info("DB connection OK (shogun_v1 @ %s)", settings.db_host)
    except Exception as exc:
        logger.error("DB connection FAILED at startup: %s", exc)
        # Don't crash — allow the app to start so /health still responds

    # Start the morning brief scheduler — fires at 22:00 UTC = 7:00 AM JST
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_morning_brief,
        CronTrigger(hour=22, minute=0, timezone="UTC"),
        id="morning_brief",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Morning brief scheduler started (fires at 22:00 UTC = 7:00 AM JST)")

    yield

    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
    logger.info("shogun-core shutting down")


app = FastAPI(title="shogun-core", version="0.4.0", lifespan=lifespan)


@app.get("/health")
async def health():
    """Liveness check used by validate_shogun.py and monitoring."""
    return {"ok": True, "service": "shogun-core", "version": "0.4.0"}


@app.get("/debug/morning-brief")
async def trigger_morning_brief():
    """Manually trigger the morning brief — for testing only."""
    from app.services.brief import send_morning_brief
    await send_morning_brief()
    return {"ok": True, "message": "Brief sent"}


@app.post("/telegram/events")
async def telegram_events(request: Request):
    """
    Primary inbound endpoint. Receives all Telegram event envelopes from the gateway.
    Returns {"reply_text": "..."} to trigger a bot reply, or {} to stay silent.
    """
    t0 = time.time()
    try:
        raw = await request.json()
    except Exception:
        logger.warning("Received non-JSON body on /telegram/events")
        return JSONResponse(status_code=400, content={"error": "invalid JSON"})

    # Normalise "from" → "from_" (Python reserved word)
    envelope = TelegramEnvelope.model_validate_json_alias(raw)
    telegram_user_id = envelope.from_.user_id
    kind = envelope.kind

    logger.info(
        "receipt=%s kind=%s user=%s chat=%s",
        envelope.receipt_id, kind, telegram_user_id, envelope.chat.id,
    )

    # Load user and preferences from DB
    user = None
    prefs = []
    if telegram_user_id:
        try:
            user = db.get_user_by_telegram_id(telegram_user_id)
            if user:
                prefs = db.get_user_preferences(user["id"])
        except Exception as exc:
            logger.error("DB lookup failed for user %s: %s", telegram_user_id, exc)

    # Route to the correct handler
    reply_text = None
    try:
        if kind == "text":
            reply_text = await text_handler.handle(envelope, user, prefs)
        elif kind == "location":
            reply_text = await location_handler.handle(envelope, user, prefs)
        elif kind == "photo":
            reply_text = await photo_handler.handle(envelope, user, prefs)
        elif kind == "voice":
            reply_text = await voice_handler.handle(envelope, user, prefs)
        elif kind == "document":
            reply_text = await media_handler.handle_document(envelope, user, prefs)
        else:
            logger.warning("Unknown envelope kind: %s", kind)

    except Exception as exc:
        logger.error("Handler error kind=%s user=%s: %s", kind, telegram_user_id, exc, exc_info=True)
        reply_text = "Something went wrong on my end. Please try again."

    elapsed = (time.time() - t0) * 1000
    logger.info("receipt=%s handled in %.0fms reply=%s", envelope.receipt_id, elapsed, bool(reply_text))

    if reply_text:
        return {"reply_text": reply_text}
    return {}
