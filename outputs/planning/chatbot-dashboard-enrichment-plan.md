# Plan: Chatbot Fix + AI Enrichment + Dashboard Tiles
Date: 2026-03-15
Status: Approved — ready for execution

## Objective

Repair the chatbot regression introduced by the Docker Desktop migration, enrich both
chatbots with real-time context (time, weather, sakura, web search), and build a set
of live dashboard tiles on the web UI that give the family ambient situational awareness
for the Japan trip without having to ask the AI.

## Scope

**In scope:**
- Diagnose and fix chatbot persona + memory on both Telegram (shogun-core) and web UI (shogun-web-api)
- Add JST time, weather, sakura, and general Tavily web search to both chatbot system prompts
- Dashboard tiles: sakura status, weather cards, transit disruption alerts, AQI, exchange rate, weather radar, public holiday, what's-on-this-weekend

**Out of scope:**
- knowledge_items table / data lake (separate plan — awaiting keyword taxonomy session Tuesday)
- Reddit Gateway (separate task)
- Cloudflare Tunnel (blocked on Todd browser work)
- Navigation / transit timetables (Google Maps deeplinks only)

## Current State

- 10 containers running on Docker Desktop (Windows laptop)
- Both chatbots broken: returning "I am an AI chatbot" instead of Japan persona
- Valkey wired in both chatbots but runtime connectivity unconfirmed post-migration
- shogun-web-api already has `weather.py` (Open-Meteo) — not yet exposed to dashboard or chat
- No dashboard tiles exist yet — dashboard shows itinerary and POI data only

## Proposed Approach

Three sequential phases. Phase 1 must complete and go green before Phase 2 starts.
Phase 3 (dashboard tiles) can proceed in parallel with Phase 2 if two agents are available,
since they touch different codebases (shogun-core vs shogun-web).

Shared data layer principle: every tile data source must also be available as a cached
endpoint on shogun-web-api so the AI system prompt can consume the same data the UI
displays. One fetch, two consumers.

---

## Phase 1 — Chatbot Regression Diagnosis and Fix

**Goal:** Both chatbots restored to Japan persona with working conversation memory.

**Entry criteria:** Containers running. SSH or Docker exec access available.

**Deliverables:**
- `tools/verify_chatbot.py` — diagnostic script, runnable against live containers
- All checks green
- Evidence record: `outputs/validation/2026-03-15_chatbot-regression-fix_report.md`

**Checks to implement in verify_chatbot.py:**

| Check | Target | Pass condition |
|-------|--------|----------------|
| DB connectivity | shogun-core container | Returns user record for Todd (user_id=1) |
| System prompt content | shogun-core | Non-empty, contains "Japan" and persona language |
| LLM gateway reachability | shogun-core container | HTTP 200 on health endpoint |
| Live persona test | shogun-core → LLM gateway | Response contains Japan context, no "AI chatbot" self-intro |
| Valkey round-trip | shogun-core | Write test key, read it back, delete |
| Memory persistence | shogun-core | Send 2-turn conversation, confirm second turn references first |
| LLM gateway reachability | shogun-web-api container | HTTP 200 on health endpoint |
| Web UI persona test | shogun-web-api → LLM gateway | Response contains Japan concierge context |
| Valkey round-trip | shogun-web-api | Same pattern, `shogun:web:` key namespace |
| Web UI memory persistence | shogun-web-api /chat endpoint | 2-turn test, confirm memory |

**Fix strategy (execute after failures identified):**
- DB broken → check DATABASE_URL env var in shogun-core container, verify platform-postgres reachable
- LLM gateway unreachable → check LLM_GATEWAY_URL env var, verify port (confirm 8080 vs other)
- System prompt empty → trace build_system_prompt() with test user, check None-guard on user object
- Valkey unreachable → check VALKEY_URL env var in both containers, verify platform-valkey reachable
- Memory not persisting → check context key format, TTL being set on save

**Exit criteria:** All 10 checks green. Evidence record written.

