# Dashboard Tile Fixes — Validation Report
**Date:** 2026-03-17
**Branch:** develop
**Task:** Dashboard tile audit — TransitAlert formatting, sakura deduplication, white banner fix

---

## Step 1 — Playwright Visual Audit

Playwright browser navigation was denied by the permission system during this session.
Visual screenshot validation was not completed. Manual verification is required after rebuild.

---

## Step 2 — TransitAlert Analysis

**File:** `app-services/shogun-web/shogun-web-ui/src/components/ambient/TransitAlert.tsx`
**API:** `app-services/shogun-web/shogun-web-api/routers/ambient.py` → `_fetch_transit()`

**Finding:** TransitAlert.tsx is correctly implemented. No fix was required.

The API returns a clean, typed structure:
```json
{ "city": "...", "status": "normal"|"disruption", "alerts": [...], "last_checked": "..." }
```

The component handles all states:
- `loading` or `!data` → grey placeholder ("Checking transit…" / "Transit status unavailable")
- `status === "normal"` → green badge with train emoji and "Transit — All clear"
- `status === "disruption"` → red card with ⚠️ header and bullet-list of up to 3 alert titles

No raw JSON, no markdown, no code blocks are rendered. If raw text was previously
visible, the root cause was likely a stale build or a render of a different component
(not TransitAlert). The component code itself was already correct.

**Action:** No code changes made to TransitAlert.tsx or ambient.py.

---

## Step 3 — Sakura Tile Deduplication + White Banner Fix

### Problem identified

The dashboard was rendering sakura data twice:

| Render point | Component | Data source | Behaviour |
|---|---|---|---|
| `AmbientDashboard` (inside) | `SakuraStatus` | Summary endpoint (single city, cached via Valkey) | Correct — live, cached |
| `BlossomWidget` (in page.tsx) | Two `SakuraStatus` instances | Two independent `api.ambient.sakura()` calls (osaka + tokyo) | Duplicate — extra Tavily hits |

`BlossomWidget` was also the source of the white banner: it wraps everything in
`background: "white"` with a `boxShadow`, sitting immediately after `AmbientDashboard`
which already includes its own sakura tile.

### Fixes applied

**1. `dashboard/page.tsx`** — Removed `BlossomWidget` import and usage entirely.
The standalone `WeatherWidget` / `BlossomWidget` two-column row was replaced with
a single `WeatherWidget` row. The `WeatherPlanner` and `RemindersPanel` sections
are unchanged.

**2. `SakuraStatus.tsx`** — Replaced white backgrounds with transparent + themed borders:
- Loading/unavailable state: `background: "white"` → `background: "transparent"`, added `border: "1px solid #f3f4f6"`
- Loaded state: `background: "white"` → `background: "transparent"`, `boxShadow` removed, added `border: "1px solid #fce7f3"` (soft pink, consistent with sakura theme)

This ensures `SakuraStatus` inherits whatever background the parent container provides
(the `AmbientDashboard` section background) rather than forcing a white panel.

### Files changed

- `app-services/shogun-web/shogun-web-ui/src/app/(app)/dashboard/page.tsx`
- `app-services/shogun-web/shogun-web-ui/src/components/ambient/SakuraStatus.tsx`

---

## Step 4 — Loading Performance Notes (from code analysis)

### Parallel vs serial loading

**AmbientDashboard** uses a single `/api/ambient/summary` call which internally fans
out with `asyncio.gather()` across all sub-fetches (weather, exchange, AQI, sakura,
transit, events) in parallel on the API side. The UI fires one HTTP request and waits
for the combined response. This is optimal — all sub-data arrives in one payload.

**Valkey caching** is present for all sub-fetches:
- Weather: 30-minute TTL (`shogun:ambient:weather:{city}`)
- Exchange rate: 1-hour TTL (`shogun:ambient:exchange`)
- AQI: 1-hour TTL (`shogun:ambient:aqi:{city}`)
- Sakura: 6-hour TTL (`shogun:ambient:sakura:{city}`)
- Transit: 30-minute TTL (`shogun:ambient:transit:{city}`)
- Events: 6-hour TTL (`shogun:ambient:events:{city}`)

On a warm cache the summary endpoint should return sub-100ms. On a cold cache,
parallel Tavily calls (sakura + events each fire 2 queries) are the dominant latency
factor (~2-5s expected).

**Auto-refresh** is set to 10 minutes (`REFRESH_INTERVAL_MS = 10 * 60 * 1000`)
in `AmbientDashboard.tsx`. This is sensible given the shortest TTL is 30 minutes.

### Console errors

Not directly observed (Playwright was blocked). No structural issues visible in code
that would produce systematic console errors.

### WeatherWidget (standalone)

The standalone `WeatherWidget` in `page.tsx` makes its own separate call to
`/api/ambient/weather/{city}`. This is a mild redundancy — the weather data is also
included in the AmbientDashboard summary. Not a blocker for MVP; noted for future
consolidation.

---

## Rebuild Required

The following command must be run to apply the UI changes:
```bash
cd C:/git/work/shogun/app-services/shogun-web/shogun-web-ui
docker compose up -d --build
```

Bash execution was denied during this session — this must be run manually or with
Bash tool permission granted.

---

## Commit

Commit message for these changes:
```
fix(web-ui): dashboard tiles — sakura dedup, white banner fix
```

Files to stage:
- `app-services/shogun-web/shogun-web-ui/src/app/(app)/dashboard/page.tsx`
- `app-services/shogun-web/shogun-web-ui/src/components/ambient/SakuraStatus.tsx`
