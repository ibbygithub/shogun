# Planning State — Shogun
Last updated: 2026-03-17

## Project Summary

Shogun is an AI travel concierge for the Ibbotson Japan trip (Mar 23–Apr 9).
Delivered via Telegram (shogun-core) and a web frontend (shogun-web).
The Telegram bot handles live location-aware recommendations; the web app gives
Brenda an itinerary editing surface and all three travelers a unified trip view.

**Current infrastructure: all 10 services running on Docker Desktop (Windows laptop).**
Laptop stays home in California unattended during the trip (Mar 23–Apr 9).
Public access via Cloudflare Tunnel → shogun.ibbytech.com (in progress — see blockers).
Startup/shutdown: `scripts/start-shogun.ps1` / `scripts/stop-shogun.ps1`

## Infrastructure — Current State (2026-03-15)

All 10 containers validated on Docker Desktop. Both repos pushed to GitHub (develop + master/main).

| Container | Status | Notes |
|-----------|--------|-------|
| platform-postgres | healthy | Named volume platform-postgres-data |
| platform-valkey | running | 127.0.0.1:6379 (localhost only) |
| platform-llm-gateway | running | Gemini 2.0 Flash |
| platform-telegram-gateway | running | Polling mode, no public URL needed |
| platform-places-google | running | Pulls image (harmless warning on build) |
| platform-tavily | running | |
| platform-scraper-api | running | |
| shogun-core | running | Containerized 2026-03-15 (was systemd on brainnode-01) |
| shogun-web-api | running | SHOGUN_BYPASS_AUTH=true (Cloudflare handles auth) |
| shogun-web-ui | running | http://localhost:3010 |

**Not running (intentional):** platform-reddit-gateway (DB setup needed first — Phase 1 below)
**Traefik:** Disabled. Will NOT be restored pre-trip. Cloudflare Tunnel proxies directly to shogun-web-ui:3000.

## RECOVERY COMPLETE — 2026-03-15
✅ All 10 containers running and validated
✅ Telegram bot live (polling mode)
✅ LLM pipeline working (Gemini 2.0 Flash via llm-gateway)
✅ Location trigger logic validated
✅ Web UI loading at localhost:3010
✅ Web AI chat working
✅ Database schema applied, Todd seeded (11 itinerary legs, 30 POIs, 8 preferences)
✅ Start/stop scripts with directory preservation
✅ Both repos committed and pushed (develop + master/main)

## Completed — 2026-03-15 to 2026-03-16

| Item | Notes |
|------|-------|
| Shogun-core health URL fix | admin.py had old brainnode-01 hostname → http://shogun-core:8082/health |
| Dashboard /status 500 fix | shogun_app missing grants on wishlist_items → wrapped in try/except |
| Calendar city colors | All 18 trip tiles: Osaka=amber, Kanazawa=green, Tokyo=blue, travel=grey + city emoji labels |
| Temperatures °F primary | WeatherCard + WeatherWidget — °F large, °C smaller, all forecast in °F |
| Live blossom status | BlossomWidget: replaced static DB with live Tavily Osaka + Tokyo sakura calls |
| Planning page | /planning — POI browser with city filter, 18-day timeline, schedule modal |
| Phrases page | /phrases — 40 phrases, 6 category tabs, tap-to-copy Japanese text |
| Transit guide | /transit — ICOCA/Suica guide, per-city coverage, KIX purchase instructions |
| Packing checklist | /checklist — 32 items, 7 categories, localStorage persistence, progress bar |
| Budget tracker | /budget UI + /api/budget (GET/POST/DELETE) + budget_items table with shogun_app grants |
| Restaurant reservation tracking | wishlist_items: category, needs_reservation, reservation_confirmed columns + PATCH endpoints |
| Morning Telegram brief | brief.py + APScheduler CronTrigger 22:00 UTC (7am JST) + /debug/morning-brief test |
| Chat multi-conversation | Valkey per-conv key scheme, sidebar UI, new/switch/delete/clear, legacy auto-migration |
| Ghibli countdown tile | Amber/green countdown on /city/tokyo |
| Weather day planner | 5-day outdoor score (Great/OK/Rainy) on dashboard + all city pages |
| Reddit gateway first-use | Validation report: search behavior documented, Nara + Osaka intel compiled |
| Pre-existing wishlist bug | shogun_app had zero grants on wishlist_items — fixed with full CRUD grants |
| GitHub push | develop branch pushed — 17 commits now on origin/develop |
| AI calendar management (web chat) | Gemini function calling: 6 tools (get/update itinerary, checklist, knowledge, POIs). Tool action badge in chat. Notes write to notes_ja. PATCH endpoint. | Web UI | ✅ Completed 2026-03-17 | 2026-03-17 |
| Calendar + planning page SSR fix | force-dynamic on calendar and city pages. Planning page: remove dead api.planning.itinerary() call. | Web UI | ✅ Completed 2026-03-17 | 2026-03-17 |
| LegCard description + notes display | Non-compact view shows description (grey) and notes (amber badge). | Web UI | ✅ Completed 2026-03-17 | 2026-03-17 |
| Dashboard sakura dedup + white banner | Removed BlossomWidget duplicate; SakuraStatus transparent background. | Web UI | ✅ Completed 2026-03-17 | 2026-03-17 |
| Tokyo knowledge seeding | 100 records across shopping, skincare, temples, food, museum categories. | Data Lake | ✅ Completed 2026-03-17 | 2026-03-17 |
| checklist_items migration | 15 packing items seeded. shogun_app grants on checklist_items + knowledge_items. | Database | ✅ Completed 2026-03-17 | 2026-03-17 |

