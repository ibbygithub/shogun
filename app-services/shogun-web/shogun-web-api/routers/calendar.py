from fastapi import APIRouter, Request, Depends, HTTPException
from auth import get_current_user, require_edit, User
from db import get_conn
from models import ItineraryLeg, ItineraryLegCreate

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _row_to_leg(row) -> ItineraryLeg:
    return ItineraryLeg(
        id=row[0],
        leg_type=row[1],
        city=row[2],
        date_start=row[3],
        date_end=row[4],
        title=row[5],
        description=row[6],
        address_en=row[7],
        address_ja=row[8],
        confirmation_number=row[9],
        notes=row[10],
        status=row[11],
    )


@router.get("", response_model=list[ItineraryLeg])
def get_calendar(request: Request, user: User = Depends(get_current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, leg_type, city, date_start, date_end, title,
                       description, address_en, address_ja, confirmation_number,
                       notes, status
                FROM trip_itinerary
                ORDER BY date_start, id
                """
            )
            return [_row_to_leg(r) for r in cur.fetchall()]
