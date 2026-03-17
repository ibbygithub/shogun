import json
import os
import time
import uuid
import httpx
from datetime import datetime, date, timezone, timedelta
from fastapi import APIRouter, Request, Depends
from auth import get_current_user, User
from cache import get_cache
from db import get_conn
from models import ChatMessage

router = APIRouter(prefix="/chat", tags=["chat"])

LLM_GATEWAY  = os.getenv("LLM_GATEWAY_URL", "http://platform-llm-gateway:8080")
TAVILY_GW    = os.getenv("TAVILY_GATEWAY_URL", "http://platform-tavily:8084")
# Gemini REST API — used directly for function-calling requests (not available via gateway)
GOOGLE_API_KEY   = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_BASE_URL  = os.getenv("GOOGLE_BASE_URL", "https://generativelanguage.googleapis.com").rstrip("/")
GEMINI_MODEL     = "gemini-2.0-flash"

HISTORY_TTL  = 86400  # 24 hours

CONV_LIST_TTL = 60 * 60 * 24 * 30   # 30 days
CONV_MSG_TTL  = 60 * 60 * 24        # 24h rolling

# Chat conversation API contract:
# GET  /chat/conversations              → {conversations: [{id,title,created_at,last_at,message_count}], current_id}
# POST /chat/conversations              → creates new, returns conv object
# DELETE /chat/conversations/{id}       → deletes conversation + messages
# POST /chat/conversations/{id}/activate → switches active conv, returns {id, messages:[]}
# DELETE /chat/history                  → clears current conv messages
# GET  /chat/history                    → returns current conv messages (unchanged)
# POST /chat                            → send message in current conv (unchanged)

# Japan Standard Time
_JST = timezone(timedelta(hours=9))

# Trip city schedule — used to derive the current city without a DB call
_CITY_SCHEDULE = [
    ("2026-03-23", "2026-03-29", "osaka"),
    ("2026-03-30", "2026-03-31", "kanazawa"),
    ("2026-04-01", "2026-04-09", "tokyo"),
]

# Open-Meteo coordinates for trip cities
_CITY_COORDS: dict[str, tuple[float, float]] = {
    "osaka":    (34.6937, 135.5023),
    "kanazawa": (36.5613, 136.6562),
    "tokyo":    (35.6762, 139.6503),
    "kyoto":    (35.0116, 135.7681),
    "nara":     (34.6851, 135.8048),
}

# Keywords that trigger a Tavily search for current sakura / event data
_SAKURA_KEYWORDS = {
    "sakura", "cherry blossom", "hanami", "bloom", "blooming", "blossoms",
    "spring flowers", "weather", "forecast", "what's on", "events",
    "happening", "weekend",
}


# ---------------------------------------------------------------------------
# Gemini function calling — tool definitions
# ---------------------------------------------------------------------------
# These are declared in Gemini's native function-declaration format.
# Each tool maps 1:1 to a _exec_* function below.

