# Shogun Web — Autonomous Coding Agent Execution Brief
Date: 2026-03-13
Status: Approved — Ready for autonomous execution

## How to Use This Document

This brief is written for a Claude Code agent running with `--dangerously-skip-permissions`.
Read it completely before writing a single line of code. Every decision has been made.
Your job is execution, not design. If something is unclear, use the planning documents
listed in the References section — do not improvise architecture.

Commit at the end of every phase. Write a validation evidence file at the end of every
phase to `outputs/validation/YYYY-MM-DD_shogun-web-phaseN_report.md`.

Work branch: `feature/20260313-shogun-web` (create if not present).

---

## Infrastructure Constraints (Hard Rules)

| Rule | Detail |
|------|--------|
| Deploy node | svcnode-01 (192.168.71.220) only. All Docker runs here. |
| SSH persona | devops-agent — key: `~/.ssh/devops-agent_ed25519_clean` |
| Transport | Git push/pull only. NO scp, sftp, rsync. |
| Database node | dbnode-01 (192.168.71.221) — dba-agent persona for schema work only |
| Do not touch | brainnode-01 (192.168.71.222) — shogun-core Telegram bot lives there. Leave it alone. |
| No Docker on dbnode | dbnode-01 is PostgreSQL only. No applications. No Docker. |

---

## Deployment Target: Internal Network First

Cloudflare and Google OAuth are not yet configured. Build for the internal network.

**Internal URL:** `http://shogun.ibbytech.com` (Pi-hole resolves this to 192.168.71.220)
**Fallback URL:** `http://192.168.71.220:3000` (direct IP if DNS not set up)

### Auth Stub (Critical — Read This)

Cloudflare Access JWT is not available. Implement an auth bypass for internal testing:

```python
# shogun-web-api: auth.py
BYPASS_AUTH = os.getenv("SHOGUN_BYPASS_AUTH", "false").lower() == "true"

def get_current_user(request: Request) -> User:
    if BYPASS_AUTH:
        # Return Todd as default admin user for internal testing
        return User(id=1, email="todd@ibbytech.com", name="Todd", role="admin")
    # Production path: parse CF-Authorization JWT header
    cf_jwt = request.headers.get("CF-Authorization")
    if not cf_jwt:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Decode CF JWT, map email to user, return role
    return decode_cf_jwt(cf_jwt)
```

Set `SHOGUN_BYPASS_AUTH=true` in `.env` for development.
When Cloudflare is ready, set to `false` and implement `decode_cf_jwt()`.
All route protection code is already in place — only the bypass changes.

### Traefik Labels for Internal Access

```yaml
# Both services route through Traefik on svcnode-01
# shogun-web-ui: traefik routes shogun.ibbytech.com → :3000
# shogun-web-api: traefik routes shogun-api.ibbytech.com → :8090
# For internal-only testing, use Host rules with the internal DNS names
```

---

## Project Structure

