# Plan: All-Nighter — AI Calendar Management + Tokyo Knowledge + Audit
Date: 2026-03-16 (evening)
Status: Approved — Auto-approval active
Target: All green by morning (Pacific time)

## Objective

Six parallel workstreams running tonight:
1. Fix visible bugs (landing page, dashboard tiles)
2. Enter real trip data for Nara + USJ + Tokyo
3. Build AI calendar management (web chat only) — CRITICAL PATH
4. Seed Tokyo knowledge base (shopping, food, temples, museums)
5. Run Playwright audit across entire app
6. Produce final audit report — all green before morning

## Auto-Approval Scope

All code changes, DB writes, container rebuilds, and commits are pre-approved.
No confirmation needed for any action except: DROP TABLE, DELETE FROM (bulk),
force-push to main. Those still require human confirmation.

---

## Team 1 — Landing Page Fixes
**Time estimate:** 30 min
**Branch:** develop (directly — small UI fixes)
**No blockers**

### Tasks
1. **Logo crop fix:** The Shogun Concierge logo in the bottom-left of the hero
   image is being clipped. Adjust `object-position` on the img tag to shift
   up slightly (try `object-position: center 20%` or `center top`) so the full
   logo is visible. Test at multiple viewport sizes.

2. **Enter button — make prominent:** Current pill button is too subtle against
   the dense image. Changes:
   - Increase padding: `1rem 3rem`
   - Increase font size: `1.1rem`
   - Add stronger background: `rgba(0,0,0,0.75)` (darker)
   - Add a subtle glow/shadow: `box-shadow: 0 0 20px rgba(0,0,0,0.5)`
   - Consider white border: `border: 1.5px solid rgba(255,255,255,0.6)`

3. **Remove Login link:** Delete the bottom-right Login link entirely.
   Cloudflare Access handles auth transparently.

### Exit criteria
- Logo fully visible at 1440px and 390px (iPhone) widths
- Enter button clearly readable against the hero image
- No Login link present
- Rebuild container, HTTP 200 on `/`

---

## Team 2 — Dashboard Bug Audit + Fix
**Time estimate:** 1.5–2 hours
**Requires:** Playwright browser inspection
**Branch:** develop

### Tasks

**Step 1 — Playwright inspection:** Screenshot all dashboard tiles at
`http://localhost:3010/dashboard`. Capture:
- Full page screenshot
- Individual tile screenshots for: SakuraStatus, TransitAlert, AmbientDashboard
- Browser console errors

**Step 2 — TransitAlert fix:** Component is rendering raw API response text
instead of parsed/formatted disruption data. Inspect `TransitAlert.tsx` and
the `/ambient/transit` API response. Fix rendering logic to show:
- Green "No disruptions reported" if clean
- Structured list of disruptions if any (line, severity, description)
- NOT raw JSON or unparsed markdown

**Step 3 — Duplicate sakura fix:**
- Inventory all sakura components: `SakuraStatus.tsx`, `BlossomWidget.tsx`,
  `AmbientDashboard.tsx`, dashboard page, city pages
- Identify which renders the best data (live Tavily results vs. static)
- Keep ONE — the one with live data. Remove the other.
- Fix the white banner issue on the remaining one (likely a div with
  background-color: white that needs to be transparent or removed)

**Step 4 — Loading performance:** All tiles load slowly because they each
make independent API calls sequentially. Investigate:
- Are tiles fetching in parallel or serial?
- Does the API cache responses in Valkey? Check cache TTLs.
- Add loading skeleton states where missing
- If API responses are slow, check if Tavily calls are blocking the response
  (they should be cached — verify cache hits are working)

### Exit criteria
- Playwright screenshots show all tiles rendering correctly
- TransitAlert shows formatted text, not code
- Single sakura tile, no white banner
- No console errors on dashboard load

---

## Team 3 — Calendar + Itinerary Data Entry
**Time estimate:** 1 hour
**Requires:** DB write access via shogun-web-api or direct psql
**Branch:** develop

### Trip data to enter

