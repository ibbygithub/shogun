# Plan: Shogun-Core Telegram Capability Upgrade
Date: 2026-03-20
Status: Approved

## Objective

Bring shogun-core (Telegram bot) to full feature parity with shogun-web-api's AI
toolset, plus maximize the unique capabilities Telegram provides. The web UI chat
has Gemini function calling with 6 structured tools and 710 knowledge_items accessible
via `search_trip_knowledge`. The Telegram bot has none of that — it runs keyword-
triggered Tavily RAG only. This plan closes that gap before departure (Mar 23).

---

## Current State

**shogun-core architecture (as-audited 2026-03-20):**

`text.py` → `rag.py` (keyword detection) → Tavily → LLM injection
No function calling. No DB knowledge search. No find_nearby_places. No itinerary
mutations. No checklist. Static trip schedule hardcoded in system prompt.

**6 commands:** /help, /status, /quiet, /active, /translate, /reset
**RAG keywords:** food/restaurant terms → Tabelog-restricted Tavily; event/sakura terms → open Tavily
**DB reads:** users, user_preferences, trip_itinerary, trip_pois (top 8 by city), city lookup
**Multimodal:** voice OGG transcription, photo analysis (both via Gemini)
**Location:** 150m + 5min cooldown trigger → 200-token proximity response
**Morning brief:** APScheduler CronTrigger 22:00 UTC (7am JST) Mar 16–Apr 9

---

## Gap Matrix

| Tool / Capability | Web UI | Telegram | Gap |
|---|---|---|---|
| search_trip_knowledge (710 items) | ✅ function call | ❌ absent | **Critical** |
| find_nearby_places (Google Places) | ✅ function call | ❌ absent | **Critical** |
| web_search (Tavily direct) | ✅ function call | ⚠️ keyword RAG only | Partial |
| get_itinerary | ✅ function call | ⚠️ system prompt inject only | Partial |
| get_trip_pois | ✅ function call | ⚠️ system prompt inject (top 8) | Partial |
| update_itinerary_leg (notes) | ✅ via PATCH | ❌ absent | Major |
| checklist_get / checklist_toggle | ✅ | ❌ absent | Major |
| search_trip_knowledge case fix (LOWER()) | ✅ committed | ❌ not in shogun-core | **Critical** |
| Voice transcription | — | ✅ native | Telegram-unique |
| Photo analysis | — | ✅ native | Telegram-unique |
| Location triggers | — | ✅ running | Telegram-unique |
| Translate mode | — | ✅ running | Telegram-unique |
| Morning brief | — | ✅ running | Telegram-unique |
| /pois command | — | ❌ absent | Gap |
| /checklist command | — | ❌ absent | Gap |

---

## Architecture Decision: Function Calling vs RAG Extension

**Option A — Extend RAG (rag.py only):**
Add knowledge_items DB query to rag.py, keeping the existing keyword-detection path.
Fast to ship. Closes the search_trip_knowledge gap. Leaves find_nearby_places, itinerary
mutations, and checklist out of reach — those require tool execution.

**Option B — Gemini Function Calling (full port):**
Add a tool-calling loop to text.py: send user message + tool definitions to Gemini,
execute returned tool_calls, feed results back, get final response. Identical pattern
to web UI. Closes all gaps. Bigger change but unlocks the full platform surface.

**Decision: Phase 0 = Option A (fast), Phase 1 = Option B (full).**

The 25s LLM gateway timeout is the binding constraint. Function calling adds a
round-trip (Gemini → executor → Gemini). To stay safe, limit Phase 1 to a single
tool call per turn (no chained calls). If the tool call times out, fall through to
plain LLM. This matches the web UI behavior in practice.

---

## Scope

**In scope:**
- Phase 0: search_trip_knowledge added to rag.py (DB-first, Tavily fallback)
- Phase 1: Gemini function calling in text.py — read tools only (5 tools)
- Phase 2: Mutation tools — itinerary notes + checklist
- Phase 3: Telegram-unique enhancements — location upgrade, new commands, brief

**Not in scope:**
- Photo-to-knowledge-base auto-ingestion (post-trip)
- Reddit integration in Telegram (post-trip)
- MCP tool calling (deferred post-MVP per CLAUDE.md)
- Conversation persistence in Postgres (deferred post-MVP)

---

## Phase 0: search_trip_knowledge — DB-first RAG

**Goal:** Telegram bot can query the 710-item knowledge_items table before calling Tavily.
The keyword RAG path is extended: DB search first → if results → inject as context → LLM.
Tavily fires only when knowledge_items returns nothing relevant.

**Entry criteria:** None. Can start immediately.

**Files modified:**
- `app-services/shogun-core/app/db.py` — add `search_trip_knowledge(city, query, anchor=None)`
- `app-services/shogun-core/app/services/rag.py` — call DB search first in food/place branch

