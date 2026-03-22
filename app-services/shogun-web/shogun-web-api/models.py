from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class ItineraryLeg(BaseModel):
    id: int
    leg_type: str
    city: Optional[str]
    date_start: Optional[date]
    date_end: Optional[date]
    title: str
    description: Optional[str]
    address_en: Optional[str]
    address_ja: Optional[str]
    confirmation_number: Optional[str]
    notes: Optional[str]
    status: Optional[str]
    trip_poi_id: Optional[int] = None


class ItineraryLegCreate(BaseModel):
    leg_type: str
    city: Optional[str] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    title: str
    description: Optional[str] = None
    address_en: Optional[str] = None
    address_ja: Optional[str] = None
    confirmation_number: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "confirmed"


class Poi(BaseModel):
    id: int
    city: Optional[str]
    name_en: str
    name_ja: Optional[str]
    category: Optional[str]
    tags: Optional[list[str]]
    description: Optional[str]
    crowd_notes: Optional[str]
    best_time: Optional[str]
    map_url: Optional[str]
    source: Optional[str]
    lat: Optional[float] = None
    lng: Optional[float] = None


class WishlistItem(BaseModel):
    id: int
    requested_by: int
    city: Optional[str]
    description: str
    ai_research: Optional[str]
    status: str
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    itinerary_note: Optional[str]
    created_utc: datetime
    category: Optional[str] = "general"
    needs_reservation: bool = False
    reservation_confirmed: bool = False


class WishlistCreate(BaseModel):
    city: Optional[str] = None
    description: str


class WishlistApprove(BaseModel):
    itinerary_note: Optional[str] = None


class ChatMessage(BaseModel):
    message: str


class WeatherCurrent(BaseModel):
    temperature_2m: float
    weather_code: int
    wind_speed_10m: float


class WeatherDay(BaseModel):
    date: str
    weather_code: int
    temperature_max: float
    temperature_min: float
    precipitation_sum: float


class WeatherResponse(BaseModel):
    city: str
    current: WeatherCurrent
    forecast_3day: list[WeatherDay]


class BlossomEntry(BaseModel):
    city: str
    spot: str
    status: str
    peak_date: str
    notes: Optional[str] = None


class Reminder(BaseModel):
    type: str
    icon: str
    text: str


class RemindersResponse(BaseModel):
    date_reminders: list[Reminder]
    global_reminders: list[Reminder]


class DashboardStatus(BaseModel):
    current_city: Optional[str]
    trip_day: Optional[int]
    total_days: int
    departure_date: str
    shogun_health: str
    pending_wishlist_count: int


class ServiceHealth(BaseModel):
    name: str
    status: str
    latency_ms: Optional[float]
    last_check: str


class AdminHealthResponse(BaseModel):
    services: list[ServiceHealth]
