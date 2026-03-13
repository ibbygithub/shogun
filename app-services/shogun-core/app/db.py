"""
PostgreSQL connection pool for shogun_v1.
Uses psycopg2 with a simple connection-per-request pattern (single user MVP).
"""
import logging
import psycopg2
import psycopg2.extras
from app.config import settings

logger = logging.getLogger(__name__)


def get_connection():
    """Return a new psycopg2 connection. Caller is responsible for closing."""
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        cursor_factory=psycopg2.extras.RealDictCursor,
        connect_timeout=5,
    )


def get_user_by_telegram_id(telegram_user_id: int) -> dict | None:
    """Return the users row for a given Telegram user ID, or None."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE telegram_user_id = %s",
                (telegram_user_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def get_user_preferences(user_id: int) -> list[dict]:
    """Return all user_preferences rows for a given users.id."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT category, preference_key, preference_value, notes "
                "FROM user_preferences WHERE user_id = %s ORDER BY category, preference_key",
                (user_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_todays_itinerary(date_local: str) -> list[dict]:
    """Return trip_itinerary rows for a given local date (YYYY-MM-DD)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT leg_type, city, title, address_en, address_ja, "
                "start_time, end_time, notes_en "
                "FROM trip_itinerary WHERE date_local = %s ORDER BY leg_sequence",
                (date_local,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_pois_by_city(city: str, category: str | None = None) -> list[dict]:
    """Return trip_pois for a city, optionally filtered by category."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if category:
                cur.execute(
                    "SELECT name_en, name_ja, category, address_en, lat, lng, "
                    "tags, crowd_notes, best_time_notes "
                    "FROM trip_pois WHERE city = %s AND category = %s",
                    (city, category),
                )
            else:
                cur.execute(
                    "SELECT name_en, name_ja, category, address_en, lat, lng, "
                    "tags, crowd_notes, best_time_notes "
                    "FROM trip_pois WHERE city = %s",
                    (city,),
                )
            return cur.fetchall()
    finally:
        conn.close()
