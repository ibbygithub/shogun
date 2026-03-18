"""
ambient.py — All ambient data endpoints for the Shogun dashboard.

Endpoints under /api/ambient/:
  GET /api/ambient/weather/{city}     — Open-Meteo 5-day forecast, cached 30 min
  GET /api/ambient/exchange-rate      — frankfurter.app USD→JPY, cached 1 h
  GET /api/ambient/calendar           — Japan public holidays / spring events (static)
  GET /api/ambient/aqi/{city}         — WAQI air quality index, cached 1 h
  GET /api/ambient/sakura/{city}      — Tavily sakura search, cached 6 h
  GET /api/ambient/transit/{city}     — Tavily transit disruption check, cached 30 min
  GET /api/ambient/events/{city}      — Tavily weekend events, cached 6 h
  GET /api/ambient/summary            — All of the above in one call (current city)
"""

import logging
from datetime import date, datetime, timezone
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException

from auth import User, get_current_user
from cache import get_cache
from db import get_conn
from services.tavily import tavily_search

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ambient", tags=["ambient"])

# ── City data ──────────────────────────────────────────────────────────────────

CITY_COORDS: dict[str, dict] = {
    "osaka":    {"lat": 34.6937, "lon": 135.5023, "waqi_city": "osaka",    "name_ja": "大阪"},
    "nara":     {"lat": 34.6851, "lon": 135.8048, "waqi_city": "nara",     "name_ja": "奈良"},
    "kanazawa": {"lat": 36.5613, "lon": 136.6562, "waqi_city": "kanazawa", "name_ja": "金沢"},
    "tokyo":    {"lat": 35.6762, "lon": 139.6503, "waqi_city": "tokyo",    "name_ja": "東京"},
    "kyoto":    {"lat": 35.0116, "lon": 135.7681, "waqi_city": "kyoto",    "name_ja": "京都"},
}

# Trip city schedule — used by current_trip_city()
TRIP_CITIES: list[tuple[date, date, str]] = [
    (date(2026, 3, 23), date(2026, 3, 31), "tokyo"),
    (date(2026, 4, 1),  date(2026, 4, 2),  "nara"),
    (date(2026, 4, 3),  date(2026, 4, 5),  "osaka"),
    (date(2026, 4, 6),  date(2026, 4, 9),  "kyoto"),
]


def current_trip_city() -> str:
    today = date.today()
    for start, end, city in TRIP_CITIES:
        if start <= today <= end:
            return city
    # Pre-trip default
    return "osaka"


# ── Japan public holidays and spring events (static, no API) ──────────────────

JAPAN_HOLIDAYS_2026: dict[str, str] = {
    "2026-01-01": "New Year's Day",
    "2026-01-12": "Coming of Age Day",
    "2026-02-11": "National Foundation Day",
    "2026-02-23": "Emperor's Birthday",
    "2026-03-20": "Vernal Equinox Day",
    "2026-04-29": "Showa Day",
    "2026-05-03": "Constitution Memorial Day",
    "2026-05-04": "Greenery Day",
    "2026-05-05": "Children's Day",
    "2026-07-20": "Marine Day",
    "2026-08-11": "Mountain Day",
    "2026-09-21": "Respect for the Aged Day",
    "2026-09-23": "Autumnal Equinox Day",
    "2026-10-12": "Sports Day",
    "2026-11-03": "Culture Day",
    "2026-11-23": "Labor Thanksgiving Day",
}

JAPAN_SPRING_EVENTS_2026: dict[str, str] = {
    "2026-03-20": "Vernal Equinox Day — shrines and parks are busy, many people visit graves",
    "2026-03-21": "Spring Holiday Saturday — expect crowds at popular sites",
    "2026-03-25": "Nara Omizutori ends — Todai-ji less crowded after festival",
    "2026-04-01": "Cherry blossom full bloom expected in Osaka and Kyoto",
    "2026-04-03": "Osaka Castle Park sakura peak — best day for castle photos",
}

# ── WMO weather-code descriptions ─────────────────────────────────────────────

def _wmo_description(code: int) -> str:
    if code == 0:
        return "Clear sky"
    if code in (1, 2, 3):
        return "Mainly clear / partly cloudy"
    if code in (45, 48):
        return "Fog"
    if 51 <= code <= 67:
        return "Drizzle / Rain"
    if 71 <= code <= 77:
        return "Snow"
    if 80 <= code <= 82:
        return "Rain showers"
    if code == 95:
        return "Thunderstorm"
    if code in (96, 99):
        return "Thunderstorm with hail"
    return "Mixed conditions"