---

## Phase 2 — AI Real-Time Context Enrichment

**Goal:** Both chatbots know current JST time, weather for today's city, and can answer
sakura / general web questions with live data.

**Entry criteria:** Phase 1 complete and green.

**Deliverables:**
- Updated `shogun-core/app/services/llm.py` — time + weather in system prompt
- Updated `shogun-core/app/services/weather.py` — new Open-Meteo service (if not present)
- Updated `shogun-core/app/services/rag.py` — sakura + general web search trigger keywords
- Updated `shogun-web-api/routers/chat.py` — time + weather in system prompt
- Updated `shogun-web-api/routers/weather.py` → wired to chat system prompt build
- Evidence record: `outputs/validation/2026-03-15_chatbot-enrichment_report.md`

**Changes by enrichment type:**

### Time (both chatbots)
- shogun-core: already injects today's date in JST. Add current time: `%H:%M JST`
- shogun-web-api: hardcoded system prompt. Add dynamic time injection at request time.
- One line change in each. No caching needed — time is read at request time.

### Weather (both chatbots) — Option A: ambient injection
- shogun-core: add `weather.py` service that calls Open-Meteo for current city coordinates.
  Current city derived from `db.get_city_for_date(today_jst)` (already exists).
  Cache result in Valkey at key `shogun:weather:{city}` with 30-minute TTL.
  Inject into system prompt: current conditions + today's high/low + precipitation chance.
- shogun-web-api: `weather.py` already exists. Wire it to `build_system_prompt()` equivalent.
  Cache in Valkey same pattern.
- City coordinates (for Open-Meteo):

| City | Lat | Lon |
|------|-----|-----|
| osaka | 34.6937 | 135.5023 |
| nara | 34.6851 | 135.8048 |
| kanazawa | 36.5613 | 136.6562 |
| tokyo | 35.6762 | 139.6503 |

### Sakura + general web search (both chatbots) — Option B: RAG trigger
- shogun-core: extend RAG keyword trigger list in `rag.py` to include sakura/nature terms:
  `sakura`, `cherry blossom`, `hanami`, `bloom`, `season`, `spring`, `flower`
- Lift Tabelog domain restriction for non-restaurant queries. Restaurant queries keep
  `domain:tabelog.com`. Sakura/general queries use unrestricted Tavily search.
- shogun-web-api: add Tavily service (not currently present). Wire to chat handler with
  same keyword detection. On trigger: call Tavily, inject results into messages before
  LLM call, save results to cache for future queries.
- Tavily endpoint: `http://platform-tavily:8000` (container name on platform_net).
  Check actual port in platform tavily service config.

**System prompt additions (both chatbots):**
```
Current time: {HH:MM} JST
Today's weather in {city}: {conditions}, {temp_c}°C (high {max_c}°C / low {min_c}°C),
precipitation {precip_mm}mm. {brief forecast note if available.}
```

**Exit criteria:**
- Both chatbots respond with Japan persona ✓ (from Phase 1)
- Ask "what time is it?" → correct JST time in response
- Ask "what's the weather like today?" → Open-Meteo data in response
- Ask "are the cherry blossoms blooming in Osaka?" → Tavily live result in response
- Evidence record written

---

## Phase 3 — Dashboard Tiles

**Goal:** Live ambient data tiles on the shogun-web dashboard.

**Entry criteria:** Phase 1 complete. (Phase 3 can run in parallel with Phase 2.)

**Architecture principle:** Each tile is a cached API endpoint on shogun-web-api.
The frontend fetches from these endpoints. The same endpoints feed the AI system
prompt where applicable. One fetch, two consumers.

**All new endpoints live under `/api/ambient/` on shogun-web-api.**

---

### Tile Group A — Quick wins (1-2 hrs total)

These have trivial or zero API integration. Build these first.

