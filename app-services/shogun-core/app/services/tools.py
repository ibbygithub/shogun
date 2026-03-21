"""
Gemini function-calling tools for shogun-core.

Provides 5 read-only trip tools and the chat_with_tools() entry point
used by text.py. The LLM decides which tool to call based on user intent —
no hardcoded keyword matching.

Design:
- Single tool call per turn (Telegram 25s window; two Gemini REST calls +
  tool execution ≈ 20s worst case).
- DB executors run synchronously (fast, no blocking concern for single-user MVP).
- Remote executors (Places, Tavily) run via asyncio.to_thread with a 10s cap.
- Falls back to rag.respond() on Gemini errors, missing API key, or unknown tool.
"""
import asyncio
import json
import logging
import math
from datetime import date, timezone, timedelta

import httpx

from app.config import settings
from app import db as _db

logger = logging.getLogger(__name__)

_JST = timezone(timedelta(hours=9))

GEMINI_MODEL    = "gemini-2.0-flash"
GEMINI_TIMEOUT  = 20.0   # per REST call — leaves budget for two calls + tool exec
TOOL_TIMEOUT    = 10.0   # max time for a remote tool call (Places, Tavily)
RESPONSE_LIMIT  = 1200   # Telegram is a phone — truncate wall-of-text

# ---------------------------------------------------------------------------
# Trip geography constants (mirrors web UI — single source of truth is CLAUDE.md)
# ---------------------------------------------------------------------------

_CITY_SCHEDULE = [
    ("2026-03-23", "2026-03-29", "osaka"),
    ("2026-03-30", "2026-03-31", "kanazawa"),
    ("2026-04-01", "2026-04-09", "tokyo"),
]

_ANCHOR_COORDS: dict[str, tuple[float, float]] = {
    "osaka-airbnb":   (34.7085, 135.5105),
    "nara-park":      (34.6850, 135.8305),
    "usjapan":        (34.6654, 135.4321),
    "kanazawa-hotel": (36.5704, 136.6588),
    "tokyo-sugamo":   (35.7395, 139.7312),
    "ghibli-museum":  (35.6963, 139.5705),
}

_ANCHOR_LABELS: dict[str, str] = {
    "osaka-airbnb":   "Osaka Airbnb",
    "nara-park":      "Nara Park",
    "usjapan":        "Universal Studios Japan",
    "kanazawa-hotel": "Hotel Sanraku, Kanazawa",
    "tokyo-sugamo":   "Tokyo Airbnb (Sugamo)",
    "ghibli-museum":  "Ghibli Museum, Mitaka",
}

_CITY_ANCHOR_DEFAULTS = {
    "osaka":    "osaka-airbnb",
    "kanazawa": "kanazawa-hotel",
    "tokyo":    "tokyo-sugamo",
    "nara":     "nara-park",
}


def _current_city() -> str:
    today = date.today().isoformat()
    for start, end, city in _CITY_SCHEDULE:
        if start <= today <= end:
            return city
    return "osaka"


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Tool definitions (Gemini function declaration format)
# ---------------------------------------------------------------------------

