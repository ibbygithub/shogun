# Frontend Fixes 2 — Evidence Report
**Date:** 2026-03-15
**Branch:** feature/20260315-ui-fixes-planning
**Build result:** PASS — TypeScript clean, `next build` 0 errors, container started successfully

---

## Fix 1: City page map (HIGHEST PRIORITY)

**Files changed:**
- `src/app/city/[slug]/page.tsx`

**What was done:**
- Added `import PoisMap from "@/components/pois/PoisMap"` to the city page.
- Changed `getCityData` to return ALL POIs for the city (previously sliced to 6 before return). The card grid still shows `.slice(0, 6)` but the map receives all POIs.
- Added a `mappablePois` filter (lat/lng non-null) to determine whether the map section renders.
- Added a "Places in {city}" section at the TOP of the page content (above the weather/blossom strip), using a CSS grid class `city-map-grid`:
  - Desktop (>767px): `grid-template-columns: 1fr 1fr` — POI cards left, map right (sticky).
  - Mobile (≤767px): `grid-template-columns: 1fr` — map ordered first (top), full width, Leaflet container height overridden to 350px.
- `PoisMap` passes `city={slug}` — `PoisMapInner` already has the full `ACCOMMODATION` record and red marker logic built in. No changes needed to PoisMap or PoisMapInner for this fix.

**Accommodation coordinates used by PoisMapInner (pre-existing, confirmed correct):**
| City | Lat | Lng | Label |
|------|-----|-----|-------|
| osaka | 34.7255 | 135.5185 | Tenjinbashi Queen Airbnb |
| kanazawa | 36.5613 | 136.6562 | Hotel Sanraku Kanazawa |
| tokyo | 35.7358 | 139.7283 | Sugamo Airbnb |
| nara | 34.6851 | 135.8048 | Nara Park (day trip) |

---

## Fix 2: Calendar pre-trip countdown

**Files changed:**
- `src/lib/types.ts` — added `UpcomingLeg` interface and `CalendarData` interface (shared type)
- `src/components/ambient/CalendarEvent.tsx` — rewritten to handle pre-trip state
- `src/components/ambient/AmbientDashboard.tsx` — local `CalendarData` interface extended; `showCalendar` condition updated

**What was done:**

### types.ts
Added two new exported types:
```typescript
interface UpcomingLeg { leg, title, city, date, notes }
interface CalendarData { date, event, note, is_holiday, error?, days_until_trip?, upcoming_legs? }
```

### CalendarEvent.tsx
- Now imports `CalendarData` from `@/lib/types` instead of defining it inline.
- Pre-trip branch: renders when `!data?.event && data?.days_until_trip > 0`. Shows indigo tile with "✈️ Japan in N days" heading and up to 3 upcoming legs formatted as "Mon Mar 23 — Title · notes".
- `formatDate()` helper: converts `"2026-03-23"` → `"Mon Mar 23"` using `toLocaleDateString`.
- During-trip branch: existing holiday/event display preserved unchanged.
- Fallback: returns `null` (no change from before for empty data).

### AmbientDashboard.tsx
- Local `CalendarData` interface now includes `days_until_trip?` and `upcoming_legs?` to match what the API will return.
- `showCalendar` replaces `hasCalendarEvent`: evaluates to true if `data?.calendar?.event` OR `data?.calendar?.days_until_trip > 0`.

---

## Fix 3: YouTube links — new tab direct

**Files changed:**
- `src/components/knowledge/KnowledgeDeepDive.tsx`

**What was done:**
- The YouTube "Watch on YouTube" `<button>` that called `setMediaViewer(...)` was replaced with an `<a>` tag.
- `href` points directly to `https://www.youtube.com/results?search_query=...`
- `target="_blank"` + `rel="noopener noreferrer"` — opens in new tab, no embedding attempted.
- Button text updated to "▶ Watch on YouTube ↗" to signal external link.
- Styling preserved: red background (`#ff0000`), white text, same padding/border-radius.
- `MediaViewer` import and state remain in place — still used by Google Maps (`data.booking_url`) and suggested search buttons.

---

## Fix 4: PoiCard "Save" button

**Files changed:**
- `src/components/pois/PoiCard.tsx`

**What was done:**
- Added `"use client"` directive — required for `useState`.
- Added `import { useState } from "react"` and `import { api } from "@/lib/api"`.
- Added `SaveState` type: `"idle" | "saving" | "saved" | "error"`.
- `handleSave` async function: calls `api.wishlist.create({ city, description: poi.name_en })`. Uses `e.preventDefault()` + `e.stopPropagation()` to prevent Link navigation triggering.
- State transitions: idle → saving → saved (2s auto-reset) | error (3s auto-reset).
- Button label by state: `"⭐ Save"` | `"…"` | `"✓ Saved"` | `"⚠ Failed"`.
- Button background/color shifts: green tint on saved, red tint on error.
- Button positioned at bottom-right of card using `justifyContent: "flex-end"`.
- All existing card markup (category badge, names, description, tags, best_time) preserved unchanged.

---

## Build verification

```
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Generating static pages (12/12)
Container shogun-web-ui Started
✓ Ready in 75ms
```

No TypeScript errors. No linting warnings.

---

## Files modified

| File | Change |
|------|--------|
| `src/app/city/[slug]/page.tsx` | Map section added at top of content, responsive grid layout |
| `src/lib/types.ts` | `UpcomingLeg` + `CalendarData` interfaces added |
| `src/components/ambient/CalendarEvent.tsx` | Pre-trip countdown view + shared type import |
| `src/components/ambient/AmbientDashboard.tsx` | Local CalendarData extended, showCalendar condition updated |
| `src/components/knowledge/KnowledgeDeepDive.tsx` | YouTube button → `<a target="_blank">` |
| `src/components/pois/PoiCard.tsx` | `"use client"` + Save button with save states |
