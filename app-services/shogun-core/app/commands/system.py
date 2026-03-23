"""
System commands: /quiet, /active, /status, /help, /reset, /translate,
                 /pois, /checklist, /brief, /bug, /social
Sync commands return a reply_text directly.
Async commands (/brief) are handled by handle_async_command().
"""
import logging
import psycopg2
from app import db
from app.db import get_connection
from app.valkey_client import (
    clear_context, get_translate_mode, set_translate_mode,
    set_social_mode,
)

logger = logging.getLogger(__name__)


def handle_command(command: str, user: dict | None) -> str | None:
    """
    Check if text is a system command. Returns reply_text if handled, None otherwise.
    command: the full message text (e.g. "/quiet", "/status")
    """
    cmd = command.strip().lower().split()[0]

    if cmd == "/help":
        return (
            "*Shogun Commands*\n"
            "/pois — today's key spots for your city\n"
            "/checklist — packing list status\n"
            "/brief — today's morning brief on demand\n"
            "/research [query] — search knowledge base + web\n"
            "/bug [description] — report an issue with Shogun\n"
            "/social — save photos and notes for your trip journal\n"
            "/quiet — stop unsolicited location alerts\n"
            "/active — resume location alerts\n"
            "/translate on|off — toggle translation mode\n"
            "/status — show your current settings\n"
            "/reset — clear conversation memory\n"
            "/help — this message"
        )

    if cmd == "/status":
        if not user:
            return "You're not registered in Shogun yet. Ask Todd to add you."
        notif = "active" if user["notification_active"] else "quiet"
        translate = get_translate_mode(user["telegram_user_id"])
        return (
            f"*{user['display_name']}*\n"
            f"Notifications: {notif}\n"
            f"Translate mode: {'on' if translate else 'off'}"
        )

    if cmd == "/quiet":
        if not user:
            return "You're not registered in Shogun. Ask Todd to add you."
        _set_notification(user["id"], False)
        return "Notifications silenced. I'll only respond when you message me directly."

    if cmd == "/active":
        if not user:
            return "You're not registered in Shogun. Ask Todd to add you."
        _set_notification(user["id"], True)
        return "Notifications active. I'll alert you when something relevant is nearby."

    if cmd == "/translate":
        if not user:
            return "You're not registered in Shogun. Ask Todd to add you."
        # /translate on|off|toggle
        parts = command.strip().lower().split()
        arg = parts[1] if len(parts) > 1 else None
        uid = user["telegram_user_id"]
        current = get_translate_mode(uid)
        if arg == "on" or (arg is None and not current):
            set_translate_mode(uid, True)
            return "Translate mode *on*. I'll translate Japanese↔English in every message."
        elif arg == "off" or (arg is None and current):
            set_translate_mode(uid, False)
            return "Translate mode *off*. Back to normal concierge mode."
        else:
            state = "on" if current else "off"
            return f"Translate mode is currently *{state}*. Use /translate on or /translate off."

    if cmd == "/reset":
        if user:
            clear_context(user["telegram_user_id"])
        return "Conversation memory cleared."

    if cmd == "/pois":
        if not user:
            return "You're not registered in Shogun. Ask Todd to add you."
        return _cmd_pois()

    if cmd == "/checklist":
        if not user:
            return "You're not registered in Shogun. Ask Todd to add you."
        return _cmd_checklist()

    if cmd == "/bug":
        if not user:
            return "You're not registered in Shogun. Ask Todd to add you."
        args = command.strip().split(maxsplit=1)
        if len(args) < 2 or not args[1].strip():
            return "Usage: /bug <describe the issue>\nExample: /bug AI is returning HTML instead of text"
        return _cmd_bug(args[1].strip(), user)

    if cmd == "/social":
        if not user:
            return "You're not registered in Shogun. Ask Todd to add you."
        args = command.strip().split(maxsplit=1)
        if len(args) >= 2 and args[1].strip():
            return _cmd_social_text(args[1].strip(), user)
        return _cmd_social_mode(user)

    return None  # Not a system command (or async — caller checks handle_async_command)


def _cmd_pois() -> str:
    """Return today's POIs for the current city."""
    from datetime import datetime, timezone, timedelta
    _JST = timezone(timedelta(hours=9))
    today_jst = datetime.now(_JST).strftime("%Y-%m-%d")
    city = db.get_city_for_date(today_jst)
    if not city:
        return "No city on record for today — are we still in transit?"
    pois = db.get_pois_by_city(city.lower())
    if not pois:
        return f"No POIs loaded for {city} yet."
    lines = [f"📍 *Key spots in {city}:*"]
    for poi in pois:
        name = poi["name_en"]
        ja = f" ({poi['name_ja']})" if poi.get("name_ja") else ""
        timing = poi.get("best_time_notes") or poi.get("crowd_notes") or ""
        note = f" — {timing[:80]}" if timing else ""
        lines.append(f"• {name}{ja}{note}")
    return "\n".join(lines)