TELEGRAM_TOOLS = [
    {
        "name": "search_trip_knowledge",
        "description": (
            "Search the trip knowledge base for local recommendations: restaurants, shops, "
            "craft beer, sake breweries, temples, ceramics, vintage clothing, tech/electronics, "
            "skincare, and travel tips. Use this FIRST before web_search for any question "
            "about places, food, shopping, or activities during the trip."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Plain English query (e.g. 'craft beer bar Osaka', 'ceramics Kanazawa')",
                },
                "city": {
                    "type": "string",
                    "description": "Filter by city: 'osaka', 'kyoto', 'nara', 'kanazawa', 'tokyo'. Omit to search all cities.",
                },
                "anchor": {
                    "type": "string",
                    "description": (
                        "Filter by accommodation anchor for proximity queries: "
                        "'osaka-airbnb', 'kanazawa-hotel', 'nara-park', 'tokyo-sugamo', "
                        "'ghibli-museum', 'usjapan'."
                    ),
                },
                "category": {
                    "type": "string",
                    "description": (
                        "Filter by category: dining, coffee_cafe, craft_beer, shopping, "
                        "anime_manga, tech_electronics, skincare, jewelry_artisan, "
                        "eyewear_prescription, knife_shop, ceramics, shopping_crafts, "
                        "sake_brewery, museum, temple, shrine, park, sightseeing, market, "
                        "neighborhood, convenience_store"
                    ),
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "find_nearby_places",
        "description": (
            "Search Google Places for real businesses near a trip location. "
            "ALWAYS prefer this over web_search for 'near me', 'nearby', 'walking distance', "
            "'closest', or 'within X minutes' queries. Use for: pharmacy, convenience store, "
            "ATM, restaurant nearby, etc. "
            "Anchors: 'osaka-airbnb', 'nara-park', 'usjapan', 'kanazawa-hotel', "
            "'tokyo-sugamo', 'ghibli-museum'. Omit anchor to use current accommodation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for: 'pharmacy', 'ramen restaurant', 'convenience store', 'ATM'",
                },
                "anchor": {
                    "type": "string",
                    "description": "Trip location anchor. Omit to use current city's accommodation.",
                },
                "radius_m": {
                    "type": "integer",
                    "description": "Search radius in meters. 500=5min walk, 1000=10min. Default 800.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "web_search",
        "description": (
            "Search the web for current information about restaurants, activities, events, "
            "transit, or travel topics in Japan. Use when search_trip_knowledge returns nothing "
            "or when the user needs real-time/current information (events, disruptions, hours)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query — include area/neighborhood for better results",
                },
                "city": {
                    "type": "string",
                    "description": "City context to append to the search",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_trip_pois",
        "description": "Get points of interest for the trip, optionally filtered by city or category.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Filter by city: osaka, kanazawa, tokyo, nara, kyoto. Omit for all.",
                },
                "category": {
                    "type": "string",
                    "description": "Filter by POI category",
                },
            },
        },
    },
    {
        "name": "get_itinerary",
        "description": (
            "Get trip itinerary legs. Use when the user asks what's planned, what's on a "
            "specific day, or the trip schedule."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Filter by city: osaka, nara, kanazawa, tokyo. Omit for all.",
                },
                "date": {
                    "type": "string",
                    "description": "Filter by date in YYYY-MM-DD format. Omit for all dates.",
                },
            },
        },
    },
]

# Tools that make remote HTTP calls — must run via asyncio.to_thread
_REMOTE_TOOLS = {"find_nearby_places", "web_search"}


# ---------------------------------------------------------------------------
# Tool executors (sync — safe for DB; remote ones wrapped in to_thread below)
# ---------------------------------------------------------------------------

def _exec_search_trip_knowledge(args: dict) -> str:
    query = (args.get("query") or "").strip()
    if not query:
        return "Error: query is required."
    rows = _db.search_trip_knowledge(
        query,
        city=args.get("city"),
        anchor=args.get("anchor"),
        category=args.get("category"),
    )
    if not rows:
        return f"No knowledge items found for: {query}"
    lines = []
    for row in rows:
        city_label = (row["city"] or "").title() or "General"
        topic = row["topic"] or ""
        summary = row["content_summary"] or ""
        cat = row["category"] or ""
        lines.append(f"[{city_label} / {cat}] {topic}: {summary}")
    return "\n\n".join(lines)


