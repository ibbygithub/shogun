# Backend Fixes 2 — Validation Report
**Date:** 2026-03-15
**Branch:** feature/20260315-ui-fixes-planning
**Files changed:**
- `app-services/shogun-web/shogun-web-api/routers/dashboard.py`
- `app-services/shogun-web/shogun-web-api/routers/ambient.py`

---

## Fix 1: shogun-core health check URL

### Problem
`_shogun_core_health()` in `dashboard.py` called `http://brainnode-01.ibbytech.com:8082/health`.
After Docker Desktop migration, shogun-core is a container on `platform_net`, not a systemd service on brainnode-01.

### Discovery
- `docker inspect shogun-core` → internal port `8082/tcp`, network `platform_net`
- `docker inspect shogun-web-api` → network `platform_net` (same network, DNS resolution by container name confirmed)
- `docker exec shogun-core python -c "...app.routes..."` → `/health` endpoint exists, returns `{"ok":true,"service":"shogun-core","version":"0.4.0"}`

### Fix applied
`dashboard.py` line 40: URL changed from `http://brainnode-01.ibbytech.com:8082/health` to `http://shogun-core:8082/health`.

### Test result
```
docker exec shogun-web-api python -c "import httpx; resp = httpx.get('http://shogun-core:8082/health', timeout=3.0); print(resp.status_code, resp.text)"
# → 200  {"ok":true,"service":"shogun-core","version":"0.4.0"}
```

The `GET /dashboard/status` endpoint returns HTTP 500 due to a pre-existing `permission denied for table wishlist_items` error in `_pending_wishlist_count()`. This is unrelated to the health check fix and was present before this change. The health check function itself resolves correctly — confirmed by direct container exec.

---

## Fix 2: Calendar — upcoming trip legs pre-trip

### Problem
`_fetch_calendar()` returned `{"event": null, "itinerary": null}` before trip start (2026-03-23). No pre-trip content for the calendar tile.

### Discovery
`trip_itinerary` columns confirmed via `information_schema.columns`:
`id, leg_sequence, leg_type, date_local, city, title, address_en, address_ja, contact_phone, confirmation_number, notes_en, notes_ja, start_time, end_time, created_utc`

Note: task spec used `leg_number`, `start_date`, `notes` — corrected to actual column names `leg_sequence`, `date_local`, `notes_en`.

### Fix applied
`ambient.py`:
- Added `_fetch_upcoming_legs(limit=3)` — queries `trip_itinerary` for rows with `date_local >= today`, ordered by `date_local, leg_sequence`, returns up to `limit` rows.
- Extended `_fetch_calendar()` to call `_fetch_upcoming_legs(3)` and add `upcoming_legs` and `days_until_trip` to the response dict.

### Test result
```
curl http://localhost:8090/api/ambient/calendar
```
Response (2026-03-16, 7 days before trip):
```json
{
  "date": "2026-03-16",
  "event": null,
  "note": null,
  "is_holiday": false,
  "itinerary": null,
  "upcoming_legs": [
    {"leg": 1, "title": "JL7555 SFO → LAX", "city": "San Francisco", "date": "2026-03-23", "notes": "..."},
    {"leg": 2, "title": "JL69 LAX → KIX (Kansai International)", "city": "Los Angeles", "date": "2026-03-23", "notes": "..."},
    {"leg": 3, "title": "Tenjinbashi Queen Airbnb — check in", "city": "Osaka", "date": "2026-03-24", "notes": "..."}
  ],
  "days_until_trip": 7
}
```

`days_until_trip` = 7 (correct for 2026-03-16 → 2026-03-23).
`upcoming_legs` = 3 entries starting from trip day 1.

---

## Pre-existing issue noted (out of scope)
`GET /dashboard/status` returns 500 due to `permission denied for table wishlist_items` in `_pending_wishlist_count()`. This is unrelated to both fixes in this task and was present before these changes.