**Deliverables:**
- `search_trip_knowledge()` in db.py — exact port of the fixed version in shogun-web-api chat.py:
  LOWER() city match, OR token logic, stopword filter, anchor filter, LIMIT 15, relevance ordering
- rag.py updated: food/place query path checks DB first, formats results as context block, falls
  through to Tavily if DB returns nothing
- Functional test: "craft beer near osaka airbnb" via Telegram returns relevant results from DB

**Exit criteria:**
- Tested live via Telegram: food/place query returns knowledge_items context
- Tavily only fires when DB search returns 0 results
- No regression on event/sakura queries (those bypass DB search)

**Complexity:** Low
**Risk:** Low — additive change to rag.py, no changes to text.py or LLM gateway call

---

## Phase 1: Gemini Function Calling (Read Tools)

**Goal:** text.py uses Gemini function calling to execute structured tools dynamically.
The LLM decides which tool to call based on user intent — no more hardcoded keyword
matching. All 5 read tools available.

**Entry criteria:** Phase 0 complete (Phase 0 DB function is reused here).

**Tools to port (identical definitions to web UI):**

| Tool | Source | DB/API call |
|---|---|---|
| `search_trip_knowledge` | db.py (Phase 0) | knowledge_items ILIKE query |
| `find_nearby_places` | Google Places gateway | `places.platform.ibbytech.com` |
| `web_search` | Tavily gateway | `tavily.platform.ibbytech.com` |
| `get_trip_pois` | db.py existing | trip_pois by city |
| `get_itinerary` | db.py existing | trip_itinerary by date range |

**Files modified:**
- `app-services/shogun-core/app/services/tools.py` — NEW: tool definitions (JSON schema) + executor
- `app-services/shogun-core/app/handlers/text.py` — replace `rag_respond()` call with function-
  calling loop; RAG path becomes fallback for non-tool queries

**Execution flow:**
```
user message → LLM call with tool definitions
  → tool_call returned → execute tool → inject result
  → second LLM call → final response to user
  (if no tool_call → single LLM call, no change)
  (if timeout → fall back to plain LLM)
```

**Telegram response formatting:**
- Strip markdown tables (render poorly on mobile)
- Keep bulleted lists (render fine in Telegram)
- Truncate at 1,200 chars — Telegram max is 4,096 but wall-of-text is unusable on phone
- Prefix tool-triggered responses with subtle context indicator (optional — evaluate in testing)

**Exit criteria:**
- "Craft beer near the Osaka Airbnb" → calls search_trip_knowledge, returns DB results
- "What's within 5 min walk of the hotel?" → calls find_nearby_places
- "Any big events this weekend in Kanazawa?" → calls web_search
- "What's on our itinerary for Apr 3?" → calls get_itinerary
- All queries respond within 25s (LLM timeout)
- Voice messages (already transcribed) route through function calling transparently

**Complexity:** Medium
**Risk:** Medium — 25s timeout is binding. Single tool call per turn is the mitigation.
If tool execution takes >8s (Places API cold), second LLM call may fail. Add timeout
guard: if tool executor exceeds 10s → skip tool result, call plain LLM.

---

## Phase 2: Mutation Tools

**Goal:** Telegram bot can update itinerary notes and toggle checklist items. This
mirrors the web UI chat behavior where Brenda can say "add a note to our Ghibli day."

**Entry criteria:** Phase 1 complete.

**Tools to add:**

| Tool | Operation | DB target |
|---|---|---|
| `update_itinerary_leg` | Write notes_en to an itinerary leg | trip_itinerary PATCH via db.py |
| `checklist_get` | Return checklist status | checklist_items SELECT |
| `checklist_toggle` | Toggle checked state | checklist_items UPDATE |

**Files modified:**
- `app-services/shogun-core/app/services/tools.py` — add 3 tool definitions + executors
- `app-services/shogun-core/app/db.py` — add `update_itinerary_notes()`, `get_checklist()`, `toggle_checklist_item()`

**Note on write access:** shogun-core currently uses `shogun_app` which has confirmed
grants on checklist_items and trip_itinerary (verified 2026-03-17). No schema changes needed.

**Exit criteria:**
- "Add a note to the Ghibli day — bring the Mitaka address" → itinerary leg updated, confirmed in reply
- "What's on our packing checklist?" → returns checklist with checked/unchecked status
- "Mark passport as packed" → toggles item, confirms in reply

**Complexity:** Low-Medium
**Risk:** Low — write access confirmed, operations are simple and reversible

---

## Phase 3: Telegram-Unique Enhancements

**Goal:** Capitalize on features only Telegram provides. Location triggers get meaningfully
upgraded. New convenience commands added. Morning brief delivers more value.

**Entry criteria:** Phase 1 complete (Phase 2 can run in parallel).

### 3a: Location Trigger Upgrade