def _exec_find_nearby_places(args: dict) -> str:
    """Sync — called via asyncio.to_thread."""
    query = (args.get("query") or "").strip()
    if not query:
        return "Error: query is required."

    anchor = (args.get("anchor") or "").strip().lower()
    radius_m = int(args.get("radius_m") or 800)

    if anchor and anchor in _ANCHOR_COORDS:
        lat, lng = _ANCHOR_COORDS[anchor]
        location_label = _ANCHOR_LABELS.get(anchor, anchor)
    else:
        current_city = _current_city()
        default_anchor = _CITY_ANCHOR_DEFAULTS.get(current_city, "osaka-airbnb")
        lat, lng = _ANCHOR_COORDS[default_anchor]
        location_label = _ANCHOR_LABELS.get(default_anchor, default_anchor)
        anchor = default_anchor

    resp = httpx.post(
        f"{settings.places_gateway_url}/v1/places/search_text",
        json={
            "text_query": f"{query} Japan",
            "lat": lat,
            "lng": lng,
            "radius_m": radius_m,
            "max_results": 6,
            "language_code": "en",
            "region_code": "JP",
        },
        timeout=10.0,
    )
    resp.raise_for_status()
    data = resp.json()

    if not data.get("ok"):
        return f"Places search failed: {data.get('error', 'unknown error')}"

    raw_places = (data.get("data") or {}).get("places") or []
    if not raw_places:
        return f"No places found for '{query}' within {radius_m}m of {location_label}."

    # Sort by distance
    places_with_dist = []
    for p in raw_places:
        loc = p.get("location") or {}
        plat = loc.get("latitude")
        plng = loc.get("longitude")
        dist_m = round(_haversine_m(lat, lng, plat, plng)) if plat and plng else None
        places_with_dist.append((dist_m if dist_m is not None else 9_999_999, p, dist_m))
    places_with_dist.sort(key=lambda x: x[0])

    walk_limit = radius_m // 80
    lines = [f"{query.title()} near {location_label} (~{walk_limit} min walk radius):"]
    for i, (_, p, dist_m) in enumerate(places_with_dist, 1):
        name = (p.get("displayName") or {}).get("text", "Unknown")
        address = p.get("formattedAddress", "")
        rating = p.get("rating")
        rating_count = p.get("userRatingCount", 0)
        maps_uri = p.get("googleMapsUri", "")

        dist_str = f"{dist_m}m (~{max(1, round(dist_m / 80))} min walk)" if dist_m is not None else "distance unknown"
        rating_str = f" ★{rating} ({rating_count} reviews)" if rating else ""
        addr_str = f"\n   {address}" if address else ""
        maps_str = f"\n   {maps_uri}" if maps_uri else ""

        lines.append(f"\n{i}. {name}{rating_str}\n   {dist_str}{addr_str}{maps_str}")

    return "\n".join(lines)


def _exec_web_search(args: dict) -> str:
    """Sync — called via asyncio.to_thread."""
    query = (args.get("query") or "").strip()
    if not query:
        return "Error: query is required."

    city = args.get("city", "")
    search_query = query
    if city and city.lower() not in query.lower():
        search_query = f"{query} {city} Japan"
    elif "japan" not in query.lower():
        search_query = f"{query} Japan"

    resp = httpx.post(
        f"{settings.tavily_gateway_url}/v1/search",
        json={"query": search_query, "max_results": 5, "search_depth": "basic"},
        timeout=15.0,
    )
    resp.raise_for_status()
    results = resp.json().get("results") or []

    if not results:
        return (
            f"No web results for: {query}. "
            "Answer from your Japan expertise — give specific places, distances, and hours."
        )

    lines = []
    for r in results:
        title = r.get("title", "")
        content = r.get("content", "")
        url = r.get("url", "")
        if content:
            snippet = f"{title}: {content[:300]}" if title else content[:300]
            if url:
                snippet += f"\n{url}"
            lines.append(snippet)
    return "\n\n".join(lines)


