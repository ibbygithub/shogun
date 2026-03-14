from fastapi import APIRouter, Request, Depends, Query
from auth import get_current_user, User
from models import RemindersResponse, Reminder

router = APIRouter(prefix="/reminders", tags=["reminders"])

# Day-specific logistics reminders keyed by YYYY-MM-DD
TRIP_REMINDERS: dict[str, list[dict]] = {
    "2026-03-23": [
        {"type": "logistics", "icon": "✈️", "text": "Arrival day — Narita or Haneda. IC card (Suica/Pasmo) available at airport. Load ¥5,000–10,000."},
        {"type": "tip", "icon": "🚃", "text": "Narita Express (N'EX) to central Tokyo ~¥3,000. Limousine Bus is cheaper but slower."},
    ],
    "2026-04-01": [
        {"type": "logistics", "icon": "🦌", "text": "Nara — deer will bow if you bow first. Do not tease them. They bite."},
        {"type": "warning", "icon": "⚠️", "text": "Todaiji museum requires passport for foreign visitors. Bring passports."},
        {"type": "tip", "icon": "🦌", "text": "Deer crackers (shika senbei) sold outside for ¥200. Expect to be surrounded immediately."},
    ],
    "2026-04-03": [
        {"type": "logistics", "icon": "🚄", "text": "Osaka arrival — Shinkansen Nozomi from Nara via Shin-Osaka."},
        {"type": "tip", "icon": "🦪", "text": "Kuromon Ichiba Market — Osaka's kitchen. Morning is best for seafood."},
    ],
    "2026-04-06": [
        {"type": "logistics", "icon": "🚃", "text": "Osaka → Kyoto: Hankyu Railway ¥400 (30 min). Avoid shinkansen — overkill for this distance."},
    ],
    "2026-04-09": [
        {"type": "logistics", "icon": "✈️", "text": "Departure day. Kansai International Airport (KIX). Allow 2.5 hours minimum before flight."},
        {"type": "tip", "icon": "🎁", "text": "Last chance for omiyage (souvenir gifts) — best selection at KIX departures duty-free."},
    ],
}

GLOBAL_REMINDERS: list[dict] = [
    {"type": "tip", "icon": "🎫", "text": "Train tickets in Japan: sold outside the station, not inside. Buy before you enter the gate."},
    {"type": "tip", "icon": "💴", "text": "Many restaurants and smaller shops are cash-only. Keep ¥10,000–20,000 on hand."},
    {"type": "tip", "icon": "📱", "text": "7-Eleven ATMs accept foreign cards. Post Office ATMs also work internationally."},
    {"type": "warning", "icon": "⚠️", "text": "Eating while walking is considered rude in Kyoto and Nara. Stop and eat."},
    {"type": "tip", "icon": "🗑️", "text": "Almost no public trash cans in Japan. Keep a bag for your own trash."},
    {"type": "logistics", "icon": "👟", "text": "Slip-on shoes are strongly recommended. You will remove them at many temples and restaurants."},
]


@router.get("", response_model=RemindersResponse)
def get_reminders(
    request: Request,
    date: str | None = Query(None, description="YYYY-MM-DD"),
    user: User = Depends(get_current_user),
):
    date_items = []
    if date and date in TRIP_REMINDERS:
        date_items = [Reminder(**r) for r in TRIP_REMINDERS[date]]

    global_items = [Reminder(**r) for r in GLOBAL_REMINDERS]

    return RemindersResponse(date_reminders=date_items, global_reminders=global_items)
