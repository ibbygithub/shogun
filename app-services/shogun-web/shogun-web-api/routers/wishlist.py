from fastapi import APIRouter, Request, Depends, HTTPException
from auth import get_current_user, require_edit, User
from db import get_conn
from models import WishlistItem, WishlistCreate, WishlistApprove
from datetime import datetime, timezone

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


def _row_to_item(row) -> WishlistItem:
    return WishlistItem(
        id=row[0],
        requested_by=row[1],
        city=row[2],
        description=row[3],
        ai_research=row[4],
        status=row[5],
        reviewed_by=row[6],
        reviewed_at=row[7],
        itinerary_note=row[8],
        created_utc=row[9],
    )


@router.get("", response_model=list[WishlistItem])
def get_wishlist(request: Request, user: User = Depends(get_current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            if user.role == "admin":
                cur.execute(
                    """
                    SELECT id, requested_by, city, description, ai_research,
                           status, reviewed_by, reviewed_at, itinerary_note, created_utc
                    FROM wishlist_items ORDER BY created_utc DESC
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT id, requested_by, city, description, ai_research,
                           status, reviewed_by, reviewed_at, itinerary_note, created_utc
                    FROM wishlist_items WHERE requested_by=%s ORDER BY created_utc DESC
                    """,
                    (user.id,),
                )
            return [_row_to_item(r) for r in cur.fetchall()]


@router.post("", response_model=WishlistItem)
def create_wishlist_item(body: WishlistCreate, request: Request, user: User = Depends(get_current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO wishlist_items (requested_by, city, description)
                VALUES (%s, %s, %s)
                RETURNING id, requested_by, city, description, ai_research,
                          status, reviewed_by, reviewed_at, itinerary_note, created_utc
                """,
                (user.id, body.city, body.description),
            )
            return _row_to_item(cur.fetchone())


@router.put("/{item_id}/approve")
def approve_item(item_id: int, body: WishlistApprove, request: Request, user: User = Depends(get_current_user)):
    require_edit(user)
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE wishlist_items
                SET status='approved', reviewed_by=%s, reviewed_at=%s, itinerary_note=%s
                WHERE id=%s RETURNING id
                """,
                (user.id, now, body.itinerary_note, item_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Item not found")
    return {"approved": item_id}


@router.put("/{item_id}/reject")
def reject_item(item_id: int, request: Request, user: User = Depends(get_current_user)):
    require_edit(user)
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE wishlist_items
                SET status='rejected', reviewed_by=%s, reviewed_at=%s
                WHERE id=%s RETURNING id
                """,
                (user.id, now, item_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Item not found")
    return {"rejected": item_id}
