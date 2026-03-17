# AI Calendar Tools — Implementation Report
**Date:** 2026-03-17
**Branch:** feature/20260316-ai-calendar-tools
**Task:** Team 4 critical path — Gemini function calling for web chat

---

## Summary

Implemented 6 AI tools enabling the Shogun web chat to read and write trip data
via Gemini function calling. The LLM gateway does not expose tool calling
(`available-upstream` per service docs), so chat.py calls the Gemini REST API
directly using `GOOGLE_API_KEY` for tool-enabled requests. If the key is absent,
the code falls back to the existing LLM gateway path (no tools).

---

## Files Changed

| File | Change |
|------|--------|
| `routers/chat.py` | Full rewrite — added CALENDAR_TOOLS definitions, 6 tool executor functions, Gemini direct REST call loop, `tool_actions` in response |
| `routers/itinerary.py` | Added `PATCH /itinerary/{leg_id}` endpoint (LegPatch model, partial update) |
| `.env` | Added `GOOGLE_API_KEY` |
| `.env.example` | Documented `GOOGLE_API_KEY` entry |
| `src/lib/types.ts` | Added `ToolAction` interface; extended `ChatMessage` with `tool_actions?: ToolAction[]` |
| `src/components/chat/ChatMessage.tsx` | Renders green badge strip below AI messages when tool_actions present |
| `database/migrations/20260316_checklist_and_knowledge.sql` | New migration: creates `checklist_items` and `knowledge_items` tables with seed data |

---

## Tools Implemented

| Tool | Description | DB table |
|------|-------------|----------|
| `get_itinerary_legs` | Read itinerary filtered by city and/or date | `trip_itinerary` |
| `update_itinerary_leg` | Partial update of leg title and/or notes_en | `trip_itinerary` |
| `get_checklist_items` | Read checklist filtered by category/packed | `checklist_items` |
| `toggle_checklist_item` | Mark item packed or unpacked | `checklist_items` |
| `search_trip_knowledge` | ILIKE search on topic + content_summary | `knowledge_items` |
| `get_trip_pois` | Read POIs filtered by city/category | `trip_pois` |

---

## Architecture Decisions

**Why Gemini direct REST (not gateway)?**
The platform LLM gateway (`/v1/chat`) does not pass `tools` or `functionDeclarations`
to Gemini — it strips the request down to messages + generationConfig only.
The service doc explicitly marks function calling as `available-upstream` (not exposed).
Rather than modifying the platform gateway (out of scope for this task), chat.py calls
`generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`
directly with function declarations. The existing gateway is kept as a no-tools fallback.

**Tool execution loop:**
- Max 3 rounds of tool calls before forcing a text-only final response
- Each round: Gemini returns functionCall parts → executor runs → functionResponse appended → Gemini synthesizes
- All executors catch exceptions and return error strings (never raise)

**`checklist_items` and `knowledge_items` tables:**
These tables are referenced in the task brief but had no existing migrations.
Migration `20260316_checklist_and_knowledge.sql` creates both tables.
**This migration must be run on dbnode-01 before the API can serve checklist/knowledge tools.**

---

## Pre-deployment Checklist

- [ ] Run migration on dbnode-01:
      `psql -U dba-agent -d shogun_v1 -f database/migrations/20260316_checklist_and_knowledge.sql`
- [ ] Rebuild API container:
      `docker compose up -d --build` in `app-services/shogun-web/shogun-web-api`
- [ ] Rebuild UI container:
      `docker compose up -d --build` in `app-services/shogun-web/shogun-web-ui`

---

## Test Queries

Once deployed, verify with:

```
POST http://localhost:8090/chat
{"message": "What's on March 24th?"}
```
Expected: tool_actions includes `get_itinerary_legs`, response includes Nara details.

```
POST http://localhost:8090/chat
{"message": "Add a note to the Nara leg: backside trail approach, bring yen"}
```
Expected: tool_actions includes `get_itinerary_legs` (to find the leg) then `update_itinerary_leg`.

```
POST http://localhost:8090/chat
{"message": "Mark passport as packed"}
```
Expected: tool_actions includes `get_checklist_items` then `toggle_checklist_item`.

```
POST http://localhost:8090/chat
{"message": "Find vintage shops near Sugamo"}
```
Expected: tool_actions includes `search_trip_knowledge` and/or `get_trip_pois`.

---

## Known Limitations

- `knowledge_items` table will be empty until content is seeded — the AI will report
  no results for knowledge searches until rows are added.
- `checklist_items` has a seed of 15 common items. IDs are not guaranteed until the
  migration runs — use natural language ("mark passport as packed") not raw IDs.
- The tool-calling loop uses the full conversation history for each Gemini call;
  on long conversations this may approach token limits for the 1024-token config.
  Increase `max_output_tokens` in `_call_gemini_with_tools` if needed.