# ── AQI category helper ────────────────────────────────────────────────────────

def _aqi_category(aqi: int) -> str:
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"


# ── Timestamp helper ──────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Valkey best-effort helpers ─────────────────────────────────────────────────

def _cache_get(key: str) -> Optional[str]:
    """Return cached value, or None if Valkey is unreachable."""
    try:
        return get_cache().get(key)
    except Exception as e:
        logger.warning("Valkey GET failed for key %s: %s", key, e)
        return None


def _cache_set(key: str, value: str, ttl: int) -> None:
    """Write to Valkey; silently ignore errors so callers never crash."""
    try:
        get_cache().setex(key, ttl, value)
    except Exception as e:
        logger.warning("Valkey SETEX failed for key %s: %s", key, e)


# ── Internal fetch functions (called by both individual routes and /summary) ───

async def _fetch_weather(city: str) -> dict:
    """Fetch Open-Meteo 5-day weather for the given city."""
    import json

    if city not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"Unknown city: {city}")

    cache_key = f"shogun:ambient:weather:{city}"
    cached = _cache_get(cache_key)
    if cached:
        return json.loads(cached)

    coords = CITY_COORDS[city]
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "current": "temperature_2m,weathercode,precipitation,windspeed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
        "timezone": "Asia/Tokyo",
        "forecast_days": 5,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error("Open-Meteo request failed for %s: %s", city, e)
        return {
            "city": city,
            "error": "Weather data unavailable",
            "cached_at": _now_iso(),
        }

    cur = data["current"]
    daily = data["daily"]

    forecast = [
        {
            "date": daily["time"][i],
            "max": round(daily["temperature_2m_max"][i], 1),
            "min": round(daily["temperature_2m_min"][i], 1),
            "precip": round(daily["precipitation_sum"][i], 1),
            "conditions": _wmo_description(daily["weathercode"][i]),
        }
        for i in range(len(daily["time"]))
    ]

    result = {
        "city": city,
        "temp_c": round(cur["temperature_2m"], 1),
        "conditions": _wmo_description(cur["weathercode"]),
        "precip_mm": round(cur.get("precipitation", 0.0), 1),
        "wind_kmh": round(cur.get("windspeed_10m", 0.0), 1),
        "temp_max": round(daily["temperature_2m_max"][0], 1),
        "temp_min": round(daily["temperature_2m_min"][0], 1),
        "forecast": forecast,
        "cached_at": _now_iso(),
    }

    _cache_set(cache_key, json.dumps(result), 1800)
    return result


async def _fetch_exchange_rate() -> dict:
    """Fetch USD→JPY from frankfurter.app."""
    import json

    cache_key = "shogun:ambient:exchange"
    cached = _cache_get(cache_key)
    if cached:
        return json.loads(cached)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.frankfurter.app/latest",
                params={"from": "USD", "to": "JPY"},
            )
            resp.raise_for_status()
            data = resp.json()
        rate = data["rates"]["JPY"]
    except Exception as e:
        logger.error("Frankfurter exchange rate request failed: %s", e)
        return {"usd_to_jpy": None, "jpy_1000_in_usd": None, "cached_at": _now_iso(), "error": "Unavailable"}

    result = {
        "usd_to_jpy": round(rate, 2),
        "jpy_1000_in_usd": round(1000 / rate, 2) if rate else None,
        "cached_at": _now_iso(),
    }
    _cache_set(cache_key, json.dumps(result), 3600)
    return result


def _fetch_today_itinerary_for_calendar() -> Optional[dict]:
    """
    Query trip_itinerary for today's date_local.
    Returns a dict with leg, title, city, notes, or None if no row exists.
    Failures are logged and silently swallowed — calendar must not crash.
    """
    today_str = date.today().isoformat()
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
                    (today_str,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return {
            "leg": row[0],
            "title": row[1],
            "city": row[2],
            "notes": row[4],  # notes_en
        }
    except Exception as e:
        logger.warning("trip_itinerary query failed in calendar: %s", e)
        return None


def _fetch_upcoming_legs(limit: int = 3) -> list[dict]:
    """Returns the next N itinerary legs starting from today or later."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT leg_sequence, title, city, date_local, notes_en
                    FROM trip_itinerary
                    WHERE date_local >= %s
                    ORDER BY date_local, leg_sequence
                    LIMIT %s
                    """,
                    (date.today().isoformat(), limit),
                )
                rows = cur.fetchall()
                return [
                    {
                        "leg": r[0],
                        "title": r[1],
                        "city": r[2],
                        "date": str(r[3]),
                        "notes": r[4],
                    }
                    for r in rows
                ]
    except Exception as e:
        logger.warning("_fetch_upcoming_legs query failed: %s", e)
        return []