**Leg 4 — March 24 — Nara Day Trip**
```
title: "Nara — Deer Park & Todai-ji"
city: nara
date: 2026-03-24
description: Full day in Nara. Bus from Osaka (approx 1hr). Approach from
  the backside trail (go down the hill) rather than the main entrance — less
  crowded. Allow 3 hours at the deer park and Todai-ji. Afternoon: shopping
  in the Naramachi district (old merchant quarter). Street food along
  Higashimuki shopping arcade.
notes: Brenda has trail details for backside approach. Buy deer crackers
  (shika senbei) from vendors — ¥200/pack. Kasugataisha Shrine worth a
  short detour from the deer park.
transport: JR Osaka → Nara (approx 50 min, ¥820) or Kintetsu Nara line
  (express, 35 min, ¥680). From Nara station: bus to Todai-ji or 20-min walk.
```

**Leg 5 — March 25 — Universal Studios Japan**
```
title: "Universal Studios Japan — Nintendo World"
city: osaka
date: 2026-03-25
description: Full day at USJ. Tickets already purchased. Priority: Nintendo
  World (Super Nintendo World area). Get there at opening — first train from
  Tenjinbashi-suji 6-chome. Express pass recommended for key attractions.
notes: USJ opens 9:00am most days (check app for exact time Mar 25).
  First train: Osaka Metro Tanimachi Line from Tenjinbashisuji 6-chome
  → Shin-Osaka → JR Yumesaki Line → Universal City station.
  Approx 45 min total, depart ~8:00am to arrive at opening.
transport: Tenjinbashisuji-6 (Tanimachi Line) → Nishi-Umeda/Osaka →
  JR Osaka Loop → Nishikujo → JR Yumesaki Line → Universal City.
  Alternatively: direct bus from Osaka Umeda (Express bus 45 min).
```

**Tokyo legs — verify and update**
Check existing Tokyo legs (Apr 1–9). Ensure these are present:
- Tokyo National Museum (Ueno) — suggest Apr 2 or Apr 4
- Ghibli Museum (Apr 3, noon timed entry — already in DB, verify)
- Sugamo neighborhood exploration (Kōganji Temple / Togenuki Jizo)
- Shibuya / Harajuku shopping day (Brenda priority)
- Shimokitazawa vintage shopping (Brenda priority)

If Tokyo National Museum leg is missing, create it:
```
title: "Tokyo National Museum + Ueno"
city: tokyo
date: 2026-04-02 (suggest — adjust if conflict)
description: Tokyo National Museum (Ueno Park) — largest art museum in Japan.
  Budget 2-3 hours. Ueno Park itself is worth a walk (sakura trees).
  Adjacent: Ameyoko market (outdoor street market, food + goods, 5-min walk
  from museum). Good for street food, snacks, some vintage/thrift.
notes: Museum opens 9:30am, closed Mondays. General admission ¥1,000.
  Ameyoko is free, packed on weekends — go early or late afternoon.
```

### Exit criteria
- Mar 24 leg updated in DB with full Nara data
- Mar 25 leg updated in DB with USJ + transit info
- Tokyo legs reviewed — National Museum present, Ghibli confirmed
- Verify via `/api/calendar` or `/api/itinerary` endpoints returning correct data

---

## Team 4 — AI Calendar Management (CRITICAL PATH — by morning)
**Time estimate:** 3–4 hours
**Branch:** feature/20260316-ai-calendar-tools
**Target:** Working in web chat by morning

### What this builds

The web chat AI (Gemini 2.0 Flash) gains function-calling tools that let it
read and write trip data. User types "what's on the 24th?" or "add a note to
the Nara day: backside trail" and the AI executes it.

### Tools to implement