#### Weather radar map
- **Implementation:** Windy.com embeddable iframe. No API, no code beyond the React component.
- **Component:** `<WindyMap city={city} lat={lat} lon={lon} />` — renders iframe with Windy embed URL
- **Cities:** One map per city on city tab. Osaka default on dashboard.
- **Effort:** 30 min

#### JPY/USD exchange rate
- **API:** `https://api.frankfurter.app/latest?from=JPY&to=USD` — free, no key
- **Endpoint:** `GET /api/ambient/exchange-rate` — Valkey cached 1h
- **Tile:** Single line "¥1,000 ≈ $X.XX" with last updated timestamp
- **Effort:** 30 min

#### Japan public holiday / calendar event
- **Data:** Static lookup table of Japanese public holidays + notable annual events
  (Vernal Equinox Day is Mar 20 — the family will be in Osaka just after this).
  Encode as JSON in the service, no external API needed.
- **Endpoint:** `GET /api/ambient/calendar-event` — returns today's holiday/event or null
- **AI injection:** If holiday exists, inject into system prompt: "Today is [holiday] — expect crowds at popular sites."
- **Effort:** 30 min

---

### Tile Group B — Weather cards (1 hr)

- **API:** Open-Meteo — already in shogun-web-api `weather.py`. Already approved, no key.
- **Endpoint:** `GET /api/ambient/weather/{city}` — returns current conditions + 5-day forecast.
  Valkey cached 30 min. This is the SAME endpoint wired into Phase 2 AI system prompt.
- **Tile:** Card per city — icon, current temp, high/low, precip chance, 3-day forecast strip.
- **Dashboard:** Card for each trip city (Osaka, Kanazawa, Tokyo). City tab: full 5-day.
- **Effort:** 1 hr (endpoint + UI component)

---

### Tile Group C — Tavily-powered tiles (3-4 hrs)

These follow the same pattern: Tavily search → parse → Valkey cache → endpoint → UI tile.
Build a shared `tavily_ambient.py` service that all three tiles call.

#### Sakura status — Osaka + Tokyo
- **Search queries (run once per 6h, cached in Valkey):**
  - `"桜 開花状況 大阪 2026"` (Osaka bloom status Japanese)
  - `"cherry blossom forecast osaka 2026"`
  - `"桜 開花状況 東京 2026"` (Tokyo bloom status Japanese)
  - `"cherry blossom forecast tokyo 2026"`
  - Run both JP + EN, merge results for richer coverage
- **Endpoint:** `GET /api/ambient/sakura/{city}` — returns summary text + source URLs
- **Tile:** Status card per city — bloom stage (budding / partial / peak / falling), forecast peak date, brief summary
- **AI injection:** Inject sakura status for today's city into system prompt daily
- **Effort:** 1.5 hrs

#### Transit disruption alerts
- **Search queries (30-min cache — disruptions are time-sensitive):**
  - Osaka: `"JR West disruption OR delay OR service notice site:jr-odekake.net OR site:osaka-metro.co.jp"`
  - Tokyo: `"JR East disruption OR delay site:jreast.co.jp OR site:tokyometro.jp"`
- **Endpoint:** `GET /api/ambient/transit/{city}` — returns list of active notices or empty
- **Tile:** Alert banner if disruption active, green "All clear" if not
- **Note:** Do NOT attempt to replicate navigation. If disruption found, show deeplink to Google Maps.
- **Effort:** 1 hr

