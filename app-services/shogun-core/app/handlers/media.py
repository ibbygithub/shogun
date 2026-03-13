"""
Media handlers for photo, document, voice — Phase 3 stubs.
Phase 4 will add: Gemini multimodal for photos, audio transcription for voice.
"""
import logging
from app.models import TelegramEnvelope

logger = logging.getLogger(__name__)


async def handle_photo(envelope: TelegramEnvelope, user: dict | None, prefs: list[dict]) -> str:
    """Phase 3 stub — photo received acknowledgement."""
    caption = envelope.payload.get("caption", "")
    logger.info("Photo received from user %s caption=%r", envelope.from_.user_id, caption)
    if not user:
        return None
    msg = f"Photo received"
    if caption:
        msg += f" with caption: \"{caption}\""
    msg += ". Photo analysis coming in the next update."
    return msg


async def handle_voice(envelope: TelegramEnvelope, user: dict | None, prefs: list[dict]) -> str:
    """Phase 3 stub — voice received acknowledgement."""
    logger.info("Voice received from user %s", envelope.from_.user_id)
    if not user:
        return None
    return "Voice message received. Voice transcription coming in the next update."


async def handle_document(envelope: TelegramEnvelope, user: dict | None, prefs: list[dict]) -> str:
    """Phase 3 stub — document received acknowledgement."""
    doc = envelope.payload.get("document") or {}
    fname = doc.get("file_name", "file")
    logger.info("Document received from user %s: %s", envelope.from_.user_id, fname)
    if not user:
        return None
    return f"Document received: {fname}."