```python
# Tool 1 — Read itinerary
get_itinerary_legs(city: str | None = None) -> list[leg]
# Returns legs filtered by city, or all legs

# Tool 2 — Update a leg
update_itinerary_leg(leg_id: int, title: str | None, description: str | None, notes: str | None) -> leg
# Partial update — only provided fields are changed

# Tool 3 — Read checklist
get_checklist_items(category: str | None = None) -> list[item]

# Tool 4 — Toggle checklist item
toggle_checklist_item(item_id: int, checked: bool) -> item

# Tool 5 — Search knowledge base
search_trip_knowledge(query: str, city: str | None = None, category: str | None = None) -> list[knowledge_item]
# RAG over knowledge_items table — returns top 5 by relevance

# Tool 6 — Get POIs
get_trip_pois(city: str | None = None, category: str | None = None) -> list[poi]
```

### Implementation approach

**Location:** `app-services/shogun-web/shogun-web-api/routers/chat.py`

Gemini 2.0 Flash supports native function calling. Add tool definitions to
the `/chat` POST endpoint using the Gemini tools API format. On tool_call
response, execute the appropriate DB operation, return result to Gemini for
final response synthesis.

**New DB endpoints needed** (add to existing routers):
- `PATCH /itinerary/legs/{id}` — partial update (title, description, notes)
- `GET /checklist` — already exists (verify)
- `PATCH /checklist/{id}` — toggle checked state

**Chat flow with tools:**
```
1. User sends message
2. Build system prompt (existing — weather, city, etc.)
3. Add tool definitions to Gemini request
4. Gemini responds with either: text reply OR tool_call
5. If tool_call: execute the tool, get result, send back to Gemini
6. Gemini synthesizes final text response including tool result context
7. Return final text to user
8. Include tool_actions array in response so UI can show what changed
```

**UI changes (minimal):**
- After chat response, if `tool_actions` present, show a subtle inline badge:
  "✓ Updated: Nara leg" or "✓ Checked: Passport"
- No page refresh needed for chat — user goes to calendar/checklist to verify

### System prompt additions

Add to the existing system prompt:
```
You have tools available to read and update trip data. Use them when the user
asks about specific days, wants to add notes, or asks to check off packing items.
Always confirm what you did: "I've added that note to the Nara leg."
```

### Exit criteria
- User can type "what's on March 24th?" → AI returns Nara details from DB
- User can type "add note to Nara: bring yen for deer crackers" → leg updated in DB
- User can type "mark passport as packed" → checklist item toggled
- User can type "search for vintage shops near Sugamo" → knowledge_items RAG result
- All 6 tools exercised, results correct
- Playwright test validates all 4 scenarios above

---

## Team 5 — Tokyo Knowledge Seeding
**Time estimate:** 2–3 hours
**Branch:** develop (data seeding script)
**Runs parallel to Team 4**

### Knowledge to seed

**Anchor: tokyo-sugamo** (Sugamo Airbnb, Toshima-ku)
Categories and queries:
- `restaurant` — "best ramen near Sugamo Tokyo", "izakaya Sugamo Toshima"
- `temple` — "Kōganji Temple Sugamo Togenuki Jizo", "Sugamo shopping street temples"
- `pharmacy` — "Matsumoto Kiyoshi Sugamo", "pharmacy Sugamo Tokyo"
- `convenience` — "konbini near Sugamo station"
- `local_market` — "Sugamo Jizo-dori shopping street", "local market Sugamo"

**Anchor: ghibli-museum** (already defined — Mitaka)
- `restaurant` — "restaurants near Ghibli Museum Mitaka"
- `transit` — "how to get to Ghibli Museum from Sugamo"

**New anchor: tokyo-ueno** (National Museum area)
- `museum` — "Tokyo National Museum highlights must see exhibits"
- `market` — "Ameyoko market Ueno food vendors hours"
- `restaurant` — "best restaurants near Ueno Park"
- `sakura` — "Ueno Park sakura 2026 bloom forecast"