def _cmd_checklist() -> str:
    """Return the packing checklist grouped by category."""
    items = db.get_checklist()
    if not items:
        return "Checklist is empty."
    by_cat: dict[str, list] = {}
    for item in items:
        by_cat.setdefault(item["category"], []).append(item)
    total = len(items)
    packed = sum(1 for i in items if i["packed"])
    lines = [f"🧳 *Packing checklist — {packed}/{total} packed:*"]
    for cat, cat_items in by_cat.items():
        lines.append(f"\n*{cat.capitalize()}*")
        for item in cat_items:
            tick = "✅" if item["packed"] else "⬜"
            note = f" _{item['notes']}_" if item.get("notes") else ""
            lines.append(f"{tick} {item['item_name']}{note}")
    return "\n".join(lines)


def _cmd_bug(description: str, user: dict) -> str:
    """Store a bug report with keyword-classified component and severity."""
    desc_lower = description.lower()

    component = "unknown"
    component_keywords = {
        "core": ["ai", "llm", "gemini", "response", "chat", "tool", "search", "location", "brief"],
        "web-ui": ["web", "page", "ui", "button", "display", "calendar", "dashboard", "frontend"],
        "web-api": ["api", "endpoint", "500", "error", "timeout", "backend"],
        "telegram": ["telegram", "bot", "command", "message", "photo", "voice"],
        "data": ["database", "db", "data", "poi", "knowledge", "itinerary", "missing"],
    }
    for comp, keywords in component_keywords.items():
        if any(kw in desc_lower for kw in keywords):
            component = comp
            break

    urgent_keywords = ["urgent", "broken", "crash", "down", "critical", "emergency", "blocked"]
    severity = "urgent" if any(kw in desc_lower for kw in urgent_keywords) else "normal"

    ai_summary = description[:500]

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO bug_reports
                   (reporter_id, telegram_user_id, raw_text, component, severity, ai_summary, status)
                   VALUES (%s, %s, %s, %s, %s, %s, 'open')
                   RETURNING id""",
                (user["id"], user["telegram_user_id"], description, component, severity, ai_summary),
            )
            bug_id = cur.fetchone()["id"]
        conn.commit()

        sev_icon = "\U0001f534" if severity == "urgent" else "\U0001f7e1"
        return (
            f"{sev_icon} Bug #{bug_id} reported\n"
            f"Component: {component}\n"
            f"Severity: {severity}\n"
            f"Status: open\n\n"
            f"Thanks {user['display_name']}, I've logged this."
        )
    except psycopg2.Error as exc:
        logger.error("Bug report insert failed: %s", exc)
        conn.rollback()
        return "Failed to record bug report. Please try again."
    finally:
        conn.close()


def _cmd_social_text(text: str, user: dict) -> str:
    """Save a text-only social note."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO social_notes
                   (user_id, telegram_user_id, note_type, text_content, city)
                   VALUES (%s, %s, 'text', %s, %s)
                   RETURNING id""",
                (user["id"], user["telegram_user_id"], text, _get_current_city()),
            )
            note_id = cur.fetchone()["id"]
        conn.commit()
        return f"\U0001f4dd Note #{note_id} saved! Send a location to tag it, or keep exploring."
    except psycopg2.Error as exc:
        logger.error("Social note insert failed: %s", exc)
        conn.rollback()
        return "Failed to save note. Please try again."
    finally:
        conn.close()


def _cmd_social_mode(user: dict) -> str:
    """Enter social capture mode — next photo/text gets saved."""
    set_social_mode(user["telegram_user_id"])
    return (
        "\U0001f4f8 *Social capture mode active* (5 minutes)\n\n"
        "Send me:\n"
        "\u2022 A photo (with optional caption)\n"
        "\u2022 A text note\n"
        "\u2022 A location to tag your last note\n\n"
        "I'll save everything to your trip journal."
    )


def _get_current_city() -> str | None:
    """Get the current city based on today's itinerary date."""
    from datetime import datetime, timezone, timedelta
    _JST = timezone(timedelta(hours=9))
    today_jst = datetime.now(_JST).strftime("%Y-%m-%d")
    return db.get_city_for_date(today_jst)


async def handle_async_command(command: str, user: dict | None) -> str | None:
    """
    Handle commands that require async execution.
    Returns reply_text if handled, None otherwise.
    text.py calls this after handle_command() returns None.
    """
    cmd = command.strip().lower().split()[0]

    if cmd == "/brief":
        if not user:
            return "You're not registered in Shogun. Ask Todd to add you."
        from app.services.brief import build_brief_text
        brief = await build_brief_text()
        return brief

    return None


def _set_notification(user_id: int, active: bool) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET notification_active = %s WHERE id = %s",
                (active, user_id),
            )
        conn.commit()
    except psycopg2.Error as exc:
        logger.error("Failed to update notification_active for user_id=%s: %s", user_id, exc)
        conn.rollback()
    finally:
        conn.close()
