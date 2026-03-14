from fastapi import APIRouter, Request, Depends
from auth import get_current_user, User
from db import get_conn
from models import ItineraryLeg

router = APIRouter(prefix="/calendar", tags=["calendar"])

# Actual DB columns: id, leg_sequence, leg_type, date_local, city, title,
#   address_en, address_ja, contact_phone, confirmation_number, notes_en, notes_ja,
#   start_time, end_time, created_utc
# API mapping: date_local→date_start, notes_en→description, notes_ja→notes, date_end=None, status=None


def _row_to_leg(row) -> ItineraryLeg:
    return ItineraryLeg(
        id=row[0],
        leg_type=row[1],
        city=row[2],
        date_start=row[3],      # date_local
        date_end=None,
        title=row[4],
        description=row[5],     # notes_en
        address_en=row[6],
        address_ja=row[7],
        confirmation_number=row[8],
        notes=row[9],           # notes_ja
        status=None,
    )


@router.get("", response_model=list[ItineraryLeg])
def get_calendar(request: Request, user: User = Depends(get_current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, leg_type, city, date_local, title,
                       notes_en, address_en, address_ja, confirmation_number, notes_ja
                FROM trip_itinerary
                ORDER BY date_local, leg_sequence
                """
            )
            return [_row_to_leg(r) for r in cur.fetchall()]