def _exec_get_trip_pois(args: dict) -> str:
    city = args.get("city")
    category = args.get("category")
    # Fall back to today's city if none provided
    city_key = city.lower() if city else _current_city()
    rows = _db.get_pois_by_city(city_key, category)
    if not rows:
        scope = city_key.title() if city else "current city"
        return f"No POIs found for {scope}."
    lines = []
    for row in rows:
        name = row["name_en"]
        if row.get("name_ja"):
            name += f" ({row['name_ja']})"
        cat = row.get("category", "")
        crowd = row.get("crowd_notes", "")
        best_time = row.get("best_time_notes", "")
        detail = " | ".join(x for x in [crowd, best_time] if x)
        suffix = f" — {detail[:100]}" if detail else ""
        lines.append(f"• {name} [{cat}]{suffix}")
    return "\n".join(lines)


def _exec_get_itinerary(args: dict) -> str:
    city_filter = args.get("city")
    date_filter = args.get("date")
    conn = _db.get_connection()
    try:
        with conn.cursor() as cur:
            clauses: list[str] = []
            params: list = []
            if city_filter:
                clauses.append("LOWER(city) = %s")
                params.append(city_filter.lower())
            if date_filter:
                clauses.append("date_local = %s")
                params.append(date_filter)
            where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
            cur.execute(
                f"""
                SELECT leg_type, city, date_local, title, notes_en, start_time
                FROM trip_itinerary
                {where}
                ORDER BY date_local, leg_sequence
                """,
                params,
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        return "No itinerary legs found matching those filters."

    lines = []
    for row in rows:
        time_str = f" {row['start_time']}" if row.get("start_time") else ""
        note_str = f" — {row['notes_en'][:100]}" if row.get("notes_en") else ""
        lines.append(
            f"• [{row['leg_type']}]{time_str} {row['date_local']} "
            f"{(row['city'] or '').title()} — {row['title']}{note_str}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

_EXECUTORS = {
    "search_trip_knowledge": _exec_search_trip_knowledge,
    "find_nearby_places":    _exec_find_nearby_places,
    "web_search":            _exec_web_search,
    "get_trip_pois":         _exec_get_trip_pois,
    "get_itinerary":         _exec_get_itinerary,
}


# ---------------------------------------------------------------------------
# Gemini REST helpers
# ---------------------------------------------------------------------------

def _gemini_url() -> str:
    base = settings.google_base_url.rstrip("/")
    return f"{base}/v1beta/models/{GEMINI_MODEL}:generateContent?key={settings.google_api_key}"


def _history_to_contents(history: list[dict]) -> list[dict]:
    contents = []
    for msg in history:
        if msg["role"] == "system":
            continue
        gemini_role = "model" if msg["role"] == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": msg["content"]}]})
    return contents


def _extract_text(raw: dict) -> str:
    candidates = raw.get("candidates", [])
    if not candidates:
        return ""
    parts = (candidates[0].get("content") or {}).get("parts") or []
    return " ".join(p.get("text", "") for p in parts if "text" in p).strip()


def _extract_function_call(raw: dict) -> dict | None:
    """Return the first functionCall from a Gemini response, or None."""
    candidates = raw.get("candidates", [])
    if not candidates:
        return None
    parts = (candidates[0].get("content") or {}).get("parts") or []
    for p in parts:
        if "functionCall" in p:
            fc = p["functionCall"]
            return {"name": fc.get("name", ""), "args": fc.get("args", {})}
    return None


def _truncate(text: str, limit: int = RESPONSE_LIMIT) -> str:
    """Trim to limit, breaking at the last sentence boundary above the midpoint."""
    if len(text) <= limit:
        return text
    truncated = text[:limit]
    for sep in (". ", ".\n", "! ", "? "):
        pos = truncated.rfind(sep)
        if pos > limit // 2:
            return text[:pos + 1] + " [...]"
    return truncated + " [...]"


# ---------------------------------------------------------------------------
# Main entry point — called from text.py
# ---------------------------------------------------------------------------

async def chat_with_tools(
    user_message: str,
    history: list[dict],
    system_prompt: str,
    city_context: str | None = None,
) -> str:
    """
    Invoke Gemini with function-calling support.
    Single tool call per turn to stay within the 25s Telegram window.
    Falls back to rag.respond() on API key absence, Gemini errors, or unknown tool.
    """
    if not settings.google_api_key:
        logger.warning("tools: GOOGLE_API_KEY not set — falling back to RAG")
        from app.services.rag import respond as _rag
        return await _rag(user_message, history, system_prompt, city_context=city_context)

    # Build Gemini contents from history + current user turn
    contents = _history_to_contents(history)
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    payload: dict = {
        "contents": contents,
        "tools": [{"functionDeclarations": TELEGRAM_TOOLS}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
    }
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    # ── Round 1: may return a tool call or a direct text response ────────────
    try:
        async with httpx.AsyncClient(timeout=GEMINI_TIMEOUT) as client:
            resp = await client.post(_gemini_url(), json=payload)
            resp.raise_for_status()
            raw1 = resp.json()
    except Exception as exc:
        logger.warning("tools: Gemini call 1 failed (%s) — falling back to RAG", exc)
        from app.services.rag import respond as _rag
        return await _rag(user_message, history, system_prompt, city_context=city_context)

    fc = _extract_function_call(raw1)
    if not fc:
        # Direct text response — no tool needed
        reply = _extract_text(raw1)
        if not reply:
            logger.warning("tools: Gemini returned no text and no tool call — falling back to RAG")
            from app.services.rag import respond as _rag
            return await _rag(user_message, history, system_prompt, city_context=city_context)
        return _truncate(reply)

    tool_name = fc["name"]
    tool_args = fc["args"]

    # Inject city context for tools that benefit from it when the LLM omitted it
    if city_context and tool_name in ("search_trip_knowledge", "find_nearby_places"):
        if not tool_args.get("city") and not tool_args.get("anchor"):
            tool_args["city"] = city_context

    executor = _EXECUTORS.get(tool_name)
    if not executor:
        logger.warning("tools: unknown tool %r — falling back to RAG", tool_name)
        from app.services.rag import respond as _rag
        return await _rag(user_message, history, system_prompt, city_context=city_context)

    logger.info("tools: executing %r args=%s", tool_name, json.dumps(tool_args)[:120])

    # ── Tool execution ────────────────────────────────────────────────────────
    try:
        if tool_name in _REMOTE_TOOLS:
            tool_result = await asyncio.wait_for(
                asyncio.to_thread(executor, tool_args),
                timeout=TOOL_TIMEOUT,
            )
        else:
            tool_result = executor(tool_args)
    except asyncio.TimeoutError:
        logger.warning("tools: %r timed out after %.0fs", tool_name, TOOL_TIMEOUT)
        tool_result = f"{tool_name} timed out. Answer from your Japan expertise instead."
    except Exception as exc:
        logger.warning("tools: %r raised %s", tool_name, exc)
        tool_result = f"Tool error ({tool_name}): {exc}. Answer from your Japan expertise instead."

    # ── Round 2: synthesise final response from tool result ───────────────────
    contents_r2 = contents + [
        {"role": "model", "parts": [{"functionCall": {"name": tool_name, "args": tool_args}}]},
        {"role": "user",  "parts": [{"functionResponse": {"name": tool_name, "response": {"result": tool_result}}}]},
    ]
    payload2: dict = {
        "contents": contents_r2,
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
    }
    if system_prompt:
        payload2["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    try:
        async with httpx.AsyncClient(timeout=GEMINI_TIMEOUT) as client:
            resp2 = await client.post(_gemini_url(), json=payload2)
            resp2.raise_for_status()
            reply = _extract_text(resp2.json())
    except Exception as exc:
        logger.warning("tools: Gemini call 2 failed (%s) — returning raw tool result", exc)
        reply = tool_result

    return _truncate(reply or tool_result)