```
app-services/
  shogun-web/
    shogun-web-api/           # FastAPI backend (Python)
      Dockerfile
      docker-compose.yml
      requirements.txt
      main.py
      auth.py                 # CF JWT + bypass
      routers/
        dashboard.py
        calendar.py
        itinerary.py
        pois.py
        chat.py
        wishlist.py
        weather.py
        reminders.py
        knowledge.py
        admin.py
      models.py               # Pydantic models
      db.py                   # psycopg2 connection pool
      cache.py                # Valkey client

    shogun-web-ui/            # Next.js frontend
      Dockerfile
      docker-compose.yml
      package.json
      next.config.js
      tailwind.config.js
      src/
        app/
          layout.tsx          # Root layout: sidebar + mobile tab bar
          globals.css         # CSS custom properties — all theme variables here
          page.tsx            # Redirect to /dashboard
          dashboard/page.tsx
          calendar/page.tsx
          itinerary/page.tsx
          pois/page.tsx
          chat/page.tsx
          wishlist/page.tsx
          settings/page.tsx
          admin/page.tsx
          city/
            [slug]/page.tsx   # Per-city themed entry pages
        components/
          layout/
            Sidebar.tsx
            MobileTabBar.tsx
            CityHeader.tsx
          widgets/
            WeatherWidget.tsx
            BlossomWidget.tsx
            TripStatusCard.tsx
            ShogunHealthCard.tsx
          city/
            CityHero.tsx      # CSS gradient + SVG landmark layer
            CityTheme.tsx     # Sets data-city attribute
          chat/
            ChatPanel.tsx
            ChatMessage.tsx
          calendar/
            CalendarGrid.tsx
            DayDrawer.tsx
            LegCard.tsx
          pois/
            PoiCard.tsx
            CityTabs.tsx
            FilterBar.tsx
          reminders/
            DayReminder.tsx
            RemindersPanel.tsx
          knowledge/
            KnowledgeDeepDive.tsx
            VideoEmbed.tsx
        lib/
          api.ts              # API client (all fetch calls to shogun-web-api)
          types.ts            # TypeScript interfaces
          cities.ts           # City config: slug, kanji, dates, theme vars
```

---

## Tech Stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Frontend | Next.js 14 (App Router) | TypeScript, React 18 |
| Styling | Tailwind CSS 3.x | References CSS variables from globals.css |
| UI components | shadcn/ui | Install: `npx shadcn-ui@latest init` |
| Backend API | FastAPI (Python 3.11+) | Async, Docker on svcnode-01 |
| Database | PostgreSQL 17, shogun_v1 | psycopg2, connection pool |
| Cache | Valkey (redis-py client) | valkey.platform.ibbytech.com:6379 |
| Weather | Open-Meteo | Free, no API key, REST |
| LLM | LLM Gateway | http://llm.platform.ibbytech.com |
| Reverse proxy | Traefik v3 | Already running on svcnode-01 |

---

## Database — Existing Schema (shogun_v1)

These tables already exist. Do not recreate them.

```sql
-- Already deployed:
users (id, telegram_id, name, email, role)
user_preferences (user_id, preference_type, preference_value)
trip_itinerary (id, leg_type, city, date_start, date_end, title, description,
                address_en, address_ja, confirmation_number, notes, status)
trip_pois (id, city, name_en, name_ja, category, tags, description,
           crowd_notes, best_time, map_url, source)
```

### New table — deploy this via dba-agent before Phase 2:

```sql
-- wishlist_items — run on dbnode-01 as dba-agent
CREATE TABLE wishlist_items (
    id              SERIAL PRIMARY KEY,
    requested_by    INTEGER NOT NULL REFERENCES users(id),
    city            TEXT,
    description     TEXT NOT NULL,
    ai_research     TEXT,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by     INTEGER REFERENCES users(id),
    reviewed_at     TIMESTAMPTZ,
    itinerary_note  TEXT,
    created_utc     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_wishlist_status ON wishlist_items(status);
CREATE INDEX idx_wishlist_requested_by ON wishlist_items(requested_by);
```

### Day reminders — seed data (hardcode in reminders.py, no separate table needed):

