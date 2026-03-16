# Backend Fixes Validation Report
**Date:** 2026-03-15
**Branch:** feature/20260315-chatbot-fix-ai-enrichment-dashboard
**Scope:** shogun-web-api — chat.py, ambient.py, pois.py, models.py

---

## Summary

Three fixes applied and validated against the running `shogun-web-api` container (port 8090).

---

## Fix 1: Web chatbot POI knowledge injection (CRITICAL)

### Problem
`build_system_prompt()` in `chat.py` was hardcoded with no database data.
The LLM had no knowledge of the actual trip POIs and defaulted to generic
Tokyo sights (Shibuya, Meiji Jingu) instead of the user's dashboard
(Akihabara, Ghibli Museum, etc.).

### Changes
- Added `from db import get_conn` and `from datetime import date` imports to `chat.py`
- Added `_fetch_city_pois(city)` — queries `trip_pois WHERE city = %s ORDER BY name_en`
- Added `_fetch_today_itinerary()` — queries `trip_itinerary WHERE date_local = %s LIMIT 1`
- `build_system_prompt()` now calls both, builds a hard-delimited dashboard block:
  ```
  === YOUR DASHBOARD DATA — USE THIS, DO NOT SUBSTITUTE ===
  Today's itinerary: <title> — <notes_en>
  Top places shown on the <City> dashboard:
  1. Name (Category) — crowd_notes
  ...
  =======================================================
  ```
- Both DB helpers degrade gracefully (return `[]` / `None`) on any DB failure

### Test
```
POST http://localhost:8090/chat
{"message":"What are the top places on the Tokyo dashboard?","user_id":1}
```

### Result: PASS
LLM response enumerated the actual POIs from the database:
1. Akihabara Electric Town
2. Asakusa Senso-ji Temple
3. Ghibli Museum, Mitaka
4. Harajuku Takeshita Street
5. Ikebukuro — Animate, Pokemon Center, Jump Shop
6. Map Camera, Shinjuku

Generic Tokyo sights (Shibuya Crossing, Meiji Jingu) were NOT the primary
response — the chatbot answered from actual dashboard data.

### DB POI data confirmed
Full `trip_pois` table snapshot at time of test:
- kanazawa: 4 POIs
- kyoto: 5 POIs
- nara: 4 POIs
- osaka: 6 POIs
- sakai: 1 POI
- tokyo: 10 POIs (including Akihabara, Asakusa Senso-ji, Ghibli Museum,
  Harajuku Takeshita, Ikebukuro, Map Camera, Nakano Broadway,
  Shibuya Crossing, Shimokitazawa, Sugamo Jizo-dori)

---

## Fix 2: Calendar endpoint — trip itinerary enrichment

### Problem
`GET /api/ambient/calendar` returned only JP public holidays and spring events.
No trip itinerary data was included.

### Changes
- Added `from db import get_conn` import to `ambient.py`
- Added `_fetch_today_itinerary_for_calendar()` — queries
  `trip_itinerary WHERE date_local = %s ORDER BY leg_sequence LIMIT 1`
  Returns `{"leg", "title", "city", "notes"}` dict or `None`
- `_fetch_calendar()` now calls the helper and includes `"itinerary"` key
  in the returned dict alongside existing holiday fields

### Updated response shape
```json
{
  "date": "2026-03-25",
  "event": null,
  "note": null,
  "is_holiday": false,
  "itinerary": {
    "leg": 4,
    "title": "Nara day trip ...",
    "city": "Nara",
    "notes": "DEPART EARLY — arrive Nara before 9am..."
  }
}
```
`"itinerary": null` when no row for today. `"event": null` when no holiday.

### Test
```
GET http://localhost:8090/api/ambient/calendar
```

### Result: PASS
Today (2026-03-16) is pre-trip. Response:
```json
{
    "date": "2026-03-16",
    "event": null,
    "note": null,
    "is_holiday": false,
    "itinerary": null
}
```
`itinerary: null` is correct — no trip entries before 2026-03-23.
The `itinerary` field is present in the response shape as required.

DB itinerary data was confirmed to exist and be queryable.
First 5 itinerary entries verified (legs 1–5, starting 2026-03-23).
The fix will return real itinerary data from departure day onward.

---

## Fix 3: Expose lat/lng in POI API response

### Problem
`trip_pois` table has `lat` and `lng` columns. Both were fetched in the DB
query in `pois.py` and used to construct `map_url`, but not returned in the
API response. The frontend Leaflet map needed them.

### Changes
- `models.py`: Added `lat: Optional[float] = None` and `lng: Optional[float] = None`
  to the `Poi` Pydantic model
- `pois.py` `_row_to_poi()`: Added `lat=lat` and `lng=lng` to the `Poi(...)` constructor
  (`lat` and `lng` were already extracted on line 25 as `lat, lng = row[5], row[6]`)
- `map_url` construction unchanged

### Test
```
GET http://localhost:8090/pois?city=tokyo
```

### Result: PASS
All 10 Tokyo POIs returned with populated `lat`/`lng` fields.
Sample output (grep for lat/lng lines):
```
"lat": 35.6984,
"lng": 139.773,
"lat": 35.7148,
"lng": 139.7967,
... (10 POIs, all with non-null coordinates)
```

---

## Container State

- Build: successful (no errors, no warnings from Python)
- Startup: clean (`Application startup complete`)
- Pre-existing warning: collation version mismatch on shogun_v1 (not caused
  by these changes — present before and after)
- All three endpoints returning correct responses

---

## Files Changed

| File | Change |
|------|--------|
| `routers/chat.py` | Added DB imports; added `_fetch_city_pois()`, `_fetch_today_itinerary()`; rewrote `build_system_prompt()` to inject POI and itinerary data |
| `routers/ambient.py` | Added DB import; added `_fetch_today_itinerary_for_calendar()`; updated `_fetch_calendar()` to include `itinerary` key |
| `routers/pois.py` | Added `lat=lat, lng=lng` to `Poi()` constructor in `_row_to_poi()` |
| `models.py` | Added `lat: Optional[float] = None` and `lng: Optional[float] = None` to `Poi` model |