def _fetch_calendar() -> dict:
    """Return today's Japan holiday / spring event and trip itinerary entry."""
    today = date.today()
    today_str = today.isoformat()

    event = JAPAN_HOLIDAYS_2026.get(today_str)
    is_holiday = event is not None
    note = JAPAN_SPRING_EVENTS_2026.get(today_str)

    if not event:
        event = note  # use spring event as primary if no formal holiday

    itinerary = _fetch_today_itinerary_for_calendar()
    upcoming = _fetch_upcoming_legs(limit=3)

    trip_start = date(2026, 3, 23)
    days_until_trip = (trip_start - today).days if today < trip_start else 0

    return {
        "date": today_str,
        "event": event,
        "note": note if is_holiday else None,  # extra note only alongside a holiday
        "is_holiday": is_holiday,
        "itinerary": itinerary,           # today's leg (during trip)
        "upcoming_legs": upcoming,         # next 3 legs from today
        "days_until_trip": days_until_trip,  # 0 if trip already started
    }


async def _fetch_aqi(city: str) -> dict:
    """Fetch AQI from WAQI demo API."""
    import json

    if city not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"Unknown city: {city}")

    cache_key = f"shogun:ambient:aqi:{city}"
    cached = _cache_get(cache_key)
    if cached:
        return json.loads(cached)

    waqi_city = CITY_COORDS[city]["waqi_city"]
    url = f"https://api.waqi.info/feed/{waqi_city}/?token=demo"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        if data.get("status") != "ok":
            raise ValueError(f"WAQI returned non-ok status: {data.get('status')}")

        aqi_val = data["data"]["aqi"]
        dominant = data["data"].get("dominentpol", "unknown")
        result = {
            "city": city,
            "aqi": aqi_val,
            "category": _aqi_category(int(aqi_val)),
            "dominant_pollutant": dominant,
            "cached_at": _now_iso(),
        }
    except Exception as e:
        logger.warning("WAQI AQI request failed for %s: %s", city, e)
        result = {
            "city": city,
            "aqi": None,
            "category": "Unavailable",
            "dominant_pollutant": None,
            "cached_at": _now_iso(),
        }

    _cache_set(cache_key, json.dumps(result), 3600)
    return result


async def _fetch_sakura(city: str) -> dict:
    """Search for current sakura bloom status via Tavily."""
    import json

    if city not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"Unknown city: {city}")

    cache_key = f"shogun:ambient:sakura:{city}"
    cached = _cache_get(cache_key)
    if cached:
        return json.loads(cached)

    name_ja = CITY_COORDS[city]["name_ja"]
    # Run English query; merge with Japanese query results
    results_en = await tavily_search(
        f"cherry blossom forecast {city} 2026 bloom status sakura",
        max_results=3,
    )
    results_ja = await tavily_search(
        f"桜 開花状況 {name_ja} 2026",
        max_results=2,
    )

    # Merge, deduplicate by URL
    seen: set[str] = set()
    merged: list[dict] = []
    for r in results_en + results_ja:
        url = r.get("url", "")
        if url not in seen:
            seen.add(url)
            merged.append({
                "title": r.get("title", ""),
                "url": url,
                "summary": r.get("content", "")[:300],
                "score": round(r.get("score", 0.0), 4),
            })

    result = {
        "city": city,
        "results": merged[:5],
        "query_time": _now_iso(),
    }
    _cache_set(cache_key, json.dumps(result), 21600)
    return result


