from fastapi import APIRouter, Request, Depends
from datetime import date, datetime
import httpx
from auth import get_current_user, User
from db import get_conn
from models import DashboardStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

TRIP_START = date(2026, 3, 23)
TRIP_END = date(2026, 4, 9)
TOTAL_DAYS = (TRIP_END - TRIP_START).days + 1


def _current_city_from_db() -> tuple[str | None, int | None]:
    today = date.today()
    if today < TRIP_START or today > TRIP_END:
        return None, None

    trip_day = (today - TRIP_START).days + 1

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT city FROM trip_itinerary
                WHERE date_local <= %s AND city IS NOT NULL
                ORDER BY date_local DESC, leg_sequence DESC LIMIT 1
                """,
                (today,),
            )
            row = cur.fetchone()
            city = row[0] if row else None

    return city, trip_day


def _shogun_core_health() -> str:
    # Post-Docker-Desktop migration: shogun-core runs as a container on
    # platform_net. Use the container name rather than the old brainnode-01 FQDN.
    try:
        resp = httpx.get("http://shogun-core:8082/health", timeout=3.0)
        return "ok" if resp.status_code == 200 else "degraded"
    except Exception:
        return "unreachable"


def _pending_wishlist_count() -> int:
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM wishlist_items WHERE status = 'pending'")
                return cur.fetchone()[0]
    except Exception:
        return 0


@router.get("/status", response_model=DashboardStatus)
def dashboard_status(request: Request, user: User = Depends(get_current_user)):
    city, trip_day = _current_city_from_db()
    shogun_health = _shogun_core_health()
    pending_count = _pending_wishlist_count() if user.role == "admin" else 0

    return DashboardStatus(
        current_city=city,
        trip_day=trip_day,
        total_days=TOTAL_DAYS,
        departure_date=TRIP_START.isoformat(),
        shogun_health=shogun_health,
        pending_wishlist_count=pending_count,
    )
