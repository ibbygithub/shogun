"""
LLM Gateway client. Routes all completions through llm.platform.ibbytech.com.
Uses Gemini 2.0 Flash (platform default).
"""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

TIMEOUT = 25.0  # Must complete before Telegram gateway times out (~30s)


def build_system_prompt(user: dict | None, prefs: list[dict]) -> str:
    """Build a system prompt from user profile and preferences."""
    lines = [
        "You are Shogun, an expert Japan travel concierge for the Ibbotson family.",
        "You have 10 years of living experience in Japan. You know crowd patterns,",
        "opening hours, local customs, and the best spots in each city on the itinerary.",
        "You are direct, practical, and give specific recommendations — not generic tourism advice.",
        "Respond in English unless explicitly asked to translate.",
        "Keep responses concise — Telegram is a mobile interface.",
        "",
    ]

    if user:
        lines.append(f"You are speaking with {user['display_name']}.")

    if prefs:
        # Group preferences by category for readability
        by_cat: dict[str, list[str]] = {}
        for p in prefs:
            cat = p["category"]
            val = p["preference_value"]
            note = f" ({p['notes']})" if p.get("notes") else ""
            by_cat.setdefault(cat, []).append(f"{p['preference_key']}: {val}{note}")

        lines.append("User profile:")
        for cat, entries in by_cat.items():
            lines.append(f"  {cat}: {', '.join(entries)}")

    return "\n".join(lines)


async def chat(
    messages: list[dict],
    system_prompt: str,
    max_tokens: int = 600,
) -> str:
    """
    Send a chat request to the LLM gateway.
    messages: list of {role, content} — conversation history + current message.
    Returns the assistant reply text, or an error string.
    """
    payload = {
        "provider": "google",
        "model": "gemini-2.0-flash",
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "max_output_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{settings.llm_gateway_url}/v1/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            # LLM gateway returns {"choices": [{"message": {"content": "..."}}], ...}
            return data["choices"][0]["message"]["content"].strip()

    except httpx.TimeoutException:
        logger.error("LLM gateway timeout after %.0fs", TIMEOUT)
        return "Sorry, I'm taking too long to respond. Please try again."
    except Exception as exc:
        logger.error("LLM gateway error: %s", exc)
        return "Sorry, I couldn't reach my thinking engine right now. Please try again in a moment."
