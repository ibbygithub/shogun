import json
from fastapi import APIRouter, Request, Query, HTTPException, Depends
import httpx
from auth import get_current_user, User
from cache import get_cache
from models import WeatherResponse, WeatherCurrent, WeatherDay

router = APIRouter(prefix="/weather", tags=["weather"])

CITY_COORDS = {
    "tokyo":  {"lat": 35.6762, "lng": 139.6503},
    "nara":   {"lat": 34.6851, "lng": 135.8048},
    "osaka":  {"lat": 34.6937, "lng": 135.5023},
    "kyoto":  {"lat": 35.0116, "lng": 135.7681},
}

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
CACHE_TTL = 1800  # 30 minutes


@router.get("", response_model=WeatherResponse)
def get_weather(
    request: Request,
    city: str = Query(...),
    user: User = Depends(get_current_user),
):
    city = city.lower()
    if city not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"Unknown city: {city}")

    cache_key = f"shogun:web:weather:{city}"
    cache = get_cache()
    cached = cache.get(cache_key)
    if cached:
        return WeatherResponse(**json.loads(cached))

    coords = CITY_COORDS[city]
    params = {
        "latitude": coords["lat"],
        "longitude": coords["lng"],
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "forecast_days": 3,
        "timezone": "Asia/Tokyo",
    }

    resp = httpx.get(OPEN_METEO, params=params, timeout=10.0)
    resp.raise_for_status()
    data = resp.json()

    current = WeatherCurrent(
        temperature_2m=data["current"]["temperature_2m"],
        weather_code=data["current"]["weather_code"],
        wind_speed_10m=data["current"]["wind_speed_10m"],
    )

    forecast = [
        WeatherDay(
            date=data["daily"]["time"][i],
            weather_code=data["daily"]["weather_code"][i],
            temperature_max=data["daily"]["temperature_2m_max"][i],
            temperature_min=data["daily"]["temperature_2m_min"][i],
            precipitation_sum=data["daily"]["precipitation_sum"][i],
        )
        for i in range(len(data["daily"]["time"]))
    ]

    result = WeatherResponse(city=city, current=current, forecast_3day=forecast)
    cache.setex(cache_key, CACHE_TTL, result.model_dump_json())
    return result
