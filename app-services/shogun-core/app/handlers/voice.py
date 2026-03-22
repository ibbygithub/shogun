"""
Voice handler — Phase 4.
Downloads OGG from Telegram → transcribes via Gemini multimodal → processes as text.
"""
import logging
import httpx
from app.models import TelegramEnvelope
from app.services.telegram_files import download_file_b64
from app.services.llm import chat, build_system_prompt
from app.valkey_client import get_context, save_context, get_translate_mode
from app.config import settings
from app.services.conversation_logger import log_field, log_section

logger = logging.getLogger(__name__)


async def handle(envelope: TelegramEnvelope, user: dict | None, prefs: list[dict]) -> str | None:
    """
    Transcribe voice message via Gemini multimodal, then process transcription as text.
    Returns a reply prefixed with the transcription so the user can confirm accuracy.
    """
    if not user:
        return None

    voice = envelope.payload.get("voice") or {}
    file_id = voice.get("file_id")
    if not file_id:
        logger.warning("Voice envelope missing file_id for user %s", envelope.from_.user_id)
        return "Received a voice message but couldn't read it. Please try again."

    # Download OGG from Telegram Bot API
    try:
        b64_data, mime_type = await download_file_b64(file_id)
    except Exception as exc:
        logger.error("Voice download failed file_id=%s: %s", file_id, exc)
        return "I couldn't download your voice message. Please try again."

    # Transcribe via LLM gateway /v1/multimodal
    try:
        async with httpx.AsyncClient(timeout=35.0) as client:
            resp = await client.post(
                f"{settings.llm_gateway_url}/v1/multimodal",
                json={
                    "prompt": "Transcribe this voice message exactly as spoken. Return only the transcription — no commentary, no labels.",
                    "file_data": b64_data,
                    "mime_type": mime_type,
                    "temperature": 0.0,
                    "max_output_tokens": 500,
                },
            )
            resp.raise_for_status()
            transcription = resp.json().get("output_text", "").strip()
    except Exception as exc:
        logger.error("Voice transcription failed: %s", exc)
        return "I couldn't transcribe your voice message. Please try sending it as text."

    if not transcription:
        return "I received your voice message but couldn't make out the words. Please try again."

    logger.info("Voice transcribed for %s: %r", user["display_name"], transcription[:80])
    log_field("user_display_name", user["display_name"])
    log_field("transcription", transcription)
    log_field("mime_type", mime_type)

    telegram_user_id = envelope.from_.user_id
    history = get_context(telegram_user_id)
    system_prompt = build_system_prompt(user, prefs)

    # If translate mode is on, treat voice as a translation request
    translate = get_translate_mode(telegram_user_id)
    log_field("translate_mode", bool(translate))
    if translate:
        user_content = (
            f"[Voice transcription]: {transcription}\n\n"
            "Translate this to Japanese. Show both the original and the translation."
        )
    else:
        user_content = f"[Voice]: {transcription}"

    history.append({"role": "user", "content": user_content})
    reply = await chat(history, system_prompt)
    log_field("system_prompt", system_prompt)
    log_field("reply_text", reply)
    history.append({"role": "assistant", "content": reply})

    if len(history) > 20:
        history = history[-20:]
    save_context(telegram_user_id, history)

    # Prefix with transcription so user can see what was heard
    return f'🎤 *"{transcription}"*\n\n{reply}'