```python
# Day-specific logistics reminders
# Key: date string YYYY-MM-DD, Value: list of reminder objects
TRIP_REMINDERS = {
    "2026-03-23": [
        {"type": "logistics", "icon": "✈️", "text": "Arrival day — Narita or Haneda. IC card (Suica/Pasmo) available at airport. Load ¥5,000–10,000."},
        {"type": "tip", "icon": "🚃", "text": "Narita Express (N'EX) to central Tokyo ~¥3,000. Limousine Bus is cheaper but slower."},
    ],
    "2026-04-01": [
        {"type": "logistics", "icon": "🦌", "text": "Nara — deer will bow if you bow first. Do not tease them. They bite."},
        {"type": "warning", "icon": "⚠️", "text": "Todaiji museum requires passport for foreign visitors. Bring passports."},
        {"type": "tip", "icon": "🦌", "text": "Deer crackers (shika senbei) sold outside for ¥200. Expect to be surrounded immediately."},
    ],
    "2026-04-03": [
        {"type": "logistics", "icon": "🚄", "text": "Osaka arrival — Shinkansen Nozomi from Nara via Shin-Osaka."},
        {"type": "tip", "icon": "🦪", "text": "Kuromon Ichiba Market — Osaka's kitchen. Morning is best for seafood."},
    ],
    "2026-04-06": [
        {"type": "logistics", "icon": "🚃", "text": "Osaka → Kyoto: Hankyu Railway ¥400 (30 min). Avoid shinkansen — overkill for this distance."},
    ],
    "2026-04-09": [
        {"type": "logistics", "icon": "✈️", "text": "Departure day. Kansai International Airport (KIX). Allow 2.5 hours minimum before flight."},
        {"type": "tip", "icon": "🎁", "text": "Last chance for omiyage (souvenir gifts) — best selection at KIX departures duty-free."},
    ],
    # Add more dates as itinerary is confirmed
}

# Global tips shown on every city page (not date-specific)
GLOBAL_REMINDERS = [
    {"type": "tip", "icon": "🎫", "text": "Train tickets in Japan: sold outside the station, not inside. Buy before you enter the gate."},
    {"type": "tip", "icon": "💴", "text": "Many restaurants and smaller shops are cash-only. Keep ¥10,000–20,000 on hand."},
    {"type": "tip", "icon": "📱", "text": "7-Eleven ATMs accept foreign cards. Post Office ATMs also work internationally."},
    {"type": "warning", "icon": "⚠️", "text": "Eating while walking is considered rude in Kyoto and Nara. Stop and eat."},
    {"type": "tip", "icon": "🗑️", "text": "Almost no public trash cans in Japan. Keep a bag for your own trash."},
    {"type": "logistics", "icon": "👟", "text": "Slip-on shoes are strongly recommended. You will remove them at many temples and restaurants."},
]
```

---

## City Configuration (cities.ts)

```typescript
// src/lib/cities.ts
export const CITIES = {
  tokyo: {
    slug: "tokyo",
    name: "Tokyo",
    kanji: "東京",
    dates: "Mar 23–31",
    nights: 8,
    lat: 35.6762,
    lng: 139.6503,
    theme: {
      primary: "#0d1b2e",
      accent: "#e91e8c",
      highlight: "#00d4ff",
      surface: "#f0f4ff",
    },
    landmark: "Shibuya Crossing",
    tagline: "34 million people. 1,300 years of temples. Let's start.",
    blossomSpot: "Shinjuku Gyoen",
  },
  nara: {
    slug: "nara",
    name: "Nara",
    kanji: "奈良",
    dates: "Apr 1–2",
    nights: 2,
    lat: 34.6851,
    lng: 135.8048,
    theme: {
      primary: "#2d3a1e",
      accent: "#8b6914",
      highlight: "#c4956a",
      surface: "#f7f3ec",
    },
    landmark: "Todaiji Temple",
    tagline: "1,300 years of sacred ground. The deer were here before the temples.",
    blossomSpot: "Nara Park",
    reminder: "Passport required for Todaiji museum entry.",
  },
  osaka: {
    slug: "osaka",
    name: "Osaka",
    kanji: "大阪",
    dates: "Apr 3–6",
    nights: 4,
    lat: 34.6937,
    lng: 135.5023,
    theme: {
      primary: "#1a0a00",
      accent: "#ff4500",
      highlight: "#f5c518",
      surface: "#fff8f0",
    },
    landmark: "Dotonbori",
    tagline: "Japan's kitchen. They eat out 14 times a week. Keep up.",
    blossomSpot: "Osaka Castle Park",
  },
  kyoto: {
    slug: "kyoto",
    name: "Kyoto",
    kanji: "京都",
    dates: "Apr 6–9",
    nights: 3,
    lat: 35.0116,
    lng: 135.7681,
    theme: {
      primary: "#1a0f0a",
      accent: "#8b1a1a",
      highlight: "#f7b8c4",
      surface: "#faf6f0",
    },
    landmark: "Fushimi Inari",
    tagline: "Ancient capital for 1,000 years. 1,600 temples. Three days is never enough.",
    blossomSpot: "Maruyama Park",
  },
} as const;

export type CitySlug = keyof typeof CITIES;
```

