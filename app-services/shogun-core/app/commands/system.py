"""
System commands: /quiet, /active, /status, /help, /reset
These modify user state in the DB or Valkey and return a direct reply_text.
"""
import logging
import psycopg2
from app.db import get_connection
from app.valkey_client import clear_context

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
            "/status — show your current settings\n"
            "/reset — clear conversation memory\n"
            "/help — this message"
        )

    if cmd == "/status":
        if not user:
            return "You're not registered in Shogun yet. Ask Todd to add you."
        notif = "active" if user["notification_active"] else "quiet"
        return (
            f"*{user['display_name']}* — notifications: {notif}\n"
            f"Language: {user.get('language_preference', 'en')}"
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
