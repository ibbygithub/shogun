"""
Photo handler — Phase 4.
Downloads photo from Telegram → analyzes via Gemini multimodal.
Saves analysis to conversation context for follow-up questions.
"""
import logging
import httpx
from app.models import TelegramEnvelope
from app.services.telegram_files import download_file_b64
from app.services.llm import build_system_prompt
from app.valkey_client import get_context, save_context
from app.config import settings

logger = logging.getLogger(__name__)

_DEFAULT_PROMPT = (
    "You are Shogun, an expert Japan travel concierge. "
    "Analyze this photo. Focus on anything travel-relevant: landmarks, food, menus, "
    "signs (translate any Japanese text), products, or places. "
    "Be specific and practical — 2-4 sentences."
)


async def handle(envelope: TelegramEnvelope, user: dict | None, prefs: list[dict]) -> str | None:
    """Analyze photo and return a description grounded in travel context."""
    if not user:
        return None

    # Gateway sends payload.photos (array of sizes) — last entry is the largest
    photos = envelope.payload.get("photos") or []
    if not photos:
        return "Photo received but I couldn't read it. Please try again."

    largest = photos[-1]
    file_id = largest.get("file_id") if isinstance(largest, dict) else None
    if not file_id:
        return "Photo received but I couldn't get the file reference. Please try again."

    caption = envelope.payload.get("caption", "").strip()

    # Build the analysis prompt — caption drives a specific question if provided
    if caption:
        prompt = (
            f"You are Shogun, an expert Japan travel concierge. "
            f"The user asks about this photo: \"{caption}\"\n"
            f"Answer their question specifically. Translate any Japanese text visible. "
            f"Be practical and concise."
        )
    else:
        prompt = _DEFAULT_PROMPT

    # Download photo from Telegram
    try:
        b64_data, mime_type = await download_file_b64(file_id)
    except Exception as exc:
        logger.error("Photo download failed file_id=%s: %s", file_id, exc)
        return "I couldn't download your photo. Please try again."

    # Analyze via LLM gateway /v1/multimodal
    try:
        async with httpx.AsyncClient(timeout=35.0) as client:
            resp = await client.post(
                f"{settings.llm_gateway_url}/v1/multimodal",
                json={
                    "prompt": prompt,
                    "file_data": b64_data,
                    "mime_type": mime_type,
                    "temperature": 0.2,
                    "max_output_tokens": 600,
                    "system_prompt": build_system_prompt(user, prefs),
                },
            )
            resp.raise_for_status()
            analysis = resp.json().get("output_text", "").strip()
    except Exception as exc:
        logger.error("Photo analysis failed: %s", exc)
        return "I couldn't analyze your photo right now. Please try again."

    if not analysis:
        return "I received your photo but couldn't analyze it. Please try again."

    logger.info("Photo analyzed for %s", user["display_name"])

    # Save to conversation context so follow-up questions have photo context
    telegram_user_id = envelope.from_.user_id
    history = get_context(telegram_user_id)
    user_entry = f"[sent a photo{': ' + caption if caption else ''}]"
    history.append({"role": "user", "content": user_entry})
    history.append({"role": "assistant", "content": analysis})
    if len(history) > 20:
        history = history[-20:]
    save_context(telegram_user_id, history)

    return f"📷 {analysis}"
