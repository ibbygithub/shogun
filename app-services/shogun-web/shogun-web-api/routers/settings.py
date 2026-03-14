from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
from auth import get_current_user, require_admin, User
from db import get_conn

router = APIRouter(prefix="/settings", tags=["settings"])


class PreferenceUpdate(BaseModel):
    preference_type: str
    preference_value: str


@router.get("/preferences")
def get_preferences(request: Request, user: User = Depends(get_current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT preference_type, preference_value FROM user_preferences WHERE user_id=%s",
                (user.id,),
            )
            return {row[0]: row[1] for row in cur.fetchall()}


@router.put("/preferences")
def set_preference(body: PreferenceUpdate, request: Request, user: User = Depends(get_current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_preferences (user_id, preference_type, preference_value)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, preference_type)
                DO UPDATE SET preference_value=EXCLUDED.preference_value
                """,
                (user.id, body.preference_type, body.preference_value),
            )
    return {"updated": body.preference_type}


@router.get("/users")
def list_users(request: Request, user: User = Depends(get_current_user)):
    require_admin(user)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, email, role FROM users ORDER BY id")
            return [
                {"id": r[0], "name": r[1], "email": r[2], "role": r[3]}
                for r in cur.fetchall()
            ]