#### What's on this weekend
- **Search queries (6h cache — weekend events don't change hourly):**
  - Trip-date-aware: compute which weekend of the trip is current
  - `"osaka events this weekend march 2026 free outdoor market"` (city-specific)
  - `"tokyo events this weekend april 2026 festival park"` etc.
- **Endpoint:** `GET /api/ambient/events/{city}` — returns list of events with name, date, type, free/paid
- **Tile:** Event cards — name, date, type tag (free / market / festival / museum), brief note
- **Dashboard:** Top 3 events per city. City tab: full list.
- **Effort:** 1.5 hrs

---

### Tile Group D — AQI (1 hr)

- **API:** WAQI (World Air Quality Index) — `https://api.waqi.info/feed/{city}/?token=demo`
  Demo token works for moderate usage. Register for free token if rate limits hit.
- **Endpoint:** `GET /api/ambient/aqi/{city}` — returns AQI number + category (Good/Moderate/Poor)
  Valkey cached 1h.
- **Tile:** AQI number with color coding (green/yellow/red) + one-line interpretation
- **AI injection:** If AQI > 100 (Moderate+), inject into system prompt: "Air quality is moderate/poor today in {city} — factor this into outdoor recommendations."
- **Effort:** 1 hr

---

## Build Sequence for Tonight

Recommended execution order given a single agent:

```
1. verify_chatbot.py (Phase 1 diagnostic) — run, identify failures
2. Fix failures found — iterate until all 10 checks green
3. Phase 2 — time injection (trivial, do this first within Phase 2)
4. Phase 2 — weather injection (Open-Meteo, Valkey cache)
5. Phase 2 — sakura + Tavily RAG extension
6. Phase 3 Group A — Windy radar, exchange rate, public holiday (quick wins)
7. Phase 3 Group B — weather cards (shares Open-Meteo work from Phase 2)
8. Phase 3 Group C — sakura tile (shares Tavily work from Phase 2)
9. Phase 3 Group C — transit disruption alerts
10. Phase 3 Group C — what's on this weekend
11. Phase 3 Group D — AQI
```

Steps 7-8 share significant infrastructure with Phase 2 — if Phase 2 is done well,
the dashboard tile is mostly a UI layer on top of already-working endpoints.

## Recommended Parallel Split (if two agents available)

| Agent A | Agent B |
|---------|---------|
| Phase 1: verify + fix (shogun-core + shogun-web-api) | Phase 3A: Windy radar, exchange rate, public holiday |
| Phase 2: AI enrichment (shogun-core + shogun-web-api) | Phase 3B+C+D: weather cards, sakura, transit, events, AQI |

**File scope — Agent A:** `shogun-core/app/services/`, `shogun-web-api/routers/chat.py`, `tools/verify_chatbot.py`
**File scope — Agent B:** `shogun-web-api/routers/` (new ambient router), `shogun-web-ui/` (new tile components)
**Shared file — coordinate:** None. These are cleanly separated.

## Dependencies

- platform-tavily container must be reachable from shogun-web-api (currently only shogun-core calls it)
- Tavily API key must be in shogun-web-api `.env` (currently only in shogun-core)
- Valkey must be reachable from both containers (Phase 1 will confirm this)
- Open-Meteo: no key needed — direct HTTPS call from container

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM gateway port wrong in shogun-web-api .env | Medium | High | Phase 1 diagnostic will surface immediately |
| Tavily not reachable from shogun-web-api container | Low | Medium | Check platform_net membership in docker-compose |
| WAQI demo token rate-limited | Low | Low | Register free account — takes 2 min |
| Windy embed blocked by CSP headers on shogun-web-ui | Low | Low | Add frame-src to next.config.js |
| Weather tile + AI enrichment both calling Open-Meteo in parallel | Low | Low | Ensure both use same Valkey cache key |

## Open Items

- Confirm Tavily service port (planning state says `http://platform-tavily:8000` — verify in platform docker-compose)
- Confirm LLM gateway port in shogun-web-api `.env` (currently `http://platform-llm-gateway:8080` — verify)
- WAQI free token registration (optional — demo token works for low volume)
- Weather tile city coordinates table — add to shogun-web-api config (Osaka, Kanazawa, Tokyo, Nara)

## Out of Scope

- knowledge_items table and data lake (separate plan, awaiting taxonomy session Tuesday)
- Reddit Gateway (separate platform task)
- Cloudflare tunnel (blocked on Todd)
- Navigation / transit timetables
- Daily cultural tip / phrase of day (post-trip backlog)
- Printable itinerary (post-trip backlog)