## Active Work — Pre-Trip (Departure Mar 23, 7 days)

| Item | Description | Phase | Status | Last Updated |
|------|-------------|-------|--------|--------------|
| **Cloudflare Tunnel + Access** | Public access to shogun.ibbytech.com from Japan. cloudflared container → web-ui. Google IdP auth. Todd must move DNS first — 24-48h propagation. | Public Access | Blocked: Todd DNS + GCP | 2026-03-16 |
| **Laptop reliability** | Windows power settings (no sleep on AC), Docker Desktop auto-start, Windows Update maintenance window 3-5am. Must be done before Mar 23. | Ops | Not started | 2026-03-16 |
| **Brenda + Madeline onboarding** | Need Telegram IDs + Google emails. Required for user seeding and Cloudflare Access policy. | Ops | Blocked: Todd | 2026-03-16 |
| **Remaining dashboard tiles** | AQI (WAQI), JPY/USD (frankfurter.app), transit disruption alerts (Tavily), what's-on-this-weekend (Tavily), Windy radar embed. | Web UI | ✅ Completed 2026-03-16 | 2026-03-16 |
| **Knowledge pipeline + Research interface** | knowledge_items table, anchor model, 3 entry points, cost controls. Taxonomy session: Tuesday 2026-03-18 after Brenda trip details. | Data Lake | Blocked: taxonomy session | 2026-03-16 |
| **RAG pipeline update** | shogun-core to query knowledge_items alongside trip_pois for richer responses | Data Lake | Blocked: knowledge_items schema | 2026-03-16 |
| Reddit Gateway Phase 1 | DB setup (pgvector, reddit schema, reddit_app user), .env Docker Desktop fixes, add to start script | Platform Phase 1 | Not started — no blockers | 2026-03-16 |
| shogun-places-ingester | Add docker-compose.yml, wire up to platform_net, one-shot run for 6 location anchors | Platform Phase 2 | Not started | 2026-03-16 |
| YouTube Data API | Integration deferred — Todd still needs to obtain API key | Feature | Blocked: Todd | 2026-03-16 |
| Printable itinerary | Standalone bilingual HTML — full trip details | MVP 6 | Not started | 2026-03-16 |

## Chatbot Regression — ✅ Resolved 2026-03-15

Root cause: DB connectivity broken post-Docker-Desktop migration + system prompt build failure.
Fixed: `build_system_prompt()` DB query guards, LLM gateway URL corrected, Valkey connectivity confirmed.
Evidence: `outputs/validation/2026-03-15_chatbot-regression-fix_report.md`
AI enrichment (time, weather, Tavily RAG): `outputs/validation/2026-03-15_chatbot-enrichment_report.md`

## Knowledge Pipeline Architecture (Decided 2026-03-15)

### Core concept
Three workflows → one table → RAG at query time.
Pre-trip bulk loader + Web UI Research tab + Telegram `/research` + persistent chat saves all write to `knowledge_items`.

