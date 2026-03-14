# Shogun Web — All Phases Build Report
Date: 2026-03-13
Branch: feature/20260313-shogun-web
Status: Code complete — awaiting deployment to svcnode-01

---

## What Was Built

### Phase 1 — Project Foundation
- `shogun-web-api/` — FastAPI skeleton with auth bypass, /health endpoint
- `shogun-web-ui/` — Next.js 14 App Router, Tailwind, TypeScript
- Docker Compose for both services with Traefik labels
- Traefik routes: `shogun.ibbytech.com` → :3000, `shogun-api.ibbytech.com` → :8090
- `.env.example` with all required variables

### Phase 2 — Backend API: All Data Endpoints
- `/calendar` — GET from trip_itinerary
- `/itinerary` — GET/POST/PUT/DELETE with edit role enforcement
- `/pois` — city + tag filtered from trip_pois
- `/pois/{id}/knowledge` — deep dive with YouTube query + suggested searches
- `/dashboard/status` — current city computed from today's date vs itinerary
- `/weather` — Open-Meteo integration, Valkey 30-min cache
- `/blossom` — seed data with dynamic status computed from today vs peak date
- `/reminders` — date-specific + global trip tips
- `/wishlist` — CRUD with role enforcement (admin sees all, others see own)
- `/chat` + `/chat/history` — LLM gateway relay, Valkey history 24h TTL
- `/admin/health` — pings shogun-core, llm-gateway, telegram-gateway, valkey, db
- `/settings/preferences` + `/settings/users` — dietary prefs, user management

### Phase 3 — Per-City Themed Entry Pages
- `/city/[slug]` for tokyo, nara, osaka, kyoto
- CityHero with gradient + kanji watermark + landmark SVG
- 4 landmark SVGs (CSS-styled, no external assets):
  - Tokyo: torii gate + Shibuya crossing lines
  - Nara: Todaiji gate + deer silhouette + antlers
  - Osaka: Dotonbori sign frames + Glico runner
  - Kyoto: Fushimi Inari torii tunnel perspective
- `globals.css` CSS variable overrides for all 4 cities
- CityTheme client component sets `data-city` on html root

### Phase 4 — Calendar + Itinerary Pages
- `/calendar` — 17-day grid (Mar 23–Apr 9), color-coded by leg type
- Day click → DayDrawer with full leg details + address EN/JA tap-to-copy
- `/itinerary` — full list with date headers, admin edit controls in LegCard
- Mobile: grid scrolls, drawer slides up from bottom

### Phase 5 — Dashboard + Weather + Chat
- `/dashboard` — TripStatusCard (countdown/in-progress), WeatherWidget 3-day,
  BlossomWidget, ShogunHealthCard, RemindersPanel (today's date)
- `/chat` — full-page ChatPanel, Valkey history, LLM gateway relay
- Web chat uses separate Valkey key `shogun:web:{user_id}` from Telegram

### Phase 6 — Blossom Tracker + POI Knowledge Base
- `/pois` — CityTabs + FilterBar (by tag), PoiCard grid
- `/pois/[id]` — KnowledgeDeepDive: summary, YouTube CTA, Google search links,
  practical info, inline "Ask Shogun" chat expander
- BlossomWidget embedded on dashboard + city pages

### Phase 7 — Trip Reminders + Day Briefing
- DayReminder component — styled by type (logistics/warning/tip)
- RemindersPanel — date-specific + global, integrated into:
  - Dashboard (today's date)
  - DayDrawer (day-specific)
  - City pages (global tips + "What to bring" checklist)

### Phase 8 — Wishlist Pipeline
- `/wishlist` — submission form (city + description)
- Admin view: pending queue with approve/reject + itinerary note
- Archive section for decided items

### Phase 9 — Settings + Admin Panel
- `/settings` — dietary preferences (read/write user_preferences)
- Admin section: user list (admin only)
- `/admin` — ServiceHealth cards for all 5 services, 60s auto-refresh

---

## Deployment Steps (Next)

### 1. Run DB migration (dba-agent on dbnode-01)
```bash
ssh -i ~/.ssh/dba-agent_ed25519 dba-agent@192.168.71.221
psql -U dba-agent -d shogun_v1 -f /opt/git/work/shogun/database/migrations/20260313_wishlist_items.sql
```

### 2. Create .env on svcnode-01 (devops-agent)
```bash
ssh -i ~/.ssh/devops-agent_ed25519_clean devops-agent@192.168.71.220
cat > /opt/git/work/shogun/app-services/shogun-web/shogun-web-api/.env << 'EOF'
SHOGUN_BYPASS_AUTH=true
DATABASE_URL=postgresql://shogun_app:PASSWORD@192.168.71.221/shogun_v1
VALKEY_URL=redis://valkey.platform.ibbytech.com:6379
LLM_GATEWAY_URL=http://llm.platform.ibbytech.com
EOF
```

### 3. Deploy
```bash
bash app-services/shogun-web/deploy.sh feature/20260313-shogun-web
```

### 4. Exit criteria checks
- `curl http://shogun.ibbytech.com` → Next.js app
- `curl http://shogun-api.ibbytech.com/health` → `{"status":"ok"}`
- Navigate to /city/tokyo → themed page with navy + magenta
- Click calendar day → drawer with reminders
- Chat → "Tell me about Todaiji Temple" → educational response

---

## Files Created
- app-services/shogun-web/shogun-web-api/ (12 Python files)
- app-services/shogun-web/shogun-web-ui/ (45+ TypeScript/TSX files)
- database/migrations/20260313_wishlist_items.sql
- app-services/shogun-web/deploy.sh
