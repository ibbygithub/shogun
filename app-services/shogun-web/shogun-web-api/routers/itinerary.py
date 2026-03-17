from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
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
def get_itinerary(
    request: Request,
    user: User = Depends(get_current_user),
    city: Optional[str] = None,
    date: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    clauses: list[str] = []
    params: list = []
    if city:
        clauses.append("LOWER(city) = %s")
        params.append(city.lower())
    if date:
        clauses.append("date_local = %s")
        params.append(date)
    if date_from:
        clauses.append("date_local >= %s")
        params.append(date_from)
    if date_to:
        clauses.append("date_local <= %s")
        params.append(date_to)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, leg_type, city, date_local, title,
                       notes_en, address_en, address_ja, confirmation_number, notes_ja
                FROM trip_itinerary
                {where}
                ORDER BY date_local, leg_sequence
                """,
                params,
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
                  (leg_sequence, leg_type, city, date_local, title, notes_en,
                   address_en, address_ja, confirmation_number, notes_ja)
                VALUES (
                  (SELECT COALESCE(MAX(leg_sequence), 0) + 1 FROM trip_itinerary),
                  %s,%s,%s,%s,%s,%s,%s,%s,%s
                )
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


class LegPatch(BaseModel):
    """Partial update model — only provided fields are written to the DB."""
    title: Optional[str] = None
    notes_en: Optional[str] = None
    notes_ja: Optional[str] = None
    date_local: Optional[str] = None
    leg_type: Optional[str] = None
    city: Optional[str] = None
    address_en: Optional[str] = None
    address_ja: Optional[str] = None
    confirmation_number: Optional[str] = None


@router.patch("/{leg_id}", response_model=ItineraryLeg)
def patch_leg(leg_id: int, body: LegPatch, request: Request, user: User = Depends(get_current_user)):
    """Partial update of a trip itinerary leg. Only provided fields are changed."""
    field_map = {
        "title": "title",
        "notes_en": "notes_en",
        "notes_ja": "notes_ja",
        "date_local": "date_local",
        "leg_type": "leg_type",
        "city": "city",
        "address_en": "address_en",
        "address_ja": "address_ja",
        "confirmation_number": "confirmation_number",
    }

    updates: list[tuple[str, object]] = []
    for field_name, col_name in field_map.items():
        val = getattr(body, field_name, None)
        if val is not None:
            updates.append((col_name, val))

    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    set_clause = ", ".join(f"{col} = %s" for col, _ in updates)
    values = [v for _, v in updates] + [leg_id]

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE trip_itinerary
                SET {set_clause}
                WHERE id = %s
                RETURNING id, leg_type, city, date_local, title,
                          notes_en, address_en, address_ja, confirmation_number, notes_ja
                """,
                values,
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
            cur.execute(
                """DELETE FROM trip_itinerary WHERE id=%s
                   RETURNING id, leg_type, city, date_local, title,
                             notes_en, address_en, address_ja, confirmation_number, notes_ja""",
                (leg_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Leg not found")
            return {"deleted": leg_id, "leg": _row_to_leg(row).model_dump()}