### knowledge_items schema (approved)
```sql
knowledge_items (
  id              SERIAL PRIMARY KEY,
  anchor          TEXT,        -- explicit anchor: 'osaka-airbnb', 'nara-park', 'kanazawa-hotel', 'tokyo-sugamo', 'ghibli-museum', 'usjapan', NULL for interest-based
  city            TEXT,        -- 'osaka', 'nara', 'kanazawa', 'tokyo'
  category        TEXT,        -- 'restaurant', 'toilet', 'pharmacy', 'connectivity', 'interest', 'sakura', 'events', 'practical'
  topic           TEXT,
  source_url      TEXT,
  content_summary TEXT,
  raw_content     TEXT,
  tavily_score    FLOAT,       -- relevance score from Tavily, for threshold filtering
  ingested_utc    TIMESTAMPTZ DEFAULT now()
)
```

### Location anchors (6 defined)
| Anchor key | Location | Categories to pre-populate |
|------------|----------|---------------------------|
| osaka-airbnb | Tenjinbashisuji 6-chome, Kita-ward | Restaurant, toilet, pharmacy, convenience, connectivity, vintage/interest |
| nara-park | Kintetsu Nara Station / Nara Park entrance | Restaurant, toilet, nearby temples |
| usjapan | Universal Studios Japan entrance | Restaurant, pharmacy |
| kanazawa-hotel | Hotel Sanraku Kanazawa | Restaurant, toilet, pharmacy, morning market |
| tokyo-sugamo | Sugamo, Toshima-ku | Restaurant, toilet, pharmacy, convenience, local market |
| ghibli-museum | Mitaka, Tokyo | Restaurant nearby, transit from Sugamo |

### Interest-based category (anchor-independent)
Searches like "knife shops Japan", "vintage clothing osaka", "sake breweries kanazawa" are NOT tied to a radius anchor. These use `anchor=NULL`, `category='interest'`, `city` set to relevant city. These can be destination-generating — the data lake should surface them to the AI for recommendation.

### Auto-save strategy
- Tavily results above relevance threshold → auto-save to knowledge_items
- If results are sparse (below threshold or <3 returned) → save everything regardless
- Deduplication: check `anchor + category + source_url` before any API call. If found within 7 days, skip the call.

### Three entry points
1. **Bulk pre-trip loader** — `tools/ingest_knowledge.py --anchor osaka-airbnb --category restaurant` — one-shot per anchor/category, runs on laptop
2. **Web UI Research tab** — free-text input, Tavily + optional Places, shows results, auto-saves on threshold
3. **Telegram `/research [query]`** — Tavily search, stores top results, replies with summary

### Persistent chat saves
When RAG fires during a chat response, Tavily results are checked against knowledge_items and saved if not present. No user action required — every chat query enriches the data lake automatically.

### Cost control model
| Operation | Cost | Cap |
|-----------|------|-----|
| Places Nearby Search | ~$0.032/call | 1 call per anchor/category |
| Places Details | ~$0.017/call | Top 8 results per nearby search only |
| Tavily search | ~$0.042/call | 1 per anchor/category pre-trip; 5 Tavily + 10 Places max per research session during trip |
| Firecrawl | rate-limited | Only for Tavily-surfaced Tabelog URLs |

Pre-trip one-time run estimate: under $10 total.

### Deferred: keyword/category taxonomy
Full list of search terms per anchor/category per city. Planning session Tuesday 2026-03-18 after Brenda provides trip plan details.

## Dashboard Tiles — Approved Set (2026-03-15)

**Main dashboard (all cities):**
- Sakura status — Osaka + Tokyo (Tavily daily search, 6h cache)
- Weather cards per city — current + 5-day (Open-Meteo, 30min cache)
- What's on this weekend — per city (Tavily daily, city-aware)
- Train/transit disruption alerts — JR West/East, Osaka Metro, Tokyo Metro (Tavily, 30min cache)
- AQI per city (WAQI free API, 1h cache)
- JPY/USD exchange rate (frankfurter.app, 1h cache)
- Japan public holiday / calendar event (static + date check)
- Weather radar map (Windy embed iframe — zero code)

**City-specific tabs:**
- All of the above scoped to that city
- POIs near accommodation
- What's on this weekend (city-specific)
- Restaurants + interest-based knowledge_items for that anchor

