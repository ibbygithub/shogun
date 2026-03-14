from fastapi import APIRouter, Request, Depends, HTTPException
from auth import get_current_user, require_edit, User
from db import get_conn
from models import ItineraryLeg, ItineraryLegCreate

router = APIRouter(prefix="/itinerary", tags=["itinerary"])


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
def get_itinerary(request: Request, user: User = Depends(get_current_user)):
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


@router.post("", response_model=ItineraryLeg)
def add_leg(body: ItineraryLegCreate, request: Request, user: User = Depends(get_current_user)):
    require_edit(user)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO trip_itinerary
                  (leg_type, city, date_local, title, notes_en,
                   address_en, address_ja, confirmation_number, notes_ja)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id, leg_type, city, date_local, title,
                          notes_en, address_en, address_ja, confirmation_number, notes_ja
                """,
                (
                    body.leg_type, body.city, body.date_start,
                    body.title, body.description, body.address_en, body.address_ja,
                    body.confirmation_number, body.notes,
                ),
            )
            return _row_to_leg(cur.fetchone())


@router.put("/{leg_id}", response_model=ItineraryLeg)
def update_leg(leg_id: int, body: ItineraryLegCreate, request: Request, user: User = Depends(get_current_user)):
    require_edit(user)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE trip_itinerary
                SET leg_type=%s, city=%s, date_local=%s, title=%s, notes_en=%s,
                    address_en=%s, address_ja=%s, confirmation_number=%s, notes_ja=%s
                WHERE id=%s
                RETURNING id, leg_type, city, date_local, title,
                          notes_en, address_en, address_ja, confirmation_number, notes_ja
                """,
                (
                    body.leg_type, body.city, body.date_start,
                    body.title, body.description, body.address_en, body.address_ja,
                    body.confirmation_number, body.notes, leg_id,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Leg not found")
            return _row_to_leg(row)


@router.delete("/{leg_id}")
def delete_leg(leg_id: int, request: Request, user: User = Depends(get_current_user)):
    require_edit(user)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM trip_itinerary WHERE id=%s RETURNING id", (leg_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Leg not found")
    return {"deleted": leg_id}
