# Shogun Web — Deployment Validation Report
Date: 2026-03-14
Branch: feature/20260313-shogun-web
Persona: devops-agent (svcnode-01), dba-agent (dbnode-01)
Status: DEPLOYED — All endpoints green

---

## What Was Deployed

### Infrastructure changes
- DB migration: `wishlist_items` table created in `shogun_v1` (dbnode-01)
- Grants: `shogun_app` granted SELECT/INSERT/UPDATE/DELETE on `wishlist_items` + sequence
- pg_hba.conf: Added `host shogun_v1 shogun_app 192.168.71.220/32 scram-sha-256` entry (svcnode-01 → dbnode-01 access)

### Docker containers on svcnode-01
| Container | Image | Port | Network | Status |
|-----------|-------|------|---------|--------|
| `shogun-web-api` | Python 3.11-slim / FastAPI | 8090 (host) | platform_net | Up |
| `shogun-web-ui` | Node 20-alpine / Next.js 14 | 3010 (host) | platform_net | Up |

### Traefik routing
| Route | Target | Result |
|-------|--------|--------|
| `shogun-api.ibbytech.com` → :80 | shogun-web-api:8090 | ✓ |
| `shogun.ibbytech.com` → :80 | shogun-web-ui:3000 | ✓ |

---

## Fixes Applied During Deployment

| Fix | Root Cause | Resolution |
|-----|-----------|------------|
| Docker network `traefik` → `platform_net` | Traefik uses `platform_net` not `traefik` | Updated both docker-compose.yml files |
| Port 3000 conflict with Grafana | `logstack-grafana-1` owns host port 3000 | Changed shogun-web-ui host port to 3010 |
| `@radix-ui/react-badge` package missing | Package doesn't exist on npm | Removed from package.json (not used in code) |
| `public/` directory missing | Dockerfile COPY expected it | Created `public/.gitkeep` |
| Schema mismatch: `date_start/date_end` | Actual DB uses `date_local` (single-date legs) | Updated calendar.py, itinerary.py, dashboard.py |
| Schema mismatch: `description/notes` | Actual DB uses `notes_en/notes_ja` | Mapped notes_en→description, notes_ja→notes |
| Schema mismatch: pois `description/best_time/map_url` | DB has `best_time_notes`, no `description` or `map_url` | Updated pois.py; map_url constructed from lat/lng |
| Schema mismatch: settings `preference_type` | Actual DB column is `preference_key` | Updated settings.py |
| Settings upsert no unique constraint | `user_preferences` has no (user_id, preference_key) unique constraint | Changed to DELETE + INSERT |
| pg_hba.conf missing svcnode-01 access for shogun_app | Only brainnode-01 (192.168.71.222) was allowed | Added svcnode-01 (192.168.71.220) rule via psql COPY TO + pg_reload_conf() |
| LLM gateway endpoint `/chat` → `/v1/chat` | Wrong path; gateway uses `/v1/chat` | Updated chat.py |
| LLM gateway payload format | Used `system` field + `/chat`; gateway needs messages array + `/v1/chat` | Fixed payload to include system as first message; added provider/model fields |

---

## Endpoint Validation Results

| Endpoint | Method | Result | Notes |
|----------|--------|--------|-------|
| `/health` | GET | ✓ 200 | `{"status":"ok"}` |
| `/calendar` | GET | ✓ 200 | Real itinerary data from DB |
| `/itinerary` | GET | ✓ 200 | Same as calendar, sortable |
| `/dashboard/status` | GET | ✓ 200 | Pre-trip: current_city=null, departure_date=2026-03-23 |
| `/weather?city=tokyo` | GET | ✓ 200 | Open-Meteo 13.1°C, 3-day forecast |
| `/blossom` | GET | ✓ 200 | 4 cities with status/peak dates |
| `/pois?city=osaka` | GET | ✓ 200 | POI data with tags and map_url |
| `/reminders?date=2026-04-01` | GET | ✓ 200 | Nara deer warnings, Todaiji passport reminder |
| `/wishlist` | GET | ✓ 200 | 0 items (empty, expected) |
| `/admin/health` | GET | ✓ 200 | All 5 services: ok |
| `/chat/history` | GET | ✓ 200 | Empty history initially |
| `/chat` | POST | ✓ 200 | AI response from Gemini about Todaiji Temple |

## Admin Health Detail
| Service | Status |
|---------|--------|
| shogun-core | ok |
| llm-gateway | ok |
| telegram-gateway | ok |
| valkey | ok |
| database | ok |

## UI Validation
| URL | Via | Result |
|-----|-----|--------|
| `shogun.ibbytech.com` | Traefik | ✓ 307 → /dashboard |
| `shogun-api.ibbytech.com/health` | Traefik | ✓ 200 |

---

## Open Items
- Cloudflare Access + Google OAuth: blocked on Todd's external setup
- `decode_cf_jwt()` in auth.py: stub — returns 501 (bypassed by SHOGUN_BYPASS_AUTH=true)
- Pi-hole DNS entries for `shogun.ibbytech.com` and `shogun-api.ibbytech.com`: verify from client devices
- Printable itinerary (MVP 6): not started

---

## Rollback
To remove: `docker compose -f app-services/shogun-web/shogun-web-api/docker-compose.yml down && docker compose -f app-services/shogun-web/shogun-web-ui/docker-compose.yml down` on svcnode-01.
DB rollback: `DROP TABLE wishlist_items;` on dbnode-01 as dba-agent.
