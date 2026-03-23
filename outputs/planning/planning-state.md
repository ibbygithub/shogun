# Planning State — Shogun
Last updated: 2026-03-22 (conversation audit logging plan approved)

## Project Summary

Shogun is an AI travel concierge for the Ibbotson Japan trip (Mar 23–Apr 9).
Delivered via Telegram (shogun-core) and a web frontend (shogun-web).
The Telegram bot handles live location-aware recommendations; the web app gives
Brenda an itinerary editing surface and all three travelers a unified trip view.

**Current infrastructure: three-node Docker deployment. Laptop is control plane only — Docker Desktop disabled.**
Public access via Cloudflare Tunnel → shogun.ibbytech.com (live as of 2026-03-19).

## Infrastructure — Current State (2026-03-18 three-node migration, verified 2026-03-20)

| Node | Container | Status | Port |
|------|-----------|--------|------|
| brainnode-01 | shogun-core | running | 0.0.0.0:8082 |
| brainnode-01 | shogun-web-api | running | 0.0.0.0:8090 |
| brainnode-01 | shogun-web-ui | running | 0.0.0.0:3010 |
| brainnode-01 | platform-cloudflared | running | (tunnel) |
| svcnode-01 | platform-valkey | running | 0.0.0.0:6379 |
| svcnode-01 | platform-llm-gateway | running | 0.0.0.0:8080 |
| svcnode-01 | platform-telegram-gateway | running | 0.0.0.0:3001 |
| svcnode-01 | platform-tavily | running | 0.0.0.0:8084 |
| svcnode-01 | platform-scraper-api | running | 0.0.0.0:8083 |
| svcnode-01 | platform-reddit-gateway | running | 0.0.0.0:8082 |
| svcnode-01 | platform-places-google | running | 8081 (internal only) |
| dbnode-01 | PostgreSQL 17 | running | shogun_v1 database |

**Traefik:** Disabled. Cloudflare Tunnel proxies directly to shogun-web-ui:3000 on brainnode-01.

## RECOVERY COMPLETE — 2026-03-15 → THREE-NODE MIGRATION COMPLETE — 2026-03-18
✅ All 11 containers running on correct nodes (validated 2026-03-20)
✅ Telegram bot live (polling mode on svcnode-01)
✅ LLM pipeline working (Gemini 2.0 Flash via llm-gateway on svcnode-01)
✅ Web UI accessible at shogun.ibbytech.com (Cloudflare Tunnel live 2026-03-19)
✅ Web AI chat working — 15/15 tool tests passed (2026-03-19)
✅ Database schema applied, Todd seeded (11 itinerary legs, 30 POIs, 8 preferences)
✅ Laptop Docker Desktop disabled — laptop is control plane only

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

## Skill System Initiative — In Progress (2026-03-19)

Plan: `outputs/planning/skill-system-plan.md` (Approved)

### Phase 0: Structural Cleanup — ✅ Complete
- Migrated shogun `.agent/` → `.claude/` (rules 10-12, skills, assets)
- Deleted 8 duplicated files from platform (rules, skills, templates)
- Updated platform CLAUDE.md to reference foundation via `--add-dir`
- Foundation skills migrated to `.claude/skills/<name>/SKILL.md` format

### Day 1 (Mar 19) — ✅ Complete (4/4 skills + 3 reference docs)
| Skill | Repo | Status |
|-------|------|--------|
| team-orchestrator | foundation | ✅ SKILL.md + references/skills-inventory.md |
| google-places-expert | platform | ✅ SKILL.md + references/api-catalogue.md |
| tavily-search-expert | platform | ✅ SKILL.md + references/japan-search-guide.md |
| frontend-design | shogun | ✅ SKILL.md + references/design-system.md |

### Day 2 (Mar 20) — ✅ Complete (4/4 skills + 2 reference docs)
| Skill | Repo | Status |
|-------|------|--------|
| mobile-ux | shogun | ✅ SKILL.md + references/mobile-viewport.md |
| concierge-brain | shogun | ✅ SKILL.md |
| telegram-admin | platform | ✅ SKILL.md |
| llm-gateway-admin | platform | ✅ SKILL.md + references/function-calling.md |

### Day 3 (Mar 21) — ✅ Complete (3/3 skills)
| Skill | Repo | Status |
|-------|------|--------|
| shogun-dba | shogun | ✅ SKILL.md |
| git-lifecycle | foundation | ✅ SKILL.md |
| documentation-standard | foundation | ✅ SKILL.md |

**Skill System Initiative: COMPLETE — All 11 skills delivered across 3 repos.**

### Day 4 (Mar 22) — Data load + dry-run (depends on Day 3 taxonomy)

---

## Conversation Audit Logging — Approved Plan (2026-03-22)

Plan: `outputs/planning/conversation-logging-plan.md`

**Why:** Todd cannot verify AI chatbot resource routing without full request/response
visibility. Departure is Mar 23. This is the observability floor.

