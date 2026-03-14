from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
from auth import get_current_user, require_admin, User
from db import get_conn

router = APIRouter(prefix="/settings", tags=["settings"])

# user_preferences actual columns: id, user_id, category, preference_key, preference_value, notes, created_utc
# users actual columns: id, telegram_user_id, display_name, full_name, notification_active, language_preference, created_utc


class PreferenceUpdate(BaseModel):
    preference_type: str    # maps to preference_key
    preference_value: str


@router.get("/preferences")
def get_preferences(request: Request, user: User = Depends(get_current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT preference_key, preference_value FROM user_preferences WHERE user_id=%s",
                (user.id,),
            )
            return {row[0]: row[1] for row in cur.fetchall()}


@router.put("/preferences")
def set_preference(body: PreferenceUpdate, request: Request, user: User = Depends(get_current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM user_preferences WHERE user_id=%s AND preference_key=%s",
                (user.id, body.preference_type),
            )
            cur.execute(
                """
                INSERT INTO user_preferences (user_id, category, preference_key, preference_value)
                VALUES (%s, 'dietary', %s, %s)
                """,
                (user.id, body.preference_type, body.preference_value),
            )
    return {"updated": body.preference_type}


@router.get("/users")
def list_users(request: Request, user: User = Depends(get_current_user)):
    require_admin(user)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, display_name, full_name, telegram_user_id FROM users ORDER BY id"
            )
            return [
                {"id": r[0], "name": r[1] or r[2], "telegram_user_id": r[3], "role": "admin"}
                for r in cur.fetchall()
            ]
