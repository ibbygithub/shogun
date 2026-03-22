from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date
from collections import defaultdict

from auth import get_current_user, User
from db import get_conn
from models import ItineraryLeg

router = APIRouter(prefix="/api/planning", tags=["planning"])

TRIP_START = date(2026, 3, 23)
TRIP_END = date(2026, 4, 9)
ALL_TRIP_DATES = [
    (TRIP_START.replace(day=TRIP_START.day) + __import__('datetime').timedelta(days=i)).isoformat()
    for i in range((TRIP_END - TRIP_START).days + 1)
]


class ScheduleRequest(BaseModel):
    date: date
    poi_name: str
    city: str
    notes: Optional[str] = ""
    poi_id: Optional[int] = None


def _row_to_leg(row) -> ItineraryLeg:
    """Map a trip_itinerary DB row to ItineraryLeg.
    Column order: id, leg_type, city, date_local, title,
                  notes_en, address_en, address_ja, confirmation_number, notes_ja, trip_poi_id
    """
    return ItineraryLeg(
        id=row[0],
        leg_type=row[1],
        city=row[2],
        date_start=row[3],
        date_end=None,
        title=row[4],
        description=row[5],      # notes_en
        address_en=row[6],
        address_ja=row[7],
        confirmation_number=row[8],
        notes=row[9],             # notes_ja
        status=None,
        trip_poi_id=row[10] if len(row) > 10 else None,
    )


@router.post("/schedule", response_model=ItineraryLeg)
def schedule_poi(
    body: ScheduleRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    # Validate date is within trip range
    if body.date < TRIP_START or body.date > TRIP_END:
        raise HTTPException(
            status_code=400,
            detail=f"Date {body.date} is outside the trip range "
                   f"{TRIP_START.isoformat()} to {TRIP_END.isoformat()}",
        )

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Determine next leg_sequence for this date
            cur.execute(
                "SELECT MAX(leg_sequence) FROM trip_itinerary WHERE date_local = %s",
                (body.date,),
            )
            row = cur.fetchone()
            max_seq = row[0] if row and row[0] is not None else None
            # If no legs exist for this date, start at 10; otherwise increment by 1
            leg_sequence = (max_seq + 1) if max_seq is not None else 10

            notes_en = body.notes if body.notes else None

            # Resolve POI ID: use provided ID, or look up by exact name match
            poi_id = body.poi_id
            if not poi_id:
                cur.execute(
                    "SELECT id FROM trip_pois WHERE name_en = %s LIMIT 1",
                    (body.poi_name,),
                )
                match = cur.fetchone()
                if match:
                    poi_id = match[0]

            cur.execute(
                """
                INSERT INTO trip_itinerary
                    (leg_type, date_local, city, title, notes_en, leg_sequence, trip_poi_id)
                VALUES
                    ('activity', %s, %s, %s, %s, %s, %s)
                RETURNING id, leg_type, city, date_local, title,
                          notes_en, address_en, address_ja, confirmation_number, notes_ja,
                          trip_poi_id
                """,
                (body.date, body.city, body.poi_name, notes_en, leg_sequence, poi_id),
            )
            new_row = cur.fetchone()
        conn.commit()

    return _row_to_leg(new_row)


@router.get("/itinerary")
def get_planning_itinerary(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Return all 18 trip days as a dict keyed by ISO date string.
    Missing dates return an empty list.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, leg_type, city, date_local, title,
                       notes_en, address_en, address_ja, confirmation_number, notes_ja,
                       trip_poi_id
                FROM trip_itinerary
                ORDER BY date_local, leg_sequence
                """
            )
            rows = cur.fetchall()

    # Group rows by date
    by_date: dict[str, list] = defaultdict(list)
    for row in rows:
        leg = _row_to_leg(row)
        key = leg.date_start.isoformat() if leg.date_start else "unknown"
        by_date[key].append(leg)

    # Build result with all 18 trip dates present (empty list for missing days)
    result = {d: by_date.get(d, []) for d in ALL_TRIP_DATES}
    return result
