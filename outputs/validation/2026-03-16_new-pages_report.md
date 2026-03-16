# Validation Report — New Pages & Features

**Date:** 2026-03-16
**Branch:** develop
**Build:** shogun-web-ui (Docker)

---

## Build Result

Docker image rebuilt with `--no-cache`. Build completed successfully. Container started and reports "Ready in 74ms".

---

## Routes Confirmed in Build Output

All 7 new routes present in Next.js build manifest:

| Route | Status | Notes |
|-------|--------|-------|
| /budget | Static | Budget tracker page |
| /checklist | Static | Packing checklist page |
| /phrases | Static | Japanese phrases page |
| /transit | Static | Transit guide page |
| /city/[slug] | Dynamic | Now includes GhibliCountdown (Tokyo only) and WeatherPlanner |
| /dashboard | Static | Now includes WeatherPlanner widget |

---

## Features Implemented

### Feature 1: Ghibli Countdown Tile
- Component: `components/widgets/GhibliCountdown.tsx`
- Counts down to 2026-04-03T12:00:00+09:00 (confirmed timed entry)
- Shows "Today!" card on day-of with green styling
- Shows amber countdown card with days/hours remaining before
- Rendered in `app/city/[slug]/page.tsx` only when `slug === "tokyo"`

### Feature 2: Phrases Page (`/phrases`)
- File: `app/phrases/page.tsx`
- 6 category tabs: Greetings, Food, Transit, Shopping, Emergency, Nara
- 40 total phrases across all categories
- Tap-to-copy Japanese text with "Copied!" feedback
- Mobile-friendly card layout

### Feature 3: Transit Guide (`/transit`)
- File: `app/transit/page.tsx`
- 5 accordion sections: IC Cards Overview, Where to Buy, How to Use, Our Trip Coverage, Key Tips
- City-specific coverage for Osaka, Nara, Kanazawa, Tokyo
- Opens first section (overview) by default

### Feature 4: Packing Checklist (`/checklist`)
- File: `app/checklist/page.tsx`
- 7 categories, 32 total items
- localStorage persistence via key `shogun_checklist_v1`
- Progress bar (X of Y packed, % complete)
- Per-category count display
- Expandable/collapsible sections (all open by default)
- Reset all button with confirmation step

### Feature 5: Budget Tracker (`/budget`)
- File: `app/budget/page.tsx`
- Calls `api.budget.list/add/remove` — handles API unavailable gracefully with amber warning banner
- Total spent card with JPY + USD equivalent (¥150/$ rate)
- Category breakdown horizontal bar chart (CSS only)
- Add expense form: date (optional), category dropdown, description, ¥ amount
- Expense list grouped by date with category emoji, ¥ and $ amounts, delete button
- BudgetItem type added to `lib/types.ts`
- `budget` namespace added to `lib/api.ts`

### Feature 6: Weather Planner Widget
- Component: `components/widgets/WeatherPlanner.tsx`
- Calls `api.ambient.weather(city)` — ambient endpoint with forecast array
- Computes outdoor score per day: Great (green), OK (yellow), Rainy (blue)
- Score logic: precip<2 AND max>12°C = Great; precip<8 OR max>8°C = OK; else Rainy
- Shows up to 5 forecast days with icon, date, high/low °F, precip, badge
- Added to `/dashboard` below WeatherWidget/BlossomWidget row
- Added to `/city/[slug]` below the weather/blossom context strip

### Feature 7: Navigation Updates
- **Sidebar** (`components/layout/Sidebar.tsx`): Refactored into MAIN_NAV, TOOLS_NAV, ADMIN_NAV groups. Trip Tools section has a visual divider and section label. Phrases, Transit, Checklist, Budget added.
- **MobileTabBar** (`components/layout/MobileTabBar.tsx`): Added Phrases, Checklist, Budget tabs. Bar is horizontally scrollable to accommodate additional items.

---

## API / Type Changes

| File | Change |
|------|--------|
| `lib/types.ts` | Added `BudgetItem` interface |
| `lib/api.ts` | Added `budget` namespace (list, add, remove) |

---

## Error Handling

- Budget page: if API returns 404 or network error, shows amber "not yet available" banner. Form is hidden when API is unavailable.
- WeatherPlanner: shows "Weather planner unavailable" on error, "Loading forecast..." while fetching.
- GhibliCountdown: pure client computation, no API calls — no failure modes.
- Checklist: localStorage errors caught silently; page renders correctly without persistence.
- Phrases: clipboard.writeText failure caught silently.
