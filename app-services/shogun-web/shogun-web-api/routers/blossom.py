from fastapi import APIRouter, Request, Depends
from datetime import date
from auth import get_current_user, User
from models import BlossomEntry

router = APIRouter(prefix="/blossom", tags=["blossom"])

# 2026 cherry blossom forecast — status computed dynamically from today vs peak
_BLOSSOM_SEED = [
    {"city": "tokyo",  "spot": "Shinjuku Gyoen",    "peak_date": "2026-03-28", "notes": "Best viewing in the Japanese Garden section."},
    {"city": "nara",   "spot": "Nara Park",          "peak_date": "2026-04-01", "notes": "Deer + blossoms. Go early morning before tour buses."},
    {"city": "osaka",  "spot": "Osaka Castle Park",  "peak_date": "2026-04-02", "notes": "1,200 cherry trees surrounding the castle moat."},
    {"city": "kyoto",  "spot": "Maruyama Park",      "peak_date": "2026-04-03", "notes": "The weeping cherry (shidarezakura) is the icon of Kyoto spring."},
]


def _compute_status(peak_date_str: str) -> str:
    peak = date.fromisoformat(peak_date_str)
    today = date.today()
    delta = (today - peak).days
    if delta < -7:
        return "not_started"
    elif delta < -2:
        return "early"
    elif delta <= 4:
        return "peak"
    elif delta <= 10:
        return "late"
    else:
        return "finished"


@router.get("", response_model=list[BlossomEntry])
def get_blossom(request: Request, user: User = Depends(get_current_user)):
    return [
        BlossomEntry(
            city=b["city"],
            spot=b["spot"],
            status=_compute_status(b["peak_date"]),
            peak_date=b["peak_date"],
            notes=b.get("notes"),
        )
        for b in _BLOSSOM_SEED
    ]