### Phases & Exec Briefs
| Phase | Brief | Task | Status |
|-------|-------|------|--------|
| 1 | exec-brief-4 | conversation_logger.py module + Docker volume mount | Not started |
| 2-3 | exec-brief-5 | Text handler + LLM + tools + RAG instrumentation | Not started — depends on Brief 4 |
| 4 | exec-brief-6 | Voice, photo, location, brief handler instrumentation | Not started — depends on Brief 4 |
| 5 | exec-brief-7 | Deploy to brainnode-01 + end-to-end verify | Not started — depends on Briefs 4-6 |

### Architecture
- JSONL files at `/opt/logs/shogun/conversations/` on brainnode-01
- Daily rotation via TimedRotatingFileHandler, 30-day retention
- `contextvars` per-request accumulator — one write at end of request
- 5 log streams: conversation, voice, photo, location, brief
- Full system prompt, full LLM payloads, full tool args/results
- Stdlib only — no new dependencies

---

## Knowledge Pipeline — Approved Plan (2026-03-20)

Plan: `outputs/planning/knowledge-pipeline-plan.md`

### Taxonomy (approved 2026-03-20)
dining, coffee_cafe, craft_beer, shopping, anime_manga, tech_electronics,
skincare, jewelry_artisan, eyewear_prescription, knife_shop, ceramics,
shopping_crafts, sake_brewery, museum, temple, shrine, park, sightseeing,
market, neighborhood, convenience_store

### Traveler interest matrix (settled — do not re-ask)
- Brenda: eyewear (same-day prescription), knives (artisan names known), skincare, handmade jewelry/bazaars, seafood, vegetarian (animal stock ok), convenience store
- Madeline: anime/manga/plushes/stickers, vintage clothing, antiques, chicken+noodles, convenience store
- Todd: vintage clothing, antiques, tech gear (ESP32/robot kits), craft beer, authentic Japanese burger, beef, noodles
- Shared: standing ramen, conveyor sushi, food halls, street food, independent cafes, no fast food chains

### Spatial model (approved)
Tier 1 (anchor-tagged): accommodation zone proximity
Tier 2 (city-tagged, anchor=NULL): destination zones — found via text search on topic

### Phases
| Phase | Task | Status |
|-------|------|--------|
| 0 | Fix search_trip_knowledge: LOWER() city, anchor param, LIMIT 15, relevance order, multi-word | Not started |
| 1a | Osaka ingestion — 38 queries across 6 zones | Not started |
| 1b | Kanazawa/Kyoto/Nara ingestion — 45 queries | Not started |
| 2 | RAG validation — 5 test queries, citation check | Not started |
| 3 | Tokyo expansion | Blocked: Brenda's Tokyo plan |

### Target volumes
Osaka: 130+ items total | Kanazawa: 50+ | Kyoto: 40+ | Nara: 25+
Script: `tools/ingest_knowledge_pipeline.py --city {osaka|kanazawa|kyoto|nara}`

### Critical prerequisite (Phase 0)
City match in search_trip_knowledge uses `=` (case-sensitive) — all Brenda items
(city='Osaka', 'Kyoto', etc.) are currently invisible to the AI. Must fix before ingestion.

---

## Telegram Upgrade — Approved Plan (2026-03-20)

Plan: `outputs/planning/telegram-upgrade-plan.md`

Priority order (3 days to departure):
1. **Phase 0** — `search_trip_knowledge` DB-first in rag.py (2h) — MUST HAVE
2. **Phase 1** — Gemini function calling in text.py, 5 read tools (4-6h) — MUST HAVE
3. **Phase 3a** — Location trigger → find_nearby_places (2h) — HIGH VALUE
4. **Phase 3b/c** — New commands (/pois, /checklist, /brief) + brief upgrade (2h) — HIGH VALUE
5. **Phase 2** — Mutation tools (3h) — can deploy from Japan if needed

Key constraint: 25s LLM gateway timeout. Single tool call per turn, 10s cap on tool executor.

---

## Active Work — Pre-Trip (Departure Mar 23, 4 days)

| Item | Description | Phase | Status | Last Updated |
|------|-------------|-------|--------|--------------|
| **Cloudflare Tunnel + Access** | Public access to shogun.ibbytech.com from Japan. cloudflared container → web-ui. Google IdP auth. DNS moved to Cloudflare, Zero Trust configured, GCP OAuth complete. | Public Access | ✅ Complete 2026-03-19 | 2026-03-19 |
| **Laptop reliability** | Windows power settings (no sleep on AC), Windows Update maintenance window 3-5am. Docker Desktop no longer relevant — laptop is control plane only. | Ops | In progress | 2026-03-20 |
| **Brenda + Madeline onboarding** | Need Telegram IDs + Google emails. Required for user seeding and Cloudflare Access policy. | Ops | Blocked: Todd | 2026-03-16 |
| **Remaining dashboard tiles** | AQI (WAQI), JPY/USD (frankfurter.app), transit disruption alerts (Tavily), what's-on-this-weekend (Tavily), Windy radar embed. | Web UI | ✅ Completed 2026-03-16 | 2026-03-16 |
| **Knowledge pipeline — Phase 0** | Fix search_trip_knowledge query engine (case, anchor, limit, relevance). PREREQUISITE before ingestion. | Data Lake | Not started | 2026-03-20 |
| **Knowledge pipeline — Phase 1** | Bulk Tavily ingestion 83 queries across Osaka/Kanazawa/Kyoto/Nara. Script: tools/ingest_knowledge_pipeline.py | Data Lake | Not started — blocked on Phase 0 | 2026-03-20 |
| **Knowledge pipeline — Phase 2** | RAG validation: 5 test queries, confirm tool_actions badge shows search_trip_knowledge | Data Lake | Not started — blocked on Phase 1 | 2026-03-20 |
| Reddit Gateway Phase 1 | DB setup (pgvector, reddit schema, reddit_app user) — container already running on svcnode-01 | Platform Phase 1 | Not started — no blockers | 2026-03-16 |
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

