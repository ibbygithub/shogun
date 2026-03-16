# Frontend Fixes Validation Report
Date: 2026-03-15
Branch: feature/20260315-chatbot-fix-ai-enrichment-dashboard
Build: PASS — zero TypeScript errors, zero lint errors

---

## Environment

| Container | Port | Status |
|-----------|------|--------|
| shogun-web-ui | 3010→3000 | Running — rebuilt and started |
| shogun-web-api | 8090 | Running |

---

## Fix 1: Ambient Dashboard Data (CRITICAL) — FIXED

**Root cause confirmed:** The ambient API routes on shogun-web-api live at `/api/ambient/...`
(e.g. `http://shogun-web-api:8090/api/ambient/summary`). The Next.js rewrite in
`next.config.js` maps `/api/:path*` → `http://shogun-web-api:8090/:path*`. So
`apiFetch("/api/ambient/summary")` in the browser becomes `/api/api/ambient/summary`,
which rewrites to `http://shogun-web-api:8090/api/ambient/summary` — the correct path.

**Changes made:**
- `src/lib/api.ts` — Added `api.ambient` namespace with 8 methods, all using `/api/ambient/...` path prefix
- `src/components/ambient/AmbientDashboard.tsx` — Replaced custom `API_BASE` + raw `fetch()` with `api.ambient.summary()`. Removed the duplicate `API_BASE` constant. Added `import { api }` from lib/api.ts.

**Verified:** `curl http://localhost:8090/api/ambient/summary` returns full JSON with city, weather, exchange_rate, aqi, sakura, transit, events fields.

---

## Fix 2: POI City Pastel Colors + Category Badges — IMPLEMENTED

**Changes made:**
- `src/components/pois/PoiCard.tsx` — Full rewrite
  - Added `CITY_BG` map: osaka=#FFF0E6, nara=#E8F5E9, kanazawa=#FFF8E1, tokyo=#EEF2FF, kyoto=#FCE4EC
  - Added `getCategoryBadge()` function: case-insensitive category matching for 8 categories
    (temple/shrine, food/restaurant/ramen, shopping, nature/park, museum/culture,
    entertainment, transit/station, electronics/tech)
  - Category badge renders as a pill at the top of each card with colored bg+text
  - City bg applied to card container background
  - Tags now use semi-transparent white background to stay readable on colored card bg

---

## Fix 3: Wishlist UX — Toast Feedback + Error Handling — IMPLEMENTED

**Changes made:**
- `src/app/wishlist/page.tsx`
  - Added `toast` state: `{ msg: string, type: 'success' | 'error' } | null`
  - Success toast: green, auto-dismisses after 3 seconds
  - Error toast: red, stays until tapped/clicked
  - Explicit try/catch around `api.wishlist.create()` — previously the `finally` swallowed errors
  - Submit button shows "Saving…" while in-flight
  - Added explanatory note: "Your wishlist items are saved for planning. The AI research pipeline will process them pre-trip."
  - Toast is `position: fixed` bottom-right, fully inline (no external library)

---

## Fix 4: External Links → MediaViewer Iframe Modal — IMPLEMENTED

**New file:** `src/components/MediaViewer.tsx`
- Props: `{ url: string, title: string, onClose: () => void }`
- URL resolution logic:
  - YouTube watch → `/embed/VIDEO_ID`
  - YouTube short link (youtu.be) → `/embed/VIDEO_ID`
  - YouTube search results → "cannot be embedded" message with Open button
  - Google Maps `?q=` → embed URL with `output=embed`
  - All other URLs → direct iframe (with `onError` fallback)
- Title bar shows page title + hostname
- "Open in tab ↗" button always visible
- Closes on ESC key or backdrop click
- `frame-src` CSP in `next.config.js` extended to include `youtube.com`, `maps.google.com`, `www.google.com`, and wildcard `*`

**Updated:**
- `src/components/knowledge/KnowledgeDeepDive.tsx` — YouTube, booking URL, and suggested search links now open MediaViewer
- `src/components/ambient/SakuraStatus.tsx` — Sakura result links open MediaViewer
- `src/components/ambient/EventsTile.tsx` — Event links open MediaViewer

---

## Fix 5: POI Map with Leaflet — IMPLEMENTED

**Package additions:**
- `package.json` — Added `leaflet: ^1.9.4`, `react-leaflet: ^4.2.1`, `@types/leaflet: ^1.9.3`
- Packages installed during Docker build (`npm install` runs in Dockerfile)

**New files:**
- `src/components/pois/PoisMap.tsx` — Dynamic import wrapper (`ssr: false`), shows loading placeholder
- `src/components/pois/PoisMapInner.tsx` — Actual Leaflet map component
  - Tile layer: OpenStreetMap (no API key required)
  - POI markers: blue (default Leaflet icon)
  - Accommodation marker: red (pointhi color markers CDN)
  - `BoundsFitter` component: auto-fits map bounds to all markers via `useMap` + `useEffect`
  - Handles 0-POI and 1-POI cases gracefully
  - Leaflet default icon URL fix applied (Next.js bundler compatibility)
  - POI marker popup: name_en, name_ja, category, crowd_notes (truncated to 100 chars)
  - Accommodation popup: label + "Your accommodation" heading
  - Hardcoded accommodation coords: osaka, kanazawa, tokyo, nara

**Updated:**
- `src/app/pois/page.tsx` — Map shows alongside POI tiles when a specific city is selected AND POIs have lat/lng. Falls back to standard grid when viewing "All" or when no coords exist.
- `src/lib/types.ts` — Added `lat?: number | null` and `lng?: number | null` to `Poi` interface (Agent A is adding these fields to the API response)

**Note:** Map does not display until Agent A's API enrichment provides lat/lng on POI objects. The `showMap` condition guards this — when lat/lng are null/undefined, standard grid renders.

---

## Build Results

```
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Generating static pages (12/12)
Container shogun-web-ui Started
✓ Ready in 73ms
```

No TypeScript errors. No lint errors. All 12 pages generated.

---

## Files Changed

| File | Action |
|------|--------|
| `src/lib/api.ts` | Modified — added `api.ambient` namespace |
| `src/lib/types.ts` | Modified — added `lat?`, `lng?` to Poi |
| `src/components/ambient/AmbientDashboard.tsx` | Modified — use `api.ambient.summary()`, removed custom fetch |
| `src/components/ambient/SakuraStatus.tsx` | Modified — links open MediaViewer |
| `src/components/ambient/EventsTile.tsx` | Modified — links open MediaViewer |
| `src/components/knowledge/KnowledgeDeepDive.tsx` | Modified — links open MediaViewer |
| `src/components/pois/PoiCard.tsx` | Modified — city pastel bg, category badge |
| `src/app/pois/page.tsx` | Modified — PoisMap wired in, conditional layout |
| `src/app/wishlist/page.tsx` | Modified — toast feedback, error handling |
| `src/components/MediaViewer.tsx` | Created |
| `src/components/pois/PoisMap.tsx` | Created |
| `src/components/pois/PoisMapInner.tsx` | Created |
| `next.config.js` | Modified — extended CSP frame-src |
| `package.json` | Modified — added leaflet, react-leaflet, @types/leaflet |
