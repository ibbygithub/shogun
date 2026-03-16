# Frontend Fixes 3 — Validation Report
Date: 2026-03-16
Branch: develop

## Summary

All 6 fixes applied, container rebuilt and verified.

---

## Fix 1: Calendar tile city colors

**File:** `src/components/calendar/CalendarGrid.tsx`

- Added `cityForDate(key)` function mapping trip dates to cities:
  - Mar 23 → travel
  - Mar 24–29 → osaka
  - Mar 30–31 → kanazawa
  - Apr 1–9 → tokyo
- Added `CITY_BG` and `CITY_LABEL` constants
- All tile backgrounds now use `CITY_BG[cityForDate(key)]` instead of `"white"`
- Free-day tiles now show city label (e.g. "🏯 Osaka") in italic grey instead of "Free day"
- Days with legs retain the city color background

**Status:** PASS

---

## Fix 2: Temperature — F primary, C secondary

**Files:**
- `src/components/ambient/WeatherCard.tsx`
- `src/components/widgets/WeatherWidget.tsx`

Both files updated with `toF(c)` helper:
- Current temp: `{toF(temp_c)}°F` large, `{Math.round(temp_c)}°C` smaller below
- High/low: `↑{toF(temp_max)}°F ↓{toF(temp_min)}°F`
- Forecast strip tiles: `{toF(max)}°F` main, `{toF(min)}°F` secondary

**Status:** PASS

---

## Fix 3: Blossom widget — live ambient sakura data

**File:** `src/components/widgets/BlossomWidget.tsx`

- Removed static `/blossom` endpoint dependency
- Now fetches `api.ambient.sakura("osaka")` and `api.ambient.sakura("tokyo")` via useEffect
- Shows two `SakuraStatus` cards side-by-side (stacked on mobile <600px)
- Header updated to "🌸 Cherry Blossom Forecast 2026"

**Status:** PASS

---

## Fix 4: City page blossom section — live ambient sakura

**Files:**
- `src/components/city/CityBlossomSection.tsx` (new client component)
- `src/app/city/[slug]/page.tsx`

- Created `CityBlossomSection` — a client component that fetches `api.ambient.sakura(slug)` and passes to `SakuraStatus`
- City page (server component) now renders `<CityBlossomSection slug={slug} />` instead of static blossom data
- Removed `api.blossom.list()` call from `getCityData()`
- Removed unused `BlossomEntry` type import

**Status:** PASS

---

## Fix 5: Planning page

**File:** `src/app/planning/page.tsx` (new)

- "use client" page with two-panel layout
- Left panel (40%): POI browser
  - Fetches `api.pois.list()` — all POIs
  - Grouped by city with city color backgrounds and labels
  - City filter dropdown
  - Category icons per POI
  - "📅 Schedule" button opens schedule modal
- Right panel (60%): Trip timeline
  - All 18 trip days (Mar 23–Apr 9)
  - City color background per day
  - City badge label
  - Current legs listed from itinerary
  - "+" button for quick-add (opens modal filtered to day city)
- Schedule modal:
  - POI name shown
  - Date select with all 18 trip days formatted as "Mon Mar 23 (🏯 Osaka)"
  - Calls `POST /api/planning/schedule`
  - Error handling if backend not yet available
  - Success message with auto-close after 1.2s, then re-fetches itinerary
- Itinerary fallback: if `/planning/itinerary` fails, falls back to `api.itinerary.list()` grouped by `date_start`
- Added `api.planning` methods to `src/lib/api.ts`

**Status:** PASS

---

## Fix 6: Planning navigation

**Files:**
- `src/components/layout/Sidebar.tsx`
- `src/components/layout/MobileTabBar.tsx`

- Sidebar: "Planning" with 📋 icon added between Calendar and Itinerary
- MobileTabBar: "Planning" with 📋 icon added (replaced Wishlist to keep 5 tabs)

**Status:** PASS

---

## Build Verification

```
docker compose build --no-cache  → SUCCESS (0 errors, 0 type errors)
docker compose up -d              → Container started
curl http://localhost:3010/       → HTTP 307 (redirect to /dashboard — expected)
docker logs shogun-web-ui         → "✓ Ready in 68ms" — no errors
```

Build output confirmed all 13 routes including `/planning` (4.19 kB).

---

## Files Changed

| File | Action |
|------|--------|
| `src/components/calendar/CalendarGrid.tsx` | Modified |
| `src/components/ambient/WeatherCard.tsx` | Modified |
| `src/components/widgets/WeatherWidget.tsx` | Modified |
| `src/components/widgets/BlossomWidget.tsx` | Modified |
| `src/components/city/CityBlossomSection.tsx` | Created |
| `src/app/city/[slug]/page.tsx` | Modified |
| `src/app/planning/page.tsx` | Created |
| `src/components/layout/Sidebar.tsx` | Modified |
| `src/components/layout/MobileTabBar.tsx` | Modified |
| `src/lib/api.ts` | Modified (added planning endpoints) |

---

## Notes

- The `POST /api/planning/schedule` backend endpoint is being built in parallel.
  The planning page has full error handling — failures show an inline error message
  and do not crash the UI.
- The `/planning/itinerary` GET endpoint falls back to `api.itinerary.list()` if unavailable.
- No hardcoded ports or credentials introduced. All API calls use the `api` client.
