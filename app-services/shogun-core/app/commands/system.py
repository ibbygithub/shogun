"""
System commands: /quiet, /active, /status, /help, /reset, /translate
These modify user state in the DB or Valkey and return a direct reply_text.
"""
import logging
import psycopg2
from app.db import get_connection
from app.valkey_client import clear_context, get_translate_mode, set_translate_mode

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

    return None  # Not a system command


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
