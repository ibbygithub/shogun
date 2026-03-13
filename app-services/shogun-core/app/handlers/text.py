"""
Text message handler — the primary interaction path.
Checks for system commands first, then routes to LLM.
"""
import logging
from app.models import TelegramEnvelope
from app.commands.system import handle_command
from app.services.llm import chat, build_system_prompt
from app.valkey_client import get_context, save_context

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

    # Unknown users get a polite rejection
    if not user:
        logger.warning("Unregistered user %s sent: %s", telegram_user_id, text[:50])
        return "Hi! I'm Shogun, the Ibbotson family Japan concierge. You're not registered in my system. Ask Todd to add you."

    # Build conversation context
    history = get_context(telegram_user_id)
    system_prompt = build_system_prompt(user, prefs)

    # Append current message
    history.append({"role": "user", "content": text})

    # Call LLM
    reply = await chat(history, system_prompt)

    # Persist updated context (user + assistant turn)
    history.append({"role": "assistant", "content": reply})
    # Keep last 20 turns to avoid Valkey bloat and context window issues
    if len(history) > 20:
        history = history[-20:]
    save_context(telegram_user_id, history)

    return reply
