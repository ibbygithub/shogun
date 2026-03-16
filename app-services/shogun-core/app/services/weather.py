"""
Weather service for shogun-core.
Fetches current conditions and daily forecast from Open-Meteo (no API key required).
Results are cached in Valkey for 30 minutes to avoid redundant network calls.
"""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

CITY_COORDS: dict[str, tuple[float, float]] = {
    "osaka":    (34.6937, 135.5023),
    "nara":     (34.6851, 135.8048),
    "kanazawa": (36.5613, 136.6562),
    "tokyo":    (35.6762, 139.6503),
    "kyoto":    (35.0116, 135.7681),
}

WEATHER_TTL = 1800  # 30 minutes — Open-Meteo updates hourly


def _get_redis():
    """Return a connected Redis client using the same settings as valkey_client."""
    import redis
    return redis.Redis(
        host=settings.valkey_host,
        port=settings.valkey_port,
        password=settings.valkey_password,
        decode_responses=True,
        socket_connect_timeout=3,
    )


async def get_weather_for_city(city: str) -> str | None:
    """
    Return a brief weather string for injection into the system prompt,
    or None on failure. Example:
      "Weather in Osaka: 18°C now (high 22°C / low 14°C), 2.1mm precipitation"
    """
    city_lower = city.lower()
    if city_lower not in CITY_COORDS:
        return None

    cache_key = f"shogun:weather:{city_lower}"

    # Try Valkey cache first — avoids hammering Open-Meteo on every message
    try:
        r = _get_redis()
        cached = r.get(cache_key)
        if cached:
            logger.debug("weather cache hit for %s", city_lower)
            return cached
    except Exception as exc:
        logger.warning("Valkey weather cache read failed for %s: %s", city_lower, exc)

    # Fetch from Open-Meteo — free, no API key, daily quota is generous
    lat, lon = CITY_COORDS[city_lower]
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,precipitation,weathercode,windspeed_10m"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
        "&timezone=Asia%2FTokyo&forecast_days=2"
    )
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
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

        # Write to cache — failures are non-fatal
        try:
            r = _get_redis()
            r.setex(cache_key, WEATHER_TTL, weather_str)
        except Exception as exc:
            logger.warning("Valkey weather cache write failed for %s: %s", city_lower, exc)

        logger.info("weather fetched for %s: %s", city_lower, weather_str)
        return weather_str

    except Exception as exc:
        logger.warning("Open-Meteo fetch failed for %s: %s", city_lower, exc)
        return None