**LLM leverage:** All tiles share the same cached data layer as the system prompt injection. Weather, sakura, holiday, AQI all flow into both the UI tile and the AI context from one fetch.

**Deferred to post-trip:** Transit timetable/navigation (use Google Maps deeplinks instead), temple ennichi calendar, full knowledge data lake integration into tiles.

## Remote Work from Japan (Decided 2026-03-15)
- Todd plans multiple Claude Code terminal windows open with remote-control activated
- Phone Claude Code app for mobile collaboration
- No automated deployment pipeline needed — git push + manual pull management from terminals
- Data lake ingest: `/research` Telegram command + Web UI Research tab; ingest script triggerable from terminal
- Final knowledge re-run planned for Mar 22 (day before departure)

## Cloudflare Tunnel Plan — Decision Log (2026-03-15)

### Architecture decision
- **Option chosen:** Cloudflare Tunnel + Access (Option C) — public access from Japan
- **Traefik:** NOT needed. cloudflared container proxies directly to `http://shogun-web-ui:3000`
- **Auth:** Cloudflare Access + Google IdP. App keeps `SHOGUN_BYPASS_AUTH=true` — Cloudflare is the auth wall.
- **Flow:** Phone in Japan → shogun.ibbytech.com → Cloudflare edge → Access auth → Tunnel → cloudflared → shogun-web-ui:3000

### What Todd must do first (browser work, no code)
1. **Move ibbytech.com DNS to Cloudflare nameservers** — change in Namecheap → Domain → Nameservers.
   Currently DNS is Namecheap-managed. Cloudflare Access REQUIRES the zone on Cloudflare DNS.
   Allow 24-48h propagation (usually faster). This is the longest lead-time item — do it first.
2. **Cloudflare Zero Trust** — dash.cloudflare.com → Zero Trust → enable free tier (up to 50 users)
   → Networks → Tunnels → Create tunnel → name it `shogun-laptop` → choose Docker connector → copy TUNNEL_TOKEN
   → Add public hostname: `shogun.ibbytech.com` → Service: `http://shogun-web-ui:3000`
3. **Google Cloud Console** — check https://console.cloud.google.com for existing project.
   Need OAuth 2.0 client ID + secret for Cloudflare Access Google IdP.
4. **Cloudflare Access Application** — attach Google IdP, set policy to allow specific Google emails.

### What Claude Code does after Todd has TUNNEL_TOKEN
- Add cloudflared Docker container to `platform/infra/compose/docker-compose.infra.yml`
- One env var: TUNNEL_TOKEN
- Add to start-shogun.ps1 (starts with infra layer)
- Test from phone

## Blockers (Cloudflare)

- **ibbytech.com DNS zone on Cloudflare:** ❌ Currently Namecheap-managed — Todd must move nameservers
- **Cloudflare Zero Trust enabled:** TBD — Todd
- **TUNNEL_TOKEN obtained:** TBD — Todd (from Zero Trust dashboard after creating tunnel)
- **Google Cloud OAuth client ID + secret:** TBD — Todd (check console.cloud.google.com for existing project)
- **Brenda and Madeline Google email addresses:** TBD — needed for Access policy
- **Brenda and Madeline Telegram IDs:** TBD — needed for seeding user profiles

## Laptop Unattended Risk (Mar 23–Apr 9)

| Risk | Mitigation |
|------|------------|
| Windows Update auto-restart | Set maintenance window to 3-5am, disable auto-restart |
| Docker Desktop not starting after reboot | Enable "Start Docker Desktop when you log in" + Windows auto-login |
| Laptop sleeps | Power settings: disable sleep on AC power, screen off is OK |
| Power outage | Nothing to do — acknowledge risk |

## Trip Itinerary Reference

