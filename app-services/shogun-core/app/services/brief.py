"""
Morning brief service — sends daily 7am JST summary to all active users.
Called by the APScheduler job in main.py.
"""
import logging
from datetime import date, datetime, timezone, timedelta

from app import db
from app.config import settings
from app.services import weather as weather_svc
from app.services.sender import send_message

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))
TRIP_START = date(2026, 3, 23)
TRIP_END = date(2026, 4, 9)
NOTIFY_FROM = date(2026, 3, 16)  # 1 week before departure

CITY_EMOJI = {
    "osaka": "🏯",
    "nara": "🦌",
    "kanazawa": "🌸",
    "tokyo": "🗼",
    "san francisco": "🌉",
    "los angeles": "✈️",
}

async def send_morning_brief():
    """Send morning brief to all users with notification_active=True."""
    today_jst = datetime.now(JST).date()

    # Only send during pre-trip window and trip itself
    if today_jst < NOTIFY_FROM or today_jst > TRIP_END:
        logger.info("Morning brief: outside notify window (%s), skipping", today_jst)
        return

    # Get active users
    users = _get_active_users()
    if not users:
        logger.warning("Morning brief: no active users found")
        return

    # Build the shared brief content
    brief_text = await _build_brief(today_jst)

    # Send to each user
    for user_id, telegram_id, display_name in users:
        text = f"Good morning, {display_name.split()[0]}! 🌅\n\n{brief_text}"
        ok = await send_message(telegram_id, text, parse_mode="Markdown")
        logger.info("Morning brief sent to user=%s telegram_id=%s ok=%s", user_id, telegram_id, ok)


def _get_active_users():
    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, telegram_user_id, display_name FROM users WHERE notification_active = TRUE"
            )
            return cur.fetchall()
    finally:
        conn.close()


def _get_today_legs(today_jst: date) -> list[dict]:
    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT title, city, start_time, notes_en
                   FROM trip_itinerary
                   WHERE date_local = %s
                   ORDER BY leg_sequence""",
                (today_jst,)
            )
            return [{"title": r[0], "city": r[1], "time": r[2], "notes": r[3]} for r in cur.fetchall()]
    finally:
        conn.close()


def _get_current_city(today_jst: date) -> str | None:
    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT city FROM trip_itinerary
                   WHERE date_local <= %s AND city IS NOT NULL
                   AND city NOT IN ('San Francisco', 'Los Angeles')
                   ORDER BY date_local DESC, leg_sequence DESC LIMIT 1""",
                (today_jst,)
            )
            row = cur.fetchone()
            return row[0].lower() if row else None
    finally:
        conn.close()


async def _build_brief(today_jst: date) -> str:
    lines = []

    # Date header
    day_name = today_jst.strftime("%A, %B %-d")
    if today_jst < TRIP_START:
        days_left = (TRIP_START - today_jst).days
        lines.append(f"*{day_name}* — ✈️ Japan in {days_left} day{'s' if days_left != 1 else ''}!")
    else:
        trip_day = (today_jst - TRIP_START).days + 1
        lines.append(f"*{day_name}* — Day {trip_day} of 18")

    # Today's city and schedule
    city = _get_current_city(today_jst)
    if city:
        emoji = CITY_EMOJI.get(city, "📍")
        lines.append(f"{emoji} *{city.capitalize()}*")

    today_legs = _get_today_legs(today_jst)
    if today_legs:
        lines.append("\n📅 *Today's plan:*")
        for leg in today_legs:
            time_str = f" at {leg['time'].strftime('%H:%M')}" if leg['time'] else ""
            lines.append(f"• {leg['title']}{time_str}")
    elif today_jst >= TRIP_START:
        lines.append("\n📅 *Free day* — no scheduled activities")

    # Weather
    if city and city in ("osaka", "nara", "kanazawa", "tokyo"):
        try:
            weather_str = await weather_svc.get_weather_for_city(city)
            if weather_str:
                lines.append(f"\n🌤️ *Weather:* {weather_str}")
        except Exception as exc:
            logger.warning("Brief weather error: %s", exc)

    # Closing
    lines.append("\n💬 _Ask me anything about today's plans!_")

    return "\n".join(lines)