### Setup — ✅ Complete (2026-03-19)
1. **ibbytech.com DNS → Cloudflare nameservers:** ✅ Done
2. **Cloudflare Zero Trust + Tunnel (`shogun-laptop`):** ✅ Done — public hostname `shogun.ibbytech.com` → `http://shogun-web-ui:3000`
3. **Google Cloud OAuth 2.0:** ✅ Done — client ID + secret configured in Cloudflare Access Google IdP
4. **Cloudflare Access Application:** ✅ Done — Google IdP attached, Access policy active
5. **cloudflared container:** ✅ Running on brainnode-01 — `app-services/compose/docker-compose.shogun.yml`

## Cloudflare Status — ✅ Complete (2026-03-19)

- **ibbytech.com DNS zone on Cloudflare:** ✅ Done — nameservers moved from Namecheap to Cloudflare
- **Cloudflare Zero Trust enabled:** ✅ Done
- **TUNNEL_TOKEN obtained:** ✅ Done — cloudflared container running
- **Google Cloud OAuth client ID + secret:** ✅ Done — GCP OAuth configured
- **Cloudflare Access Application:** ✅ Done — Google IdP attached
- **Brenda and Madeline Google email addresses:** TBD — needed for Access policy
- **Brenda and Madeline Telegram IDs:** TBD — needed for seeding user profiles

## Unattended Risk (Mar 23–Apr 9)

**Production host is brainnode-01 (192.168.71.222) — Docker containers. Laptop is control plane only.**

| Risk | Mitigation |
|------|------------|
| brainnode-01 power loss | Docker restart policies: `unless-stopped` — containers restart automatically |
| brainnode-01 network loss | Cloudflare Tunnel reconnects automatically |
| svcnode-01 power loss | Same `unless-stopped` policy on all platform containers |
| Laptop Windows Update auto-restart | Set maintenance window to 3-5am — laptop only needs to be up for SSH/git operations |
| Laptop sleeps | Power settings: disable sleep on AC power (laptop is control plane — less critical) |

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

### Laptop as production host — SUPERSEDED 2026-03-18
- Original decision (2026-03-15): Windows laptop running Docker Desktop for Mar 23–Apr 9
- Superseded: Three-node migration complete 2026-03-18. All services moved to svcnode-01 + brainnode-01.
- Laptop Docker Desktop permanently disabled. Laptop is control plane (code editing, git, SSH) only.
- Rationale: Three-node lab was restored. Proper architecture supersedes emergency laptop deployment.

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
| Telegram Upgrade Plan | outputs/planning/telegram-upgrade-plan.md | Approved 2026-03-20 |
| Knowledge Pipeline Plan | outputs/planning/knowledge-pipeline-plan.md | Approved 2026-03-20 |
| Skill System Plan | outputs/planning/skill-system-plan.md | Approved — Day 1 complete |
| Migration Guide | outputs/planning/migration-guide.md | Complete |
| Disaster Recovery Checklist | outputs/planning/disaster-recovery-checklist.md | Complete |
| Shogun Web Plan | outputs/planning/shogun-web-plan.md | Approved |
| City Theme Specification | outputs/planning/shogun-web-city-themes.md | Approved |
| Coding Agent Execution Brief | outputs/planning/shogun-web-agent-brief.md | Approved |
| Conversation Logging Plan | outputs/planning/conversation-logging-plan.md | Approved 2026-03-22 |
| Exec Brief 4 — Logger Module | outputs/planning/exec-brief-4-conversation-logger.md | Ready |
| Exec Brief 5 — Instrumentation | outputs/planning/exec-brief-5-instrumentation.md | Ready |
| Exec Brief 6 — Handler Instrumentation | outputs/planning/exec-brief-6-handler-instrumentation.md | Ready |
| Exec Brief 7 — Deploy + Verify | outputs/planning/exec-brief-7-deploy-verify.md | Ready |
| Risk Register | outputs/planning/shogun-risks.md | Draft |
| Chatbot Fix + AI Enrichment + Dashboard Tiles | outputs/planning/chatbot-dashboard-enrichment-plan.md | Approved — ready for execution |