async def _fetch_transit(city: str) -> dict:
    """Search for transit disruptions via Tavily."""
    import json

    if city not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"Unknown city: {city}")

    cache_key = f"shogun:ambient:transit:{city}"
    cached = _cache_get(cache_key)
    if cached:
        return json.loads(cached)

    # Build city-appropriate queries
    if city == "osaka":
        queries = [
            ("JR West service notice OR delay 2026", ["jr-odekake.net"]),
            ("Osaka Metro disruption delay 2026", None),
        ]
    elif city == "tokyo":
        queries = [
            ("JR East service notice OR disruption 2026", ["jreast.co.jp"]),
            ("Tokyo Metro delay disruption 2026", None),
        ]
    elif city == "kanazawa":
        queries = [
            ("IR Ishikawa service notice OR JR West kanazawa 2026", None),
        ]
    elif city == "kyoto":
        queries = [
            ("JR West service notice Kyoto delay 2026", ["jr-odekake.net"]),
            ("Kyoto city subway disruption 2026", None),
        ]
    else:
        queries = [
            (f"JR West service notice {city} 2026", None),
        ]

    all_results: list[dict] = []
    for q, domains in queries:
        r = await tavily_search(q, max_results=3, include_domains=domains)
        all_results.extend(r)

    # Detect disruption keywords in titles and content
    disruption_keywords = {
        "delay", "delayed", "disruption", "disrupted", "suspended", "suspension",
        "cancelled", "cancellation", "outage", "遅延", "運転見合わせ", "不通", "運休",
    }
    alerts: list[str] = []
    for r in all_results:
        text = (r.get("title", "") + " " + r.get("content", "")).lower()
        if any(kw in text for kw in disruption_keywords):
            alerts.append(r.get("title", "Unknown alert"))

    result = {
        "city": city,
        "status": "disruption" if alerts else "normal",
        "alerts": alerts[:5],
        "last_checked": _now_iso(),
    }
    _cache_set(cache_key, json.dumps(result), 1800)
    return result


async def _fetch_events(city: str) -> dict:
    """Search for upcoming local events via Tavily."""
    import json

    if city not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"Unknown city: {city}")

    cache_key = f"shogun:ambient:events:{city}"
    cached = _cache_get(cache_key)
    if cached:
        return json.loads(cached)

    today = date.today()
    month_name = today.strftime("%B")
    year = today.year

    results_1 = await tavily_search(
        f"{city} free events festivals markets {month_name} {year}",
        max_results=5,
    )
    results_2 = await tavily_search(
        f"{city} outdoor market flea market {month_name} {year}",
        max_results=3,
    )

    seen: set[str] = set()
    merged: list[dict] = []
    for r in results_1 + results_2:
        url = r.get("url", "")
        if url not in seen:
            seen.add(url)
            merged.append({
                "title": r.get("title", ""),
                "url": url,
                "summary": r.get("content", "")[:300],
                "score": round(r.get("score", 0.0), 4),
            })

    result = {
        "city": city,
        "results": merged[:5],
        "query_time": _now_iso(),
    }
    _cache_set(cache_key, json.dumps(result), 21600)
    return result


# ── Route handlers ─────────────────────────────────────────────────────────────

@router.get("/weather/{city}")
async def get_weather(city: str, user: User = Depends(get_current_user)) -> Any:
    return await _fetch_weather(city.lower())


@router.get("/exchange-rate")
async def get_exchange_rate(user: User = Depends(get_current_user)) -> Any:
    return await _fetch_exchange_rate()


@router.get("/calendar")
def get_calendar(user: User = Depends(get_current_user)) -> Any:
    return _fetch_calendar()


@router.get("/aqi/{city}")
async def get_aqi(city: str, user: User = Depends(get_current_user)) -> Any:
    return await _fetch_aqi(city.lower())


@router.get("/sakura/{city}")
async def get_sakura(city: str, user: User = Depends(get_current_user)) -> Any:
    return await _fetch_sakura(city.lower())


@router.get("/transit/{city}")
async def get_transit(city: str, user: User = Depends(get_current_user)) -> Any:
    return await _fetch_transit(city.lower())


@router.get("/events/{city}")
async def get_events(city: str, user: User = Depends(get_current_user)) -> Any:
    return await _fetch_events(city.lower())


@router.get("/summary")
async def get_summary(user: User = Depends(get_current_user)) -> Any:
    """Convenience endpoint — fetches all ambient data for the current trip city
    in one shot. Minimises round trips from the dashboard on page load.
    Each sub-fetch is independent; a failure in one does not abort the others.
    """
    import asyncio

    city = current_trip_city()
    coords = CITY_COORDS.get(city, CITY_COORDS["osaka"])

    async def safe(coro):
        try:
            return await coro
        except Exception as e:
            logger.error("summary sub-fetch error: %s", e)
            return {"error": str(e)}

    weather, exchange, aqi, sakura, transit, events = await asyncio.gather(
        safe(_fetch_weather(city)),
        safe(_fetch_exchange_rate()),
        safe(_fetch_aqi(city)),
        safe(_fetch_sakura(city)),
        safe(_fetch_transit(city)),
        safe(_fetch_events(city)),
    )

    return {
        "city": city,
        "lat": coords["lat"],
        "lon": coords["lon"],
        "weather": weather,
        "exchange_rate": exchange,
        "calendar": _fetch_calendar(),
        "aqi": aqi,
        "sakura": sakura,
        "transit": transit,
        "events": events,
        "generated_at": _now_iso(),
    }