---

## API Endpoints (shogun-web-api)

All routes protected by auth middleware (bypass or CF JWT).

```
GET  /health                    Service health check (no auth required)

GET  /dashboard/status          { current_city, trip_day, total_days, departure_date,
                                  shogun_health, pending_wishlist_count }
GET  /weather?city={slug}       { city, current, forecast_3day } — Open-Meteo, Valkey cached 30min
GET  /calendar                  [ { id, leg_type, city, date_start, date_end, title,
                                    description, address_en, address_ja,
                                    confirmation_number, notes, status } ]
GET  /itinerary                 Same as calendar, sortable, all legs
POST /itinerary                 Add leg (admin/edit role only)
PUT  /itinerary/{id}            Update leg (admin/edit role only)
DELETE /itinerary/{id}          Delete leg (admin/edit role only)

GET  /pois?city={slug}&tags=[]  [ { id, city, name_en, name_ja, category, tags,
                                    description, crowd_notes, best_time, map_url } ]
GET  /pois/{id}/knowledge       { poi, summary, youtube_query, suggested_searches,
                                  booking_url } — POI deep dive data

GET  /reminders?date={YYYY-MM-DD}  { date_reminders: [], global_reminders: [] }

GET  /wishlist                  All items (admin: all; read-only: own only)
POST /wishlist                  { city, description } — any authenticated user
PUT  /wishlist/{id}/approve     Admin/edit only. Optional: { itinerary_note }
PUT  /wishlist/{id}/reject      Admin/edit only

POST /chat                      { message: str } → { response: str, session_id: str }
GET  /chat/history              [ { role, content, timestamp } ] — from Valkey

GET  /blossom                   [ { city, spot, status, peak_date, notes } ]
                                Status values: "not_started" | "early" | "peak" | "late" | "finished"

GET  /admin/health              { services: [ { name, status, latency_ms, last_check } ] }
                                Services: shogun-core, llm-gateway, valkey, telegram-gateway, db
```

### Weather integration (Open-Meteo):

```python
# For each city, use lat/lng from cities config
# Open-Meteo endpoint (free, no API key):
# https://api.open-meteo.com/v1/forecast?
#   latitude={lat}&longitude={lng}
#   &current=temperature_2m,weather_code,wind_speed_10m
#   &daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum
#   &forecast_days=3&timezone=Asia/Tokyo
```

### Blossom tracker (seed data — no external API needed):

```python
# 2026 cherry blossom forecast for Japan (use as initial seed, update if official data available)
# Japan Meteorological Corporation publishes official forecasts
BLOSSOM_2026 = [
    {"city": "tokyo",  "spot": "Shinjuku Gyoen",    "peak_date": "2026-03-28", "status": "peak"},
    {"city": "nara",   "spot": "Nara Park",          "peak_date": "2026-04-01", "status": "peak"},
    {"city": "osaka",  "spot": "Osaka Castle Park",  "peak_date": "2026-04-02", "status": "late"},
    {"city": "kyoto",  "spot": "Maruyama Park",      "peak_date": "2026-04-03", "status": "late"},
]
# Status is computed dynamically: compare today's date to peak_date ± 5 days
```

### Blossom webcams (embed sources — public, no API key):

