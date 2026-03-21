"""
Text message handler — the primary interaction path.
Checks for system commands first, then routes to LLM (with RAG for food/place queries).
Translate mode: when active, appends translation instruction to the system prompt.
"""
import logging
import re
from app.models import TelegramEnvelope
from app.commands.system import handle_command, handle_async_command
from app.services.llm import chat, build_system_prompt
from app.services.tools import chat_with_tools, forced_research
from app.services.weather import get_weather_for_city
from app.services.sender import send_photo
from app.valkey_client import get_context, save_context, get_translate_mode

_IMAGE_URL_RE = re.compile(r"##IMAGE_URL:(https?://\S+)##\n?")

logger = logging.getLogger(__name__)


async def handle(envelope: TelegramEnvelope, user: dict | None, prefs: list[dict]) -> str:
    """Process a text message. Returns reply_text."""
    text = envelope.payload.get("text", "").strip()
    telegram_user_id = envelope.from_.user_id

    # System commands bypass LLM
    if text.startswith("/"):
        reply = handle_command(text, user)
        if reply:
            return reply
        # Async commands (/brief) and /research are handled below
        async_reply = await handle_async_command(text, user)
        if async_reply is not None:
            return async_reply

    # Unknown users get a polite rejection
    if not user:
        logger.warning("Unregistered user %s sent: %s", telegram_user_id, text[:50])
        return "Hi! I'm Shogun, the Ibbotson family Japan concierge. You're not registered in my system. Ask Todd to add you."

    # Build conversation context
    history = get_context(telegram_user_id)

    # Pre-fetch weather asynchronously so build_system_prompt can inject it
    # City is derived from the itinerary; fall back gracefully if unavailable
    weather_str: str | None = None
    city: str | None = None
    try:
        from datetime import datetime, timezone, timedelta
        from app import db
        _JST = timezone(timedelta(hours=9))
        today_jst = datetime.now(_JST).strftime("%Y-%m-%d")
        city = db.get_city_for_date(today_jst)
        if city:
            weather_str = await get_weather_for_city(city.lower())
    except Exception as _exc:
        logger.warning("Weather pre-fetch failed: %s", _exc)

    system_prompt = build_system_prompt(user, prefs, weather_str=weather_str)

    # Translate mode: append translation instruction to system prompt
    if get_translate_mode(telegram_user_id):
        system_prompt += (
            "\n\nThe user has translate mode active. "
            "For any Japanese text they send: translate to English. "
            "For any English text they send: translate to Japanese and show both. "
            "Keep translations natural and note any cultural context where useful."
        )

    # /research [query] — always searches, never answers from memory
    if text.lower().startswith("/research"):
        query = text[9:].strip()
        if not query:
            return "Usage: /research [query]\nExample: /research craft beer near osaka airbnb"
        # forced_research bypasses LLM routing and always calls both DB and web search
        reply = await forced_research(query, system_prompt, city_context=city)
        # Persist just this exchange
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": reply})
        if len(history) > 20:
            history = history[-20:]
        save_context(telegram_user_id, history)
        return reply

    # Route through Gemini function calling. Falls back to RAG on any error.
    reply = await chat_with_tools(text, history, system_prompt, city_context=city)

    # If an image was found, send it as a Telegram photo and use remaining text as caption
    img_match = _IMAGE_URL_RE.search(reply)
    if img_match:
        image_url = img_match.group(1)
        caption = _IMAGE_URL_RE.sub("", reply).strip()
        await send_photo(envelope.chat.id, image_url, caption)
        # Replace reply with just the caption for context persistence
        reply = caption if caption else "Here's a photo!"

    # Persist updated context (user + assistant turn)
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": reply})
    if len(history) > 20:
        history = history[-20:]
    save_context(telegram_user_id, history)

    return reply