CALENDAR_TOOLS = [
    {
        "name": "get_itinerary_legs",
        "description": (
            "Get trip itinerary legs, optionally filtered by city or date. "
            "Use this when the user asks about what's planned, what's on a specific day, "
            "or the trip schedule."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Filter by city: osaka, nara, kanazawa, tokyo. Omit for all cities.",
                },
                "date": {
                    "type": "string",
                    "description": "Filter by specific date in YYYY-MM-DD format. Omit for all dates.",
                },
            },
        },
    },
    {
        "name": "update_itinerary_leg",
        "description": (
            "Update a trip itinerary leg. ALWAYS call get_itinerary_legs first to find the correct "
            "leg_id before calling this tool. Use when the user wants to add notes or change the title "
            "for a specific day. Notes are stored separately from the main description."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "leg_id": {
                    "type": "integer",
                    "description": "The ID of the leg to update — obtain from get_itinerary_legs first",
                },
                "notes": {
                    "type": "string",
                    "description": "Trip notes to add for this leg (stored in notes field, not the main description)",
                },
                "title": {
                    "type": "string",
                    "description": "New title for the leg (optional, only set if user explicitly requests a title change)",
                },
            },
            "required": ["leg_id"],
        },
    },
    {
        "name": "get_checklist_items",
        "description": (
            "Get the packing checklist items, optionally filtered by category or packed status."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by category (documents, clothing, electronics, toiletries, misc). Omit for all.",
                },
                "packed": {
                    "type": "boolean",
                    "description": "Filter by packed status. Omit for all items.",
                },
            },
        },
    },
    {
        "name": "toggle_checklist_item",
        "description": "Mark a packing checklist item as packed or unpacked.",
        "parameters": {
            "type": "object",
            "properties": {
                "item_id": {
                    "type": "integer",
                    "description": "The ID of the checklist item",
                },
                "packed": {
                    "type": "boolean",
                    "description": "True to mark as packed, False to unpack",
                },
            },
            "required": ["item_id", "packed"],
        },
    },
    {
        "name": "search_trip_knowledge",
        "description": (
            "Search the trip knowledge base for local recommendations, restaurants, shops, temples, "
            "and travel tips. Use this when the user asks about places to visit, where to eat, "
            "shopping, or local knowledge."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "city": {
                    "type": "string",
                    "description": "Filter by city. Omit for all cities.",
                },
                "category": {
                    "type": "string",
                    "description": "Filter by category: restaurant, vintage, skincare, temple, street_food, museum, etc.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_trip_pois",
        "description": (
            "Get points of interest (places to visit) for the trip, optionally filtered by city or category."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Filter by city",
                },
                "category": {
                    "type": "string",
                    "description": "Filter by POI category",
                },
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool execution functions — each returns a plain string for Gemini
# ---------------------------------------------------------------------------

def _exec_get_itinerary_legs(args: dict) -> str:
    """Query trip_itinerary filtered by city and/or date."""
    try:
        city = args.get("city")
        date_filter = args.get("date")

        clauses: list[str] = []
        params: list = []

        if city:
            clauses.append("LOWER(city) = %s")
            params.append(city.lower())
        if date_filter:
            clauses.append("date_local = %s")
            params.append(date_filter)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, leg_type, city, date_local, title, notes_en, start_time, end_time
                    FROM trip_itinerary
                    {where}
                    ORDER BY date_local, leg_sequence
                    """,
                    params,
                )
                rows = cur.fetchall()

        if not rows:
            return "No itinerary legs found matching those filters."

        lines = []
        for r in rows:
            leg_id, leg_type, city_val, date_val, title, notes_en, start_time, end_time = r
            time_str = ""
            if start_time:
                time_str = f" at {start_time}"
                if end_time:
                    time_str += f"–{end_time}"
            notes_str = f" | Notes: {notes_en}" if notes_en else ""
            lines.append(
                f"[ID:{leg_id}] {date_val} ({leg_type}) — {title}{time_str}"
                f" | City: {city_val}{notes_str}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading itinerary: {e}"


def _exec_update_itinerary_leg(args: dict) -> str:
    """Partial update of a trip_itinerary leg — notes and/or title."""
    try:
        leg_id = args.get("leg_id")
        if not leg_id:
            return "Error: leg_id is required."

        notes = args.get("notes")
        title = args.get("title")

        if not notes and not title:
            return "Error: at least one of notes or title must be provided."

        updates: list[tuple[str, object]] = []
        if title:
            updates.append(("title", title))
        if notes:
            # notes_ja is the dedicated user notes field; notes_en is the immutable leg description
            updates.append(("notes_ja", notes))

        set_clause = ", ".join(f"{col} = %s" for col, _ in updates)
        values = [v for _, v in updates] + [leg_id]

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE trip_itinerary
                    SET {set_clause}
                    WHERE id = %s
                    RETURNING id, title, notes_en, city, date_local
                    """,
                    values,
                )
                row = cur.fetchone()
                if not row:
                    return f"Error: no itinerary leg found with ID {leg_id}."

        changed = []
        if title:
            changed.append(f"title → \"{title}\"")
        if notes:
            changed.append(f"notes added: \"{notes}\"")

        return (
            f"Updated leg ID {row[0]} ({row[3]}, {row[4]}): {row[1]}. "
            f"Changes: {', '.join(changed)}."
        )
    except Exception as e:
        return f"Error updating itinerary leg: {e}"


def _exec_get_checklist_items(args: dict) -> str:
    """Query checklist_items filtered by category and/or packed status."""
    try:
        category = args.get("category")
        packed = args.get("packed")  # may be None (omitted), True, or False

        clauses: list[str] = []
        params: list = []

        if category:
            clauses.append("category = %s")
            params.append(category.lower())
        if packed is not None:
            clauses.append("packed = %s")
            params.append(bool(packed))

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, category, item_name, packed, notes
                    FROM checklist_items
                    {where}
                    ORDER BY category, item_name
                    """,
                    params,
                )
                rows = cur.fetchall()

        if not rows:
            return "No checklist items found matching those filters."

        lines = []
        for r in rows:
            item_id, cat, name, is_packed, notes = r
            status = "✓ packed" if is_packed else "○ not packed"
            notes_str = f" ({notes})" if notes else ""
            lines.append(f"[ID:{item_id}] [{cat}] {name} — {status}{notes_str}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading checklist: {e}"


def _exec_toggle_checklist_item(args: dict) -> str:
    """Toggle packed status on a checklist_items row."""
    try:
        item_id = args.get("item_id")
        packed = args.get("packed")

        if item_id is None:
            return "Error: item_id is required."
        if packed is None:
            return "Error: packed (true/false) is required."

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE checklist_items
                    SET packed = %s
                    WHERE id = %s
                    RETURNING id, item_name, packed
                    """,
                    (bool(packed), item_id),
                )
                row = cur.fetchone()
                if not row:
                    return f"Error: no checklist item found with ID {item_id}."

        status = "packed" if row[2] else "unpacked"
        return f"'{row[1]}' is now marked as {status}."
    except Exception as e:
        return f"Error toggling checklist item: {e}"


def _exec_search_trip_knowledge(args: dict) -> str:
    """Search knowledge_items using ILIKE on topic and content_summary."""
    try:
        query = args.get("query", "").strip()
        city = args.get("city")
        category = args.get("category")

        if not query:
            return "Error: query is required."

        clauses: list[str] = []
        params: list = []

        # Full-text-style ILIKE across topic and content_summary
        clauses.append("(topic ILIKE %s OR content_summary ILIKE %s)")
        like_term = f"%{query}%"
        params.extend([like_term, like_term])

        if city:
            clauses.append("(city = %s OR city IS NULL)")
            params.append(city.lower())
        if category:
            clauses.append("category = %s")
            params.append(category.lower())

        where = "WHERE " + " AND ".join(clauses)

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, city, category, topic, content_summary
                    FROM knowledge_items
                    {where}
                    ORDER BY city NULLS LAST, topic
                    LIMIT 5
                    """,
                    params,
                )
                rows = cur.fetchall()

        if not rows:
            return f"No knowledge items found for query: {query}"

        lines = []
        for r in rows:
            item_id, city_val, cat, topic, summary = r
            city_label = city_val.title() if city_val else "All cities"
            lines.append(f"[{city_label} / {cat}] {topic}: {summary}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"Error searching knowledge base: {e}"


def _exec_get_trip_pois(args: dict) -> str:
    """Query trip_pois filtered by city and/or category."""
    try:
        city = args.get("city")
        category = args.get("category")

        clauses: list[str] = []
        params: list = []

        if city:
            clauses.append("LOWER(city) = %s")
            params.append(city.lower())
        if category:
            clauses.append("category = %s")
            params.append(category.lower())

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, city, name_en, name_ja, category, crowd_notes, best_time_notes
                    FROM trip_pois
                    {where}
                    ORDER BY city, name_en
                    LIMIT 20
                    """,
                    params,
                )
                rows = cur.fetchall()

        if not rows:
            return "No POIs found matching those filters."

        lines = []
        for r in rows:
            poi_id, city_val, name_en, name_ja, cat, crowd, best_time = r
            name_str = f"{name_en}"
            if name_ja:
                name_str += f" ({name_ja})"
            crowd_str = f" | Crowd: {crowd}" if crowd else ""
            time_str = f" | Best time: {best_time}" if best_time else ""
            lines.append(f"[ID:{poi_id}] {city_val} — {name_str} [{cat}]{crowd_str}{time_str}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading POIs: {e}"


# Dispatch table — maps tool name → executor function
_TOOL_EXECUTORS = {
    "get_itinerary_legs":    _exec_get_itinerary_legs,
    "update_itinerary_leg":  _exec_update_itinerary_leg,
    "get_checklist_items":   _exec_get_checklist_items,
    "toggle_checklist_item": _exec_toggle_checklist_item,
    "search_trip_knowledge": _exec_search_trip_knowledge,
    "get_trip_pois":         _exec_get_trip_pois,
}


# ---------------------------------------------------------------------------
# Gemini REST API helpers (direct — used for tool-calling; gateway doesn't support tools)
# ---------------------------------------------------------------------------

def _gemini_url(model: str = GEMINI_MODEL) -> str:
    if not model.startswith("models/"):
        model = f"models/{model}"
    return f"{GOOGLE_BASE_URL}/v1beta/{model}:generateContent?key={GOOGLE_API_KEY}"


def _history_to_gemini_contents(history: list[dict], system_prompt: str) -> tuple[list[dict], str | None]:
    """
    Convert Shogun chat history + system prompt to Gemini content format.
    Gemini uses role "user" and "model" (not "assistant").
    System prompt is returned separately for systemInstruction.
    """
    contents: list[dict] = []
    for msg in history:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            continue  # handled via systemInstruction
        gemini_role = "model" if role == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": content}]})
    return contents, system_prompt


def _call_gemini_with_tools(
    contents: list[dict],
    system_prompt: str,
    tools: list[dict],
    max_output_tokens: int = 1024,
) -> dict:
    """
    Single Gemini REST call with function declarations.
    Returns the raw Gemini response dict.
    Raises httpx.HTTPError on failure.
    """
    payload: dict = {
        "contents": contents,
        "tools": [{"functionDeclarations": tools}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": max_output_tokens,
        },
    }
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    resp = httpx.post(_gemini_url(), json=payload, timeout=30.0)
    resp.raise_for_status()
    return resp.json()


def _extract_gemini_text(raw: dict) -> str:
    """Extract text from a Gemini generateContent response."""
    candidates = raw.get("candidates", [])
    if not candidates:
        return ""
    parts = (candidates[0].get("content") or {}).get("parts") or []
    texts = [p.get("text", "") for p in parts if "text" in p]
    return " ".join(texts).strip()


def _extract_function_calls(raw: dict) -> list[dict]:
    """
    Extract any functionCall parts from a Gemini response.
    Returns a list of dicts: [{"name": str, "args": dict}, ...]
    """
    candidates = raw.get("candidates", [])
    if not candidates:
        return []
    parts = (candidates[0].get("content") or {}).get("parts") or []
    calls = []
    for p in parts:
        if "functionCall" in p:
            fc = p["functionCall"]
            calls.append({
                "name": fc.get("name", ""),
                "args": fc.get("args", {}),
            })
    return calls


# ---------------------------------------------------------------------------
# Tool-aware chat invocation (multi-turn with tool execution loop)
# ---------------------------------------------------------------------------

def _run_chat_with_tools(
    history: list[dict],
    user_message: str,
    system_prompt: str,
) -> tuple[str, list[dict]]:
    """
    Invoke Gemini with function-calling support.
    Executes a tool-calling loop: up to 3 rounds of tool calls before
    forcing a final text response.

    Returns:
        (reply_text, tool_actions)
        tool_actions: list of {"tool": str, "summary": str}
    """
    # Build Gemini contents from history (already includes the new user message)
    contents, _ = _history_to_gemini_contents(history, system_prompt)

    # If contents is empty (first message), Gemini needs at least a user turn
    if not contents:
        contents = [{"role": "user", "parts": [{"text": user_message}]}]

    tool_actions: list[dict] = []
    MAX_TOOL_ROUNDS = 3

    for _round in range(MAX_TOOL_ROUNDS):
        raw = _call_gemini_with_tools(contents, system_prompt, CALENDAR_TOOLS)
        function_calls = _extract_function_calls(raw)

        if not function_calls:
            # Model returned a plain text response — we're done
            return _extract_gemini_text(raw), tool_actions

        # Execute each tool call and collect results
        tool_result_parts: list[dict] = []
        for fc in function_calls:
            tool_name = fc["name"]
            tool_args = fc["args"]
            executor = _TOOL_EXECUTORS.get(tool_name)
            if executor:
                result_text = executor(tool_args)
            else:
                result_text = f"Error: unknown tool '{tool_name}'"

            tool_actions.append({
                "tool": tool_name,
                "summary": _tool_action_summary(tool_name, tool_args, result_text),
            })
            tool_result_parts.append({
                "functionResponse": {
                    "name": tool_name,
                    "response": {"result": result_text},
                }
            })

        # Append model's function-call turn and the tool results to contents
        # so Gemini can synthesize a final answer
        model_turn_parts = [{"functionCall": {"name": fc["name"], "args": fc["args"]}}
                            for fc in function_calls]
        contents.append({"role": "model", "parts": model_turn_parts})
        contents.append({"role": "user", "parts": tool_result_parts})

    # Safety exit: if we hit MAX_TOOL_ROUNDS without a text response,
    # do a final call with toolConfig set to TEXT_ONLY to force a response
    raw = _call_gemini_with_tools(contents, system_prompt, tools=[])
    return _extract_gemini_text(raw), tool_actions


def _tool_action_summary(tool_name: str, args: dict, result: str) -> str:
    """Generate a human-readable one-liner describing what a tool call did."""
    if tool_name == "get_itinerary_legs":
        city = args.get("city", "")
        date_val = args.get("date", "")
        parts = []
        if city:
            parts.append(city.title())
        if date_val:
            parts.append(date_val)
        scope = " / ".join(parts) if parts else "full trip"
        return f"Read itinerary ({scope})"

    if tool_name == "update_itinerary_leg":
        leg_id = args.get("leg_id", "?")
        changes = []
        if args.get("notes"):
            changes.append("notes updated")
        if args.get("title"):
            changes.append("title updated")
        return f"Updated leg ID {leg_id}: {', '.join(changes)}"

    if tool_name == "get_checklist_items":
        cat = args.get("category", "all categories")
        packed_filter = args.get("packed")
        status = ""
        if packed_filter is True:
            status = " (packed)"
        elif packed_filter is False:
            status = " (unpacked)"
        return f"Read checklist: {cat}{status}"

    if tool_name == "toggle_checklist_item":
        item_id = args.get("item_id", "?")
        packed = args.get("packed", False)
        action = "packed" if packed else "unpacked"
        return f"Marked checklist item {item_id} as {action}"

    if tool_name == "search_trip_knowledge":
        query = args.get("query", "?")
        city = args.get("city", "")
        scope = f" in {city.title()}" if city else ""
        return f"Searched knowledge base: \"{query}\"{scope}"

    if tool_name == "get_trip_pois":
        city = args.get("city", "all cities")
        cat = args.get("category", "all categories")
        return f"Read POIs: {city} / {cat}"

    return f"Called tool: {tool_name}"


# ---------------------------------------------------------------------------
# City / weather helpers (unchanged from original)
# ---------------------------------------------------------------------------

def _current_city() -> str:
    """Return the trip city for today's JST date, defaulting to 'osaka'."""
    today = datetime.now(_JST).strftime("%Y-%m-%d")
    for start, end, city in _CITY_SCHEDULE:
        if start <= today <= end:
            return city
    return "osaka"


def _get_weather_for_city(city: str) -> str | None:
    """
    Fetch a brief weather summary for a trip city from Open-Meteo.
    Uses the Valkey cache (key: shogun:web:weather:{city}, TTL 30 min).
    Returns None on any failure — callers must degrade gracefully.
    """
    city_lower = city.lower()
    if city_lower not in _CITY_COORDS:
        return None

    cache_key = f"shogun:web:weather:{city_lower}"
    cache = get_cache()
    try:
        cached = cache.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                current = data.get("current", {})
                temp = current.get("temperature_2m")
                forecast = data.get("forecast_3day", [])
                max_t = forecast[0].get("temperature_max") if forecast else None
                min_t = forecast[0].get("temperature_min") if forecast else None
                precip = forecast[0].get("precipitation_sum") if forecast else None
                if temp is not None:
                    s = f"Weather in {city_lower.title()}: {temp}°C now"
                    if max_t is not None and min_t is not None:
                        s += f" (high {max_t}°C / low {min_t}°C)"
                    if precip and precip > 0:
                        s += f", {precip}mm precipitation"
                    return s
            except Exception:
                pass
    except Exception:
        pass

    lat, lon = _CITY_COORDS[city_lower]
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,precipitation,weathercode,windspeed_10m"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
        "&timezone=Asia%2FTokyo&forecast_days=2"
    )
    try:
        resp = httpx.get(url, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current", {})
        daily   = data.get("daily", {})
        temp    = current.get("temperature_2m", "?")
        precip  = current.get("precipitation", 0)
        max_t   = daily.get("temperature_2m_max", [None])[0]
        min_t   = daily.get("temperature_2m_min", [None])[0]

        weather_str = f"Weather in {city_lower.title()}: {temp}°C now"
        if max_t is not None and min_t is not None:
            weather_str += f" (high {max_t}°C / low {min_t}°C)"
        if precip and precip > 0:
            weather_str += f", {precip}mm precipitation"

        try:
            cache.setex(f"shogun:web:weather:str:{city_lower}", 1800, weather_str)
        except Exception:
            pass

        return weather_str
    except Exception:
        return None


def _fetch_city_pois(city: str) -> list[dict]:
    """
    Query trip_pois for the given city.
    Returns a list of dicts with name_en, name_ja, category, crowd_notes, best_time_notes.
    Returns [] on any DB failure — callers degrade gracefully.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT name_en, name_ja, category, crowd_notes, best_time_notes
                    FROM trip_pois
                    WHERE city = %s
                    ORDER BY name_en
                    """,
                    (city,),
                )
                rows = cur.fetchall()
        return [
            {
                "name_en": r[0],
                "name_ja": r[1],
                "category": r[2],
                "crowd_notes": r[3],
                "best_time_notes": r[4],
            }
            for r in rows
        ]
    except Exception:
        return []