```python
# These are publicly accessible webcam/live streams for blossom viewing
# Embed as iframe or link out depending on embed permission
BLOSSOM_WEBCAMS = [
    {
        "city": "tokyo",
        "location": "Ueno Park",
        "source": "YouTube Live — search 'Ueno Park cherry blossom live'",
        "type": "youtube_search",  # Search YouTube, don't hardcode a video ID
    },
    {
        "city": "kyoto",
        "location": "Maruyama Park",
        "source": "YouTube Live — search 'Maruyama Park sakura live'",
        "type": "youtube_search",
    },
]
# Note: YouTube Live embed IDs change. Implement as a search link, not a hardcoded embed.
# UI: "Watch live →" button that opens YouTube search for the location + current date
```

---

## Phase Execution Plan

### Phase 1 — Project Foundation + Internal Deployment
**Goal:** Next.js and FastAPI running on svcnode-01, accessible at http://shogun.ibbytech.com

**Entry criteria:** Nothing (start here)

**Deliverables:**
- `app-services/shogun-web/shogun-web-api/` — FastAPI skeleton with /health, auth bypass
- `app-services/shogun-web/shogun-web-ui/` — Next.js 14 project, Tailwind, shadcn/ui
- `globals.css` with all CSS custom properties (base theme + city overrides)
- Docker Compose for both services on svcnode-01
- Traefik labels for internal routing (shogun.ibbytech.com and shogun-api.ibbytech.com)
- `.env.example` with all required variables documented
- Git push to feature branch, then pull on svcnode-01

**Exit criteria:** `curl http://shogun.ibbytech.com` returns the Next.js app.
`curl http://shogun-api.ibbytech.com/health` returns `{"status": "ok"}`.

**Key files:**
```
.env.example variables:
  SHOGUN_BYPASS_AUTH=true
  DATABASE_URL=postgresql://shogun_app:PASSWORD@192.168.71.221/shogun_v1
  VALKEY_URL=redis://valkey.platform.ibbytech.com:6379
  LLM_GATEWAY_URL=http://llm.platform.ibbytech.com
  NEXT_PUBLIC_API_URL=http://shogun-api.ibbytech.com
```

---

### Phase 2 — Backend API: Core Data Endpoints
**Goal:** All database-backed endpoints returning real data

**Entry criteria:** Phase 1 complete. `wishlist_items` table deployed to dbnode-01.

