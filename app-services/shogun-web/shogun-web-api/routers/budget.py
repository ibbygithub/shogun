from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Optional
from datetime import date
from pydantic import BaseModel
from auth import get_current_user, User
from db import get_conn

router = APIRouter(prefix="/api/budget", tags=["budget"])

VALID_CATEGORIES = {"food", "transport", "accommodation", "activity", "shopping", "other"}


class BudgetItemCreate(BaseModel):
    trip_date: Optional[date] = None
    category: str = "other"
    description: str
    amount_jpy: int


class BudgetItem(BaseModel):
    id: int
    trip_date: Optional[date]
    category: str
    description: str
    amount_jpy: int
    created_utc: str


@router.get("", response_model=dict)
def get_budget(request: Request, user: User = Depends(get_current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, trip_date, category, description, amount_jpy, created_utc FROM budget_items ORDER BY trip_date NULLS LAST, created_utc"
            )
            rows = cur.fetchall()
    items = [
        {"id": r[0], "trip_date": r[1].isoformat() if r[1] else None,
         "category": r[2], "description": r[3], "amount_jpy": r[4],
         "created_utc": r[5].isoformat()}
        for r in rows
    ]
    total = sum(i["amount_jpy"] for i in items)
    by_category = {}
    for i in items:
        by_category[i["category"]] = by_category.get(i["category"], 0) + i["amount_jpy"]
    return {"items": items, "total_jpy": total, "by_category": by_category}


@router.post("", response_model=BudgetItem)
def add_budget_item(body: BudgetItemCreate, request: Request, user: User = Depends(get_current_user)):
    if body.category not in VALID_CATEGORIES:
        raise HTTPException(400, f"category must be one of {sorted(VALID_CATEGORIES)}")
    if body.amount_jpy < 0:
        raise HTTPException(400, "amount_jpy must be >= 0")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO budget_items (trip_date, category, description, amount_jpy) VALUES (%s, %s, %s, %s) RETURNING id, trip_date, category, description, amount_jpy, created_utc",
                (body.trip_date, body.category, body.description, body.amount_jpy)
            )
            r = cur.fetchone()
            conn.commit()
    return {"id": r[0], "trip_date": r[1].isoformat() if r[1] else None,
            "category": r[2], "description": r[3], "amount_jpy": r[4], "created_utc": r[5].isoformat()}


@router.delete("/{item_id}")
def delete_budget_item(item_id: int, request: Request, user: User = Depends(get_current_user)):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM budget_items WHERE id = %s", (item_id,))
            conn.commit()
    return {"ok": True}