def _fetch_today_itinerary() -> dict | None:
    """
    Query trip_itinerary for today's date (date_local).
    Returns the first matching row as a dict, or None.
    """
    today = date.today().isoformat()
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT leg_sequence, title, city, date_local, notes_en
                    FROM trip_itinerary
                    WHERE date_local = %s
                    ORDER BY leg_sequence
                    LIMIT 1
                    """,
                    (today,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return {
            "leg_sequence": row[0],
            "title": row[1],
            "city": row[2],
            "date_local": str(row[3]),
            "notes_en": row[4],
        }
    except Exception:
        return None


def build_system_prompt(city: str = "osaka") -> str:
    """
    Build the chat system prompt dynamically at request time.
    Injects current JST date/time, live weather, today's itinerary, and
    the actual POIs for the current city from the database.
    """
    now_jst   = datetime.now(_JST)
    today_str = now_jst.strftime("%Y-%m-%d")
    time_str  = now_jst.strftime("%H:%M")

    weather_line = ""
    weather_str = _get_weather_for_city(city)
    if weather_str:
        weather_line = f"\nToday's weather: {weather_str}"

    itinerary = _fetch_today_itinerary()
    pois = _fetch_city_pois(city)

    dashboard_lines = ["", "=== YOUR DASHBOARD DATA — USE THIS, DO NOT SUBSTITUTE ==="]

    if itinerary:
        itin_notes = itinerary.get("notes_en") or ""
        itin_title = itinerary.get("title") or ""
        notes_suffix = f" — {itin_notes}" if itin_notes else ""
        dashboard_lines.append(f"Today's itinerary: {itin_title}{notes_suffix}")
    else:
        dashboard_lines.append("Today's itinerary: No itinerary entry for today (pre-trip or rest day)")

    if pois:
        dashboard_lines.append(f"Top places shown on the {city.title()} dashboard:")
        for i, p in enumerate(pois, start=1):
            name = p["name_en"]
            category = p["category"] or "Place"
            crowd = p["crowd_notes"] or ""
            line = f"{i}. {name} ({category})"
            if crowd:
                line += f" — {crowd}"
            dashboard_lines.append(line)
    else:
        dashboard_lines.append(
            f"No POI data found for {city.title()} in the database. "
            f"Use your general knowledge about this city."
        )

    dashboard_lines.append("=======================================================")
    dashboard_lines.append(
        "You have access to tools that let you read and write trip data. "
        "When a user asks about itinerary, packing, or places — use the appropriate tool "
        "to fetch live data before answering. When they ask to update something, use the tool to write it."
    )
    dashboard_block = "\n".join(dashboard_lines)

    return (
        f"You are Shogun, an AI travel concierge for the Ibbotson family's Japan trip "
        f"(March 23 – April 9, 2026). You have deep knowledge of every city, restaurant, "
        f"temple, and transit option on the itinerary. You can answer questions about "
        f"specific POIs, give restaurant recommendations, explain cultural customs, and "
        f"help plan each day. In the web interface, you serve as both a trip advisor "
        f"and an educational guide — if someone asks about Todaiji Temple, give them "
        f"a real educational answer, not just basic tourist tips.\n"
        f"Current date and time: {today_str} {time_str} JST{weather_line}"
        f"{dashboard_block}"
    )


def _is_sakura_query(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _SAKURA_KEYWORDS)


def _tavily_search(query: str, city: str, max_results: int = 3) -> list[str]:
    """
    Run a Tavily search for sakura/event context.
    Returns a list of snippet strings, or [] on failure (graceful degradation).
    """
    try:
        payload = {
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
        }
        resp = httpx.post(f"{TAVILY_GW}/search", json=payload, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results") or []
        snippets = []
        for r in results:
            title   = r.get("title", "")
            content = r.get("content", "")
            url     = r.get("url", "")
            if content:
                snippet = f"{title}: {content}" if title else content
                if url:
                    snippet += f" ({url})"
                snippets.append(snippet)
        return snippets
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Per-conversation Valkey helpers
# ---------------------------------------------------------------------------

def _conv_list_key(user_id: int) -> str:
    return f"shogun:web:{user_id}:conversations"


def _conv_msg_key(user_id: int, conv_id: str) -> str:
    return f"shogun:web:{user_id}:chat:{conv_id}"


def _current_conv_key(user_id: int) -> str:
    return f"shogun:web:{user_id}:current_conv"


def _load_conv_list(user_id: int) -> list[dict]:
    cache = get_cache()
    raw = cache.get(_conv_list_key(user_id))
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def _save_conv_list(user_id: int, convs: list[dict]) -> None:
    cache = get_cache()
    cache.setex(_conv_list_key(user_id), CONV_LIST_TTL, json.dumps(convs))


def _get_or_create_current_conv(user_id: int) -> str:
    """
    Return the current conversation ID for this user.
    On first call (no current_conv key), migrate any legacy history or create
    a fresh conversation, then persist the new ID.
    """
    cache = get_cache()
    conv_id = cache.get(_current_conv_key(user_id))
    if conv_id:
        if isinstance(conv_id, bytes):
            conv_id = conv_id.decode()
        return conv_id

    legacy_key = f"shogun:web:{user_id}:chat"
    legacy_raw = cache.get(legacy_key)

    new_id = str(uuid.uuid4())
    now = time.time()

    if legacy_raw:
        try:
            legacy_msgs = json.loads(legacy_raw)
        except Exception:
            legacy_msgs = []
        title = "Previous conversation"
        count = len(legacy_msgs)
        cache.setex(_conv_msg_key(user_id, new_id), CONV_MSG_TTL, json.dumps(legacy_msgs))
        cache.delete(legacy_key)
    else:
        title = "New conversation"
        count = 0

    conv = {"id": new_id, "title": title, "created_at": now, "last_at": now, "message_count": count}
    convs = _load_conv_list(user_id)
    convs.insert(0, conv)
    _save_conv_list(user_id, convs)

    cache.setex(_current_conv_key(user_id), CONV_LIST_TTL, new_id)
    return new_id


def _load_history(user_id: int) -> list[dict]:
    conv_id = _get_or_create_current_conv(user_id)
    cache = get_cache()
    raw = cache.get(_conv_msg_key(user_id, conv_id))
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def _save_history(user_id: int, history: list[dict]) -> None:
    conv_id = _get_or_create_current_conv(user_id)
    cache = get_cache()
    cache.setex(_conv_msg_key(user_id, conv_id), CONV_MSG_TTL, json.dumps(history))

    convs = _load_conv_list(user_id)
    for conv in convs:
        if conv["id"] == conv_id:
            conv["last_at"] = time.time()
            conv["message_count"] = len(history)
            if conv["title"] in ("New conversation", "Previous conversation"):
                for msg in history:
                    if msg["role"] == "user":
                        conv["title"] = msg["content"][:60] + ("…" if len(msg["content"]) > 60 else "")
                        break
            break
    _save_conv_list(user_id, convs)


# ---------------------------------------------------------------------------
# Chat endpoints
# ---------------------------------------------------------------------------

@router.post("")
def chat(body: ChatMessage, request: Request, user: User = Depends(get_current_user)):
    history = _load_history(user.id)
    city = _current_city()
    system_prompt = build_system_prompt(city)

    # Sakura / event / weather queries: augment with Tavily before LLM call
    user_message = body.message
    if _is_sakura_query(user_message):
        lower_q = user_message.lower()
        if any(kw in lower_q for kw in {"sakura", "cherry blossom", "hanami",
                                         "bloom", "blooming", "blossoms", "spring flowers"}):
            search_q = f"cherry blossom forecast {city} 2026 bloom status"
        else:
            search_q = f"{user_message} {city} Japan 2026"

        snippets = _tavily_search(search_q, city)
        if snippets:
            context_block = "\n".join(f"- {s}" for s in snippets)
            user_message = (
                f"{user_message}\n\n"
                f"[Web search results — current 2026 data:]\n{context_block}\n\n"
                f"Use these search results to give accurate, up-to-date information. "
                f"Reference specific dates and status where visible."
            )

    # Append user message to history for the tool-calling loop
    history.append({
        "role": "user",
        "content": user_message,
        "timestamp": time.time(),
    })

    # --- Tool-calling path (Gemini direct REST) ---
    # Falls back to LLM gateway (no tools) if GOOGLE_API_KEY is not configured
    tool_actions: list[dict] = []
    if GOOGLE_API_KEY:
        try:
            response_text, tool_actions = _run_chat_with_tools(history, user_message, system_prompt)
        except Exception:
            # If Gemini direct call fails, fall through to gateway
            response_text = _fallback_llm_call(system_prompt, history)
    else:
        response_text = _fallback_llm_call(system_prompt, history)

    # Store the original (un-augmented) user message in history for clean recall
    history[-1] = {
        "role": "user",
        "content": body.message,
        "timestamp": history[-1]["timestamp"],
    }
    history.append({
        "role": "assistant",
        "content": response_text,
        "timestamp": time.time(),
    })
    _save_history(user.id, history)

    return {
        "response": response_text,
        "session_id": str(user.id),
        "tool_actions": tool_actions,
    }


def _fallback_llm_call(system_prompt: str, history: list[dict]) -> str:
    """Call the LLM gateway (no function calling) as a fallback."""
    messages = [
        {"role": h["role"], "content": h["content"]}
        for h in history
    ]
    payload = {
        "provider": "google",
        "model": "gemini-2.0-flash",
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "max_output_tokens": 1024,
    }
    resp = httpx.post(f"{LLM_GATEWAY}/v1/chat", json=payload, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()
    return data.get("output_text") or data.get("response", "")


@router.get("/history")
def get_history(request: Request, user: User = Depends(get_current_user)):
    history = _load_history(user.id)
    return [
        {"role": h["role"], "content": h["content"], "timestamp": h.get("timestamp")}
        for h in history
    ]


# ---------------------------------------------------------------------------
# Conversation management endpoints
# ---------------------------------------------------------------------------

@router.get("/conversations")
def list_conversations(request: Request, user: User = Depends(get_current_user)):
    """Return all conversations for this user, newest first."""
    convs = _load_conv_list(user.id)
    current = get_cache().get(_current_conv_key(user.id))
    if isinstance(current, bytes):
        current = current.decode()
    return {"conversations": convs, "current_id": current}


@router.post("/conversations")
def new_conversation(request: Request, user: User = Depends(get_current_user)):
    """Create a new conversation and make it current."""
    cache = get_cache()
    new_id = str(uuid.uuid4())
    now = time.time()
    conv = {"id": new_id, "title": "New conversation", "created_at": now, "last_at": now, "message_count": 0}
    convs = _load_conv_list(user.id)
    convs.insert(0, conv)
    _save_conv_list(user.id, convs)
    cache.setex(_current_conv_key(user.id), CONV_LIST_TTL, new_id)
    return conv


@router.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: str, request: Request, user: User = Depends(get_current_user)):
    """Delete a conversation and its messages."""
    cache = get_cache()
    cache.delete(_conv_msg_key(user.id, conv_id))
    convs = [c for c in _load_conv_list(user.id) if c["id"] != conv_id]
    _save_conv_list(user.id, convs)
    current = cache.get(_current_conv_key(user.id))
    if isinstance(current, bytes):
        current = current.decode()
    if current == conv_id:
        if convs:
            cache.setex(_current_conv_key(user.id), CONV_LIST_TTL, convs[0]["id"])
        else:
            cache.delete(_current_conv_key(user.id))
    return {"ok": True}


@router.post("/conversations/{conv_id}/activate")
def activate_conversation(conv_id: str, request: Request, user: User = Depends(get_current_user)):
    """Switch the active conversation and return its messages."""
    from fastapi import HTTPException
    cache = get_cache()
    convs = _load_conv_list(user.id)
    if not any(c["id"] == conv_id for c in convs):
        raise HTTPException(404, "Conversation not found")
    cache.setex(_current_conv_key(user.id), CONV_LIST_TTL, conv_id)
    raw = cache.get(_conv_msg_key(user.id, conv_id))
    history = json.loads(raw) if raw else []
    return {
        "id": conv_id,
        "messages": [{"role": h["role"], "content": h["content"], "timestamp": h.get("timestamp")} for h in history]
    }


@router.delete("/history")
def clear_current_history(request: Request, user: User = Depends(get_current_user)):
    """Clear messages in the current conversation (keeps the conversation entry)."""
    cache = get_cache()
    conv_id = _get_or_create_current_conv(user.id)
    cache.delete(_conv_msg_key(user.id, conv_id))
    convs = _load_conv_list(user.id)
    for conv in convs:
        if conv["id"] == conv_id:
            conv["message_count"] = 0
            conv["title"] = "New conversation"
            break
    _save_conv_list(user.id, convs)
    return {"ok": True}