**Deliverables:**
- `/calendar` — full itinerary from trip_itinerary
- `/itinerary` — same, with POST/PUT/DELETE for admin role
- `/pois` — by city and tag filter from trip_pois
- `/dashboard/status` — current city (computed from today's date vs itinerary dates)
- `/weather` — Open-Meteo integration with Valkey 30-min cache
- `/blossom` — seed data endpoint
- `/reminders` — date-specific + global tips
- `/wishlist` — CRUD with role enforcement

**Exit criteria:** `curl http://shogun-api.ibbytech.com/calendar` returns itinerary JSON.
`curl http://shogun-api.ibbytech.com/weather?city=tokyo` returns temperature data.

---

### Phase 3 — Per-City Themed Entry Pages
**Goal:** Each city has a visually distinct, immersive landing page

**Entry criteria:** Phase 1 complete (frontend running)

**Deliverables:**
- `/city/[slug]` dynamic route for: tokyo, nara, osaka, kyoto
- `CityHero.tsx` — CSS gradient + SVG landmark composition, city kanji overlay
- `CityTheme.tsx` — sets `data-city` attribute, applies CSS variable overrides
- CSS override blocks in globals.css for all 4 cities
- City entry page sections: hero, trip context card, blossom teaser, weather strip,
  day's itinerary (if current day is in this city), top POI cards, chat CTA
- Navigation: city name links in sidebar and mobile tabs resolve to `/city/[slug]`

**Per-city landmark SVG shapes (simple, CSS-styled, no external assets):**
- Tokyo: torii gate silhouette + crossing lines
- Nara: Todaiji Nandaimon gate outline + deer shape
- Osaka: Dotonbori sign shapes (rectangular, neon-style)
- Kyoto: torii gate tunnel perspective (repeating, diminishing)

**Exit criteria:** Navigating to `/city/tokyo` shows a visually distinct page with navy
becoming midnight blue, torii red becoming neon magenta, Tokyo kanji visible, a cherry
blossom teaser card, and weather strip. All 4 cities render with distinct color moods.

---

### Phase 4 — Calendar + Itinerary Pages
**Goal:** Brenda can view and edit the full trip plan

**Entry criteria:** Phase 2 complete

**Deliverables:**
- `/calendar` — 17-day grid Mar 23–Apr 9, color-coded by leg type
- Day click → detail drawer: address EN + JA, confirmation numbers, notes
- Edit mode (admin/edit): click leg to edit inline, + to add new, trash to delete
- `/itinerary` — sortable table, Japanese address tap-to-copy, TBD dates highlighted
- Mobile-responsive: calendar grid scrolls horizontally on phone

**Exit criteria:** Click Mar 23 on calendar, see arrival day details. Edit a leg title,
save, see updated value on page without full reload.

---

### Phase 5 — Dashboard + Weather Widget + Chat
**Goal:** Full dashboard before departure, AI chat working

**Entry criteria:** Phase 2 + Phase 3 complete

**Deliverables:**
- `/dashboard` — trip status card (Day N of 17, current city), weather 3-day strip,
  Shogun health badge, pending wishlist count badge (admin only)
- Day-specific reminders panel on dashboard (today's date → TRIP_REMINDERS lookup)
- Weather widget: current conditions + 3-day forecast, city auto-detected from trip date
- `/chat` — full-page AI chat
  - Sends to LLM gateway via shogun-web-api `/chat` endpoint
  - Valkey key: `shogun:web:{user_id}` (separate from Telegram context)
  - Message history displayed, persisted 24h
- Chat panel collapsible sidebar on desktop dashboard, modal on mobile

**Chat system prompt (for shogun-web-api to pass to LLM gateway):**
```
You are Shogun, an AI travel concierge for the Ibbotson family's Japan trip
(March 23 – April 9, 2026). You have deep knowledge of every city, restaurant,
temple, and transit option on the itinerary. You can answer questions about
specific POIs, give restaurant recommendations, explain cultural customs, and
help plan each day. In the web interface, you serve as both a trip advisor
and an educational guide — if someone asks about Todaiji Temple, give them
a real educational answer, not just basic tourist tips. Current trip context:
{city} ({dates}). User: {user_name} ({role}).
```

**Exit criteria:** Dashboard shows correct trip day. Weather shows for the right city.
Chat responds: "Tell me about Todaiji Temple" → gets a substantive educational response.

---

### Phase 6 — Blossom Tracker + POI Knowledge Base
**Goal:** Blossom status and educational deep dives per POI

**Entry criteria:** Phase 2 complete

**Deliverables:**
- `/pois` — city tabs (Tokyo, Nara, Osaka, Kyoto, Sakai, Kanazawa)
  - Filter bar: category chips (temple, food, anime, camera, activity)
  - POI card: name EN + JA, description, crowd notes, best time, map link
  - Click POI card → knowledge deep dive page
- `/pois/[id]/knowledge` — POI deep dive page
  - Summary description (from trip_pois data)
  - "Learn more" section with suggested search queries for Google, YouTube
  - YouTube search CTA (formatted query: "{poi_name} Japan guide 2026")
  - Educational context pulled from chat: "Ask Shogun about {poi_name}" inline
  - Practical info: best time to visit, how long to spend, how to get there
- Blossom tracker widget (shown on dashboard and city pages)
  - City: Tokyo / Nara / Osaka / Kyoto
  - Status badge: Early | Peak | Late | Finished
  - Peak date, spot name
  - "Watch live" link (YouTube search for blossom webcam)

**Exit criteria:** Click Todaiji Temple POI card → see deep dive page with educational
content, YouTube search link, and an "Ask Shogun" inline chat entry. Blossom widget
on dashboard shows correct status for today's date vs peak date.

---

### Phase 7 — Trip Reminders + Day Briefing Panel
**Goal:** Logistics reminders integrated throughout the app

**Entry criteria:** Phase 4 complete

**Deliverables:**
- `DayReminder.tsx` component — renders a single reminder with icon, type badge, text
- `RemindersPanel.tsx` — groups date-specific + global reminders, styled by type
  (logistics = navy, warning = amber, tip = green)
- Reminders panel integrated into:
  - Calendar day drawer (when opening a specific day)
  - Dashboard (today's reminders, always visible)
  - City entry pages (global tips for that city + any date-specific if current day)
- "What to bring" checklist on city page: passport, cash, IC card, slip-on shoes

**Exit criteria:** Open calendar for Apr 1 (Nara) → see passport reminder.
Dashboard shows today's reminders. City/nara page shows Todaiji passport warning.

---

### Phase 8 — Wishlist Pipeline
**Goal:** Madeline can submit wishlist items, Todd/Brenda can approve

**Entry criteria:** Phase 2 complete, wishlist_items schema deployed

**Deliverables:**
- `/wishlist` — submission form (city selector, text description, notes)
- Admin view: approval queue with approve/reject/add-to-itinerary buttons
- Each card shows: request text, Shogun research summary (populated by shogun-core — placeholder if not yet), city tag, status badge
- On approve: optional itinerary_note field, status → approved
- On reject: status → rejected, card moves to archive section

**Exit criteria:** Submit a wishlist item → appears in admin queue →
approve it → status changes to approved.

---

### Phase 9 — Settings + Admin Panel
**Goal:** User management and service health visibility

**Entry criteria:** Phases 1–8 complete

**Deliverables:**
- `/settings` — dietary preferences (read from user_preferences), display name, Telegram ID link
- Admin section in /settings: all users management (admin/edit role only)
- `/admin` — service health panel
  - Cards: shogun-core, llm-gateway, valkey, telegram-gateway, database
  - Each card: status badge (green/yellow/red), latency, last check timestamp
  - Auto-refresh every 60 seconds
  - Powered by `/admin/health` endpoint

**Exit criteria:** /admin shows green status for all services.
Edit dietary preferences in /settings, save, reload — value persists.

---

## Commit Strategy

End of each phase:
```bash
git add app-services/shogun-web/
git commit -m "feat(shogun-web): phase N — [short description]"
git push origin feature/20260313-shogun-web
```

SSH to svcnode-01 and pull:
```bash
ssh -i ~/.ssh/devops-agent_ed25519_clean devops-agent@192.168.71.220
cd /opt/git/work/shogun
git pull origin feature/20260313-shogun-web
docker-compose -f app-services/shogun-web/shogun-web-api/docker-compose.yml up -d --build
docker-compose -f app-services/shogun-web/shogun-web-ui/docker-compose.yml up -d --build
```

---

## What Is NOT in Scope for This Brief

These features were discussed but are aspirational — do not attempt without a
separate planning session:

| Feature | Reason Deferred |
|---------|-----------------|
| Email newsletter with photo uploads | Needs SMTP service, file storage, auth — not ready |
| YouTube embed (specific video IDs) | Live stream IDs change — use search links instead |
| Booking from chat session | Requires external partner APIs |
| TikTok video integration | Platform restrictions on embedding |
| Cloudflare Access + Google IdP | Todd's external items — bypass is in place |
| Dark mode | Deferred — 3-person app, not worth the time |

---

## References

- Shogun Web Plan (full architecture): `outputs/planning/shogun-web-plan.md`
- City Theme Specifications: `outputs/planning/shogun-web-city-themes.md`
- Planning State (project overview): `outputs/planning/planning-state.md`
- Existing shogun-core (do not modify): `app-services/shogun-core/`
- Platform services: `../platform/.claude/services/_index.md`
- Foundation rules: `../ibbytech-foundation/.claude/rules/`