**Current:** 150m proximity trigger → 200-token hardcoded response mentioning the area.
**Target:** 150m trigger → calls `find_nearby_places` for real walking-distance options
from the exact GPS coordinates, returns top 3 results (category: restaurant/cafe/convenience)
with distance and opening hours.

**File:** `app-services/shogun-core/app/handlers/location.py`

### 3b: New Commands

| Command | Behavior |
|---|---|
| `/pois` | Returns top 8 POIs for today's city — formatted as a bulleted list |
| `/checklist` | Returns packing checklist — checked items greyed, unchecked bold |
| `/brief` | Manual trigger for the morning brief — same output as 7am, on demand |
| `/research [query]` | Explicit knowledge + Tavily search — stores results to knowledge_items |

`/pois` and `/checklist` read from DB directly (no LLM involved — fast, deterministic).
`/brief` reuses `brief.py` output.
`/research` runs the full RAG + Tavily pipeline, stores results if relevance > 0.5.

**File:** `app-services/shogun-core/app/commands/system.py`

### 3c: Morning Brief Upgrade

**Current:** brief.py sends itinerary + POIs + generic greeting.
**Target additions:**
- Today's weather (already available via get_weather_for_city — just not in the brief)
- Checklist reminder if any high-priority items unchecked (passport, JR pass, etc.)
- 1–2 knowledge_items relevant to today's city (query: top 2 by ingested_utc for today's city)

**File:** `app-services/shogun-core/app/services/brief.py`

### 3d: Translate Mode Improvement

**Current:** Append instruction to system prompt when `/translate` active.
**Target:** Auto-detect Japanese in incoming text (contains Unicode CJK block `\u4e00-\u9fff`)
and translate without requiring `/translate` to be active. Add "detected Japanese" note
in the response. This means tourists/shopkeepers can text Shogun directly.

**Exit criteria (Phase 3):**
- Location trigger → returns actual nearby places from Google Places gateway
- `/pois` and `/checklist` respond in <2s (no LLM)
- Morning brief includes weather and checklist reminder
- Japanese text auto-detected and translated without `/translate` active

**Complexity:** Low per sub-item (3a is Medium — location handler rewrite)
**Risk:** Low

---

## Dependencies

| Dependency | Status | Notes |
|---|---|---|
| Google Places gateway (`places.platform.ibbytech.com`) | Running on svcnode-01 | Used by find_nearby_places |
| Tavily gateway (`tavily.platform.ibbytech.com`) | Running on svcnode-01 | Used by web_search |
| LLM gateway (`llm.platform.ibbytech.com`) | Running on svcnode-01 | Single 25s timeout — critical |
| knowledge_items (710 items) | Seeded 2026-03-20 | Phase 0 prerequisite |
| shogun_app grants on checklist_items, trip_itinerary | Confirmed 2026-03-17 | Phase 2 prerequisite |
| search_trip_knowledge fix (LOWER() + OR logic) | In shogun-web-api only | Must port to shogun-core in Phase 0 |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Function call + tool execution exceeds 25s timeout | Medium | Medium | Cap tool executor at 10s; fall back to plain LLM if exceeded |
| LLM gateway returns malformed tool_call JSON | Low | Low | Validate response schema before execute; fall back if invalid |
| find_nearby_places returns 0 results for a given location | Low | Low | Message user: "No places found nearby — try a different category" |
| Phase 1 regression on voice/photo paths | Low | Medium | voice/photo handlers do not use text.py routing — isolated |
| Mutation (Phase 2) writes bad data to itinerary | Low | Medium | Require leg_id confirmation from LLM before PATCH |

---

## Pre-Trip Priority Order

Departure is Mar 23. Today is Mar 20. Three days.

| Priority | Phase | Why |
|---|---|---|
| 1 | Phase 0 | Closes the critical knowledge gap; isolated change; low risk; 2 hours |
| 2 | Phase 1 | Unlocks full toolset; medium risk; test thoroughly; 4-6 hours |
| 3 | Phase 3a | Location trigger upgrade — high value for in-trip use; 2 hours |
| 4 | Phase 3b/c | New commands + brief upgrade — high value, low risk; 2 hours |
| 5 | Phase 2 | Mutations — useful but not trip-critical; 3 hours |

If time runs short before departure: Phase 0 + Phase 1 are the must-haves.
Phase 2 can be deployed during the trip from a terminal window in Japan.

---

## Out of Scope

- Photo-to-knowledge-base ingestion pipeline (post-trip)
- Reddit gateway Telegram integration (post-trip)
- MCP tool calling (deferred post-MVP, per approved CLAUDE.md decision)
- Postgres conversation history (deferred post-MVP)
- Inline keyboard buttons (Telegram Bot API feature — adds complexity, not critical for MVP)
- Shogun-web-api changes (this plan covers shogun-core only)
