# Validation Report — Budget Tracker API & Reservation Tracking

**Date:** 2026-03-16
**Branch:** develop
**Scope:** Budget tracker API (new), reservation tracking columns on wishlist, DB schema updates

---

## Tasks Completed

### Task 1: budget_items table
- Created `budget_items` table in `shogun_v1` with columns: id, trip_date, category, description, amount_jpy, created_utc
- Granted SELECT, INSERT, UPDATE, DELETE to `shogun_app`
- Granted USAGE, SELECT on `budget_items_id_seq` to `shogun_app`

### Task 2: wishlist_items reservation columns
- Added `category VARCHAR(30) DEFAULT 'general'`
- Added `needs_reservation BOOLEAN NOT NULL DEFAULT FALSE`
- Added `reservation_confirmed BOOLEAN NOT NULL DEFAULT FALSE`
- Pre-existing bug discovered and fixed: `wishlist_items` had no grants to `shogun_app` (table existed without privileges). Grants applied: SELECT, INSERT, UPDATE, DELETE on table; USAGE, SELECT on sequence.

### Task 3: routers/budget.py
- New router at `/api/budget` (prefix), tags: budget
- GET `/api/budget` — returns items list, total_jpy, by_category breakdown
- POST `/api/budget` — create item, validates category (enum) and amount_jpy >= 0
- DELETE `/api/budget/{item_id}` — delete by id
- Valid categories: accommodation, activity, food, other, shopping, transport

### Task 4: routers/wishlist.py updates
- GET endpoint updated to select `category, needs_reservation, reservation_confirmed` (columns 10/11/12)
- `_row_to_item` updated to map new columns from result row
- Added `PATCH /{item_id}/reservation` — toggles `needs_reservation`
- Added `PATCH /{item_id}/reservation-confirmed` — toggles `reservation_confirmed`

### Task 5: models.py
- `WishlistItem` extended with `category: Optional[str] = "general"`, `needs_reservation: bool = False`, `reservation_confirmed: bool = False`

### Task 6: main.py
- Imported `budget as budget_router` from routers
- Registered `budget_router.router` via `app.include_router`

---

## Verification Results

| Check | Result |
|-------|--------|
| GET /api/budget (empty) | `{"items":[],"total_jpy":0,"by_category":{}}` |
| POST /api/budget (food, 1200 JPY) | Returns item with id=1, correct fields |
| GET /api/budget (with item) | total_jpy=1200, by_category={"food":1200} |
| DELETE /api/budget/1 | `{"ok":true}` |
| GET /api/budget (after delete) | Empty, total_jpy=0 |
| POST with invalid category | 400: category must be one of [...] |
| POST with negative amount | 400: amount_jpy must be >= 0 |
| GET /wishlist | 200, returns [] (privileges fixed) |

---

## Notes

- Collation version mismatch warning in postgres (2.41 vs 2.36) — pre-existing, cosmetic, no functional impact
- wishlist_items privilege gap was pre-existing; grants applied as part of this session
- Image rebuilt with `--no-cache`; container confirmed running on port 8090
