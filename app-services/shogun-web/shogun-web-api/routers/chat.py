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
            # The weather router stores a full JSON blob; parse and format it
            try:
                data = json.loads(cached)
                current = data.get("current", {})
                temp = current.get("temperature_2m")
                # forecast_3day is stored as list of WeatherDay dicts
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
                pass  # fall through to fresh fetch
    except Exception:
        pass

    # Fresh fetch from Open-Meteo
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

        # Cache the raw weather string (not the full JSON blob) under a separate key
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
    The POI section is formatted to be unmissable by the LLM so it uses
    dashboard data rather than generic knowledge.
    """
    now_jst   = datetime.now(_JST)
    today_str = now_jst.strftime("%Y-%m-%d")
    time_str  = now_jst.strftime("%H:%M")

    weather_line = ""
    weather_str = _get_weather_for_city(city)
    if weather_str:
        weather_line = f"\nToday's weather: {weather_str}"

    # Fetch today's itinerary and city POIs from the database
    itinerary = _fetch_today_itinerary()
    pois = _fetch_city_pois(city)

    # Build the dashboard data block — formatted to be hard to ignore
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

    # Check for legacy history (old single-key scheme)
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
        # Migrate messages to new per-conversation key
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

    # Update conversation metadata: title (from first user message), count, last_at
    convs = _load_conv_list(user_id)
    for conv in convs:
        if conv["id"] == conv_id:
            conv["last_at"] = time.time()
            conv["message_count"] = len(history)
            # Derive title from first user message if still a default placeholder
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

    # Determine current trip city for context
    city = _current_city()

    # Build dynamic system prompt with live time and weather
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

    history.append({
        "role": "user",
        "content": user_message,
        "timestamp": time.time(),
    })

    # Build messages for LLM gateway (strip timestamps for API call)
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
    response_text = data.get("output_text") or data.get("response", "")

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

    return {"response": response_text, "session_id": str(user.id)}


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
    # If deleted conversation was current, switch to most recent remaining or clear
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
