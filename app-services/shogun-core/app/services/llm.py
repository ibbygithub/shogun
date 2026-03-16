"""
LLM Gateway client. Routes all completions through llm.platform.ibbytech.com.
Uses Gemini 2.0 Flash (platform default).
"""
import logging
import httpx
from datetime import datetime, timezone, timedelta
from app.config import settings

# Japan Standard Time — used to derive "today" for trip context
_JST = timezone(timedelta(hours=9))

logger = logging.getLogger(__name__)

TIMEOUT = 25.0  # Must complete before Telegram gateway times out (~30s)


def build_system_prompt(user: dict | None, prefs: list[dict],
                        weather_str: str | None = None) -> str:
    """
    Build a system prompt from user profile, preferences, and today's trip context.
    Loads today's itinerary and city POIs from DB automatically.
    weather_str: optional pre-fetched weather string from the async weather service.
    """
    # Import here to avoid circular imports at module load time
    from app import db

    # Current JST time — always injected so the LLM never has to guess
    now_jst = datetime.now(_JST)
    today_jst = now_jst.strftime("%Y-%m-%d")
    time_jst  = now_jst.strftime("%H:%M")

    lines = [
        "You are Shogun, an expert Japan travel concierge for the Ibbotson family.",
        "You have 10 years of living experience in Japan. You know crowd patterns,",
        "opening hours, local customs, and the best spots in each city on the itinerary.",
        "You are direct, practical, and give specific recommendations — not generic tourism advice.",
        "Respond in English unless explicitly asked to translate.",
        "Keep responses concise — Telegram is a mobile interface.",
        "",
        f"Current date and time: {today_jst} {time_jst} JST",
    ]

    if user:
        lines.append(f"You are speaking with {user['display_name']}.")

    if prefs:
        by_cat: dict[str, list[str]] = {}
        for p in prefs:
            cat = p["category"]
            val = p["preference_value"]
            note = f" ({p['notes']})" if p.get("notes") else ""
            by_cat.setdefault(cat, []).append(f"{p['preference_key']}: {val}{note}")
        lines.append("User profile:")
        for cat, entries in by_cat.items():
            lines.append(f"  {cat}: {', '.join(entries)}")

    # ── Weather context (injected if pre-fetched) ─────────────────────────
    if weather_str:
        lines.append(f"Today's weather: {weather_str}")

    # ── Trip context (itinerary + city POIs) ──────────────────────────────
    try:
        # today_jst is already computed above — reuse it here
        itinerary = db.get_todays_itinerary(today_jst)
        city = db.get_city_for_date(today_jst)

        if itinerary:
            lines.append("")
            lines.append(f"Today ({today_jst} JST) — itinerary:")
            for leg in itinerary:
                time_str = f" {leg['start_time']}" if leg.get("start_time") else ""
                note_str = f" — {leg['notes_en'][:120]}" if leg.get("notes_en") else ""
                lines.append(f"  • [{leg['leg_type']}]{time_str} {leg['title']}{note_str}")

        if city:
            pois = db.get_pois_by_city(city.lower())
            if pois:
                lines.append("")
                lines.append(f"Key spots in {city} (from pre-loaded intelligence):")
                for poi in pois[:8]:  # cap at 8 to stay within reasonable token budget
                    timing = poi.get("best_time_notes", "")
                    crowd = poi.get("crowd_notes", "")
                    detail = timing or crowd
                    suffix = f" — {detail[:100]}" if detail else ""
                    lines.append(f"  • {poi['name_en']}{suffix}")

    except Exception as exc:
        logger.warning("Failed to load trip context for system prompt: %s", exc)

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
            # LLM gateway returns {"output_text": "...", "provider": ..., "model": ..., "usage": ...}
            text = data["output_text"].strip()
            # Strip any role prefix Gemini occasionally prepends
            if text.upper().startswith("ASSISTANT:"):
                text = text[10:].lstrip()
            return text

    except httpx.TimeoutException:
        logger.error("LLM gateway timeout after %.0fs", TIMEOUT)
        return "Sorry, I'm taking too long to respond. Please try again."
    except Exception as exc:
        logger.error("LLM gateway error: %s", exc)
        return "Sorry, I couldn't reach my thinking engine right now. Please try again in a moment."
