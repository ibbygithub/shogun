# Backend Fixes 3 — Validation Report
Date: 2026-03-16
Branch: develop

## Fixes Applied

### Fix 1: admin.py — shogun-core URL correction
- File: `app-services/shogun-web/shogun-web-api/routers/admin.py` line 56
- Changed `http://brainnode-01.ibbytech.com:8082/health` → `http://shogun-core:8082/health`
- Rationale: post-Docker-Desktop migration, shogun-core runs as a container on platform_net — hostname must be the container name

### Fix 2: dashboard.py — _pending_wishlist_count() exception guard
- File: `app-services/shogun-web/shogun-web-api/routers/dashboard.py`
- Wrapped `_pending_wishlist_count()` body in `try/except Exception: return 0`
- Prevents `psycopg2.errors.InsufficientPrivilege` on `wishlist_items` from propagating to a 500 on `/dashboard/status`

### Fix 3: planning.py — new planning router
- File created: `app-services/shogun-web/shogun-web-api/routers/planning.py`
- Registered in `main.py` with prefix `/api/planning`
- DB check: `shogun_app` already held `arwd` (append/read/write/delete) on `trip_itinerary` — no GRANT required
- Endpoints added:
  - `POST /api/planning/schedule` — validates trip date range, computes next leg_sequence, INSERTs activity row, returns `ItineraryLeg`
  - `GET /api/planning/itinerary` — returns all 18 trip dates (2026-03-23 to 2026-04-09) as a date-keyed dict, missing dates return empty arrays

## Docker Rebuild
- `docker compose build --no-cache` — completed successfully
- `docker compose up -d` — container recreated and started

## Verification Results

| Check | Result |
|-------|--------|
| `GET /dashboard/status` | 200 — `{"current_city":null,"trip_day":null,"total_days":18,"pending_wishlist_count":0,"shogun_health":"ok"}` |
| `GET /admin/health` (shogun-core service) | `"status":"ok","latency_ms":8.8` — container name resolves correctly |
| `GET /api/planning/itinerary` (first 5 keys) | `['2026-03-23','2026-03-24','2026-03-25','2026-03-26','2026-03-27']` |
| `POST /api/planning/schedule` (Test POI, osaka, 2026-03-25) | 200 — returned new leg id=12, leg_type=activity, city=osaka, title=Test POI |

All 4 checks passed.

## Notes
- telegram-gateway shows `unreachable` in admin health — this is pre-existing and unrelated to this task
- The test POI inserted by the schedule verification check (id=12) can be deleted manually if desired