| Leg | Date | City | Title |
|-----|------|------|-------|
| 1-2 | Mar 23 | SFO→LAX→KIX | Flights — arrive Osaka area |
| 3 | Mar 24 | Osaka | Tenjinbashi Queen Airbnb — check in |
| 4 | Mar 25 | Nara | Day trip — deer park, Todai-ji, Kasugataisha |
| 5 | Mar 26 | Osaka | Universal Studios Japan — Nintendo World |
| 6 | Mar 30 | Osaka→Kanazawa | Transit |
| 7 | Mar 30 | Kanazawa | Hotel Sanraku Kanazawa |
| 8 | Apr 1 | Kanazawa→Tokyo | Transit |
| 9 | Apr 1 | Tokyo | Sugamo Airbnb (Toshima-ku) |
| 10 | Apr 3 | Tokyo | Ghibli Museum — Mitaka (TIMED ENTRY NOON) |
| 11 | Apr 9 | Tokyo→SFO | JL2 HND → SFO |
| 14 | Apr 2 | Tokyo | Tokyo National Museum + Ueno Park + Ameyoko |
| 15 | Apr 4 | Tokyo | Sugamo Neighbourhood - Koganji Temple + Jizo-dori |
| 16 | Apr 5 | Tokyo | Shimokitazawa Vintage Shopping |
| 17 | Apr 6 | Tokyo | Harajuku + Omotesando + Shibuya Shopping Day |

POIs seeded: 30 total — osaka(6), tokyo(10), nara(4), kanazawa(4), kyoto(5), sakai(1)
Knowledge items seeded: 100 Tokyo records (shopping, skincare, temples, food, museum)
Checklist items: 15 packing items seeded

## Technology Registry

| Technology | Role in this project | Rationale | Date |
|------------|----------------------|-----------|------|
| Python / FastAPI | shogun-core + shogun-web-api | Consistent with platform services; async-capable | 2026-03-10 |
| Valkey 8.x | Conversation context per user (24h idle TTL) | Apache 2.0, Redis-protocol compatible | 2026-03-10 |
| PostgreSQL 17 | User profiles, itinerary, trip POIs, knowledge items | Platform standard | 2026-03-10 |
| Gemini 2.0 Flash | LLM completions, intent detection, vision, voice transcription | Multimodal | 2026-03-09 |
| Telegram bot | User interface — text, voice, photo, location | Polling mode — no public URL needed | 2026-03-09 |
| Next.js (React SSR) | shogun-web-ui frontend | SSR fast on mobile | 2026-03-13 |
| Cloudflare Access + Google IdP | Web authentication (edge-level) | Auth at edge; app never handles credentials | 2026-03-13 |
| Cloudflare Tunnel (cloudflared) | Public exposure of shogun.ibbytech.com — Docker container | No inbound ports; works with dynamic home IP; NO Traefik needed | 2026-03-15 |
| Open-Meteo | Weather data (free, no API key) | No rate limits; Valkey-cached 30min | 2026-03-13 |
| Tavily | Web search — kanji + English, Tabelog domain search, disruption alerts, sakura, events | TAVILY_API_KEY required | 2026-03-12 |
| WAQI | Air quality index per city | Free API, no key for basic use | 2026-03-15 |
| frankfurter.app | JPY/USD exchange rate | Free, no key, reliable | 2026-03-15 |
| Windy embed | Weather radar map tiles | Free iframe embed, no API | 2026-03-15 |
| IIJmio Japan Travel SIM | Todd's connectivity in Japan — 10GB, Docomo network, 4G | Best rural coverage; buy at KIX arrivals vending machine on landing | 2026-03-15 |

## Decision Log

### Chatbot AI context enrichment — 2026-03-15
- Gap: Neither chatbot has current time, weather, sakura status, or general web search access
- Weather + time: Option A (always-ambient, injected in system prompt)
- Sakura + general web search: Option B (RAG-triggered when user asks)
- Rationale: Weather makes the AI proactively useful ("rain this afternoon — here's what I'd shift indoors"). Sakura is specific-query — RAG is the right pattern.

### Transit/train data — 2026-03-15
- Capability need: Train disruption awareness for trip planning
- Decision: Disruption alerts only via Tavily (targeting JR West, JR East, Osaka Metro, Tokyo Metro status pages). NOT navigation/timetables.
- Navigation: Google Maps deeplinks from the web UI. Keeps cost at zero and leverages the best tool for the job.
- Rationale: Navigation APIs (HyperDia, NAVITIME, Google Transit) are paid. For a family of 3, Google Maps handles it better than any custom integration.

### knowledge_items anchor field — 2026-03-15
- Decision: Explicit `anchor` field in schema (not just `city`)
- Rationale: "10 restaurants in Tokyo" is useless. "10 restaurants within 300m of Sugamo Airbnb" is what the AI needs to give accurate recommendations. Anchor-level indexing enables proximity-aware retrieval.
- Interest-based searches use anchor=NULL, city set — these are destination-generating, not proximity-scoped.

