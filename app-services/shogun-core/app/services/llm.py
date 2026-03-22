"""
LLM Gateway client. Routes all completions through llm.platform.ibbytech.com.
Uses Gemini 2.0 Flash (platform default).
"""
import logging
import httpx
from datetime import datetime, timezone, timedelta
from app.config import settings
from app.services.conversation_logger import log_field, log_section

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
        "Three travelers: Todd (dad, tech/food/culture), Brenda (mom, shopping/skincare/temples),",
        "Madeline (daughter, anime/vintage/photography).",
        "You have 10 years of living experience in Japan. You know crowd patterns,",
        "opening hours, local customs, and the best spots in each city on the itinerary.",
        "You are direct, practical, and give specific recommendations — not generic tourism advice.",
        "Respond in English unless explicitly asked to translate.",
        "Keep responses concise — Telegram is a mobile interface.",
        "",
        f"Current date and time: {today_jst} {time_jst} JST",
        "",
        "TRIP SCHEDULE:",
        "  Mar 23: Travel day — SFO → LAX → KIX (arrive Mar 24 evening)",
        "  Mar 24–29: Osaka — Tenjinbashi Queen Airbnb, Kita-ku (大阪市北区浪花町10-12)",
        "             Station: Tenjinbashisuji-Rokuchome (天神橋筋六丁目) — Sakaisuji/Tanimachi lines",
        "  Mar 25: Nara day trip (deer park, Todai-ji, Kasuga Shrine)",
        "  Mar 26: Universal Studios Japan",
        "  Mar 27–29: Osaka exploring (Dotonbori, Shinsekai, Tenjinbashi shotengai, Den Den Town)",
        "  Mar 30–31: Hotel Sanraku, Owaricho, Kanazawa (石川県金沢市尾張町1-1-1)",
        "             Station: Kanazawa (金沢駅) — 5 min walk to Omicho Market",
        "  Apr 1–8: Sugamo Airbnb, Toshima-ku, Tokyo (東京都豊島区巣鴨4-37-6)",
        "           Station: Sugamo (巣鴨) — Yamanote + Mita lines, 1 stop to Ikebukuro",
        "  Apr 3: Ghibli Museum NOON timed entry — tickets confirmed",
        "  Apr 9: Departure HND → SFO 4:25pm",
        "",
        "When the user asks about 'our place', 'the Airbnb', 'where we're staying', or",
        "'when we get in' — use the accommodation above for the relevant trip dates.",
        "NEVER ask for an address you already have.",
    ]

    lines += [
        "",
        "TOOL USE RULES — follow these exactly:",
        "- Any question about what is nearby, walkable, within N minutes, or 'around here' → ALWAYS call find_nearby_places. Never answer from memory.",
        "- Food, place, or shopping recommendations for a specific city → call search_trip_knowledge first.",
        "- Real-time info (events, sakura, weather updates, news) → call web_search.",
        "- Questions about the schedule, what's on today/tomorrow/a specific date → call get_itinerary.",
        "- Questions about key spots or highlights for a city → call get_trip_pois.",
        "- When uncertain about location-specific facts → use a tool, don't guess.",
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

    # Audit: log the full LLM request
    log_section("llm_gateway_request", {
        "provider": "google",
        "model": "gemini-2.0-flash",
        "message_count": len(payload["messages"]),
        "system_prompt_length": len(system_prompt),
        "max_output_tokens": max_tokens,
        "messages": payload["messages"],
    })

    import time as _time
    _t = _time.time()

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

            # Audit: log the full LLM response
            log_section("llm_gateway_response", {
                "output_text": text,
                "usage": data.get("usage"),
                "latency_ms": round((_time.time() - _t) * 1000),
            })

            return text

    except httpx.TimeoutException:
        logger.error("LLM gateway timeout after %.0fs", TIMEOUT)
        log_section("llm_gateway_response", {
            "error": "timeout",
            "latency_ms": round((_time.time() - _t) * 1000),
        })
        return "Sorry, I'm taking too long to respond. Please try again."
    except Exception as exc:
        logger.error("LLM gateway error: %s", exc)
        log_section("llm_gateway_response", {
            "error": str(exc),
            "latency_ms": round((_time.time() - _t) * 1000),
        })
        return "Sorry, I couldn't reach my thinking engine right now. Please try again in a moment."