**Interest-based (anchor=NULL, city=tokyo):**
- `vintage` — "Shimokitazawa vintage clothing Tokyo best shops 2026"
- `vintage` — "Koenji vintage clothing Tokyo"
- `skincare` — "best skincare shops Tokyo Cosme Matsumoto Kiyoshi Loft Tokyu Hands"
- `skincare` — "Japanese face cream best buys tourist Tokyo"
- `street_food` — "best street food Tokyo Yanaka Ginza vendors 2026"
- `street_food` — "Ameyoko street food what to eat"
- `shopping` — "Harajuku Omotesando shopping guide vintage youth fashion"
- `shopping` — "Don Quijote Tokyo best buys souvenirs"
- `temple` — "Senso-ji Asakusa tips avoid crowds morning"
- `temple` — "lesser known temples Tokyo alternatives to Senso-ji"
- `events` — "Tokyo events late March April 2026 hanami festivals"

### Seeding approach

1. Use existing Tavily gateway (`http://localhost:8084` or platform_net) for web search
2. Use Reddit gateway for each shopping category (r/JapanTravel, r/japanlife)
3. Store results in `knowledge_items` table in `shogun_v1`
4. Deduplicate on `anchor + category + source_url` before insert

Write a one-shot Python script: `tools/seed_tokyo_knowledge.py`
Run it directly on the laptop (connects to localhost:5432 and platform gateways).

### Exit criteria
- `knowledge_items` table has minimum 30 Tokyo records
- At least 5 records for: vintage, skincare, street_food, temple, museum
- All records have valid `source_url`, `content_summary`, `city=tokyo`
- RAG search for "vintage shops Tokyo" returns ≥3 results
- RAG search for "skincare Tokyo" returns ≥3 results

---

## Team 6 — Playwright Full Audit
**Time estimate:** 2 hours (runs after Teams 1–5 complete)
**Branch:** develop

### Audit scope

**Scenario A — 3 Blank Tokyo Days via AI:**
Using the web chat, starting with Tokyo days Apr 4, 5, 6 (assumed open):
1. Ask AI: "What do we have planned for April 4th, 5th, and 6th?"
2. Ask AI: "Find me top shopping spots for vintage clothing in Tokyo and add them to April 4th"
3. Ask AI: "Search for the best street food near Ueno and suggest a morning plan"
4. Ask AI: "What's near the Ghibli Museum for lunch?"
5. Ask AI: "Add a note to April 5th: Shimokitazawa vintage day, meet at station 10am"
6. Verify leg notes updated in DB
7. Screenshot calendar page — verify days show activity

**Scenario B — Knowledge Validation:**
1. Search knowledge_items via API for: vintage, skincare, Ueno, Sugamo restaurant
2. Verify each returns ≥3 results with content_summary populated
3. Verify RAG in chat: ask "find me skincare shops near our hotel" → AI uses knowledge

**Scenario C — Dashboard tiles all green:**
1. Full page screenshot dashboard
2. Verify: weather cards, sakura (single), AQI, exchange rate, transit (no code)
3. No console errors, no white banners, no raw JSON visible

**Scenario D — Calendar + Checklist functional:**
1. Navigate to /calendar — verify Nara (Mar 24) and USJ (Mar 25) show correct data
2. Navigate to /checklist — toggle 2 items via AI chat, verify UI reflects change
3. Navigate to /planning — verify POIs load

### Audit report format
Write to `outputs/validation/2026-03-17_allnighter-audit_report.md`
Each scenario: PASS / FAIL with screenshot reference and evidence.
All 4 scenarios must be PASS before "all green" is declared.

---

## Execution Order + Dependencies

```
NOW (parallel):
  Team 1 — Landing page fixes (independent)
  Team 3 — Calendar data entry (independent)
  Team 5 — Tokyo knowledge seeding (independent)

AFTER Team 1 starts build:
  Team 2 — Dashboard audit (needs running app)

CRITICAL PATH:
  Team 4 — AI calendar management
  └── Blocks Team 6 (Playwright audit needs tools working)

LAST:
  Team 6 — Full Playwright audit (needs all other teams complete)
```

## Planning State Updates Needed After Tonight

- Mark AI calendar management as complete
- Add knowledge_items seeded count to planning state
- Update Tokyo legs in planning state
- Note: Map/planning UI feature is a SEPARATE planning session (multi-day build)
- Note: Rental car change → knowledge pipeline is taxonomy session 2026-03-18