### Knowledge pipeline auto-save strategy — 2026-03-15
- Decision: Auto-save on Tavily relevance threshold; save everything if results sparse
- Rationale: Curation overhead defeats the purpose. Low-relevance results when few exist is better than returning nothing. Quality control comes from deduplication and TTL, not manual review.
- Exception: Web UI Research tab shows results before saving — user can dismiss before commit.

### Remote work during Japan trip — 2026-03-15
- Decision: Multiple Claude Code terminal windows + phone Claude Code app. No automated deploy pipeline.
- Rationale: Todd manages deployment from terminals directly. Simpler, no new infrastructure to fail unattended.
- Data lake work is priority during trip. Ingest triggerable via Telegram command and Web UI.

### Traefik — deferred permanently (pre-trip) — 2026-03-15
- Decision: Traefik will NOT be restored before the Japan trip
- Reasoning: Services communicate via container names on platform_net — no routing needed.
  Cloudflare Tunnel proxies directly to shogun-web-ui:3000 — Traefik adds no value here.
  Complexity/risk not justified with 8 days to departure.
- Re-evaluation: Restore when Proxmox lab is rebuilt post-trip (3-node separation).
  Compose config is already written — it's a re-enable, not a rewrite.

### Cloudflare Tunnel architecture — 2026-03-15
- Capability need: External access to shogun.ibbytech.com from Japan (phones, laptop)
- Options: (A) Traefik + mkcert internal only; (B) Traefik + LAN DNS; (C) Cloudflare Tunnel direct
- Decision: Option C — cloudflared container → shogun-web-ui:3000 directly
- No Traefik required. SHOGUN_BYPASS_AUTH stays true — Cloudflare Access is the auth layer.
- Risk: ibbytech.com DNS must move from Namecheap to Cloudflare. Allow 48h propagation.
- Risk: Laptop unattended for 17 days. Windows reliability mitigations required (see above).

### Laptop as production host — 2026-03-15
- Decision: Windows laptop stays home in California, running Docker Desktop, for Mar 23–Apr 9
- Reasoning: Fastest path. No VPS cost. cloudflared handles dynamic IP and reconnection.
- Risk accepted: Windows Update reboot could take down all services. Mitigation: maintenance window + auto-start config.
- Alternative considered: Hetzner CX22 VPS (~$4/mo). Deferred — user may switch before departure.

## Backlog (Post-trip or deferred)

- **Keyword/category taxonomy** — planning session 2026-03-18 (Tuesday) after Brenda trip details arrive
- **Reddit Gateway** — platform Phase 1, DB setup needed first
- **shogun-places-ingester** — platform Phase 2, post Reddit
- **Full Data Lake Phase 3** — knowledge_items + RAG update, post-schema + keyword taxonomy
- **Temple ennichi calendar** — monthly temple fair dates; needs Japanese calendar research
- **Timed entry reminders** — Ghibli noon entry (already in itinerary, low priority)
- **Daily cultural tip / phrase of day** — LLM-generated, activity-aware, cached daily
- **Tabelog restaurant picks near accommodation** — Tavily+Scraper, post knowledge pipeline
- **Printable bilingual itinerary** — standalone HTML, MVP 6
- **eSIM option documentation** — note for future travelers: activate IIJmio eSIM before departure
- **Proxmox lab rebuild** — post-trip; restore 3-node separation and Traefik

## Planning Documents

| Document | Path | Status |
|----------|------|--------|
| Migration Guide | outputs/planning/migration-guide.md | Complete |
| Disaster Recovery Checklist | outputs/planning/disaster-recovery-checklist.md | Complete |
| Shogun Web Plan | outputs/planning/shogun-web-plan.md | Approved |
| City Theme Specification | outputs/planning/shogun-web-city-themes.md | Approved |
| Coding Agent Execution Brief | outputs/planning/shogun-web-agent-brief.md | Approved |
| Risk Register | outputs/planning/shogun-risks.md | Draft |
| Chatbot Fix + AI Enrichment + Dashboard Tiles | outputs/planning/chatbot-dashboard-enrichment-plan.md | Approved — ready for execution |
