# Telegram Upgrade — Phase 1 Validation Report
Date: 2026-03-21
Status: DEPLOYED — manual Telegram test pending

## Summary

Phase 1 of the Telegram upgrade plan deployed. shogun-core now routes all
text messages through Gemini function calling. The LLM decides which tool to
invoke based on user intent — no hardcoded keyword matching. 5 read-only tools
available. Falls back to rag.respond() on Gemini errors or missing API key.

---

## Changes Deployed (commit 8437488)

| File | Change |
|------|--------|
| `app-services/shogun-core/app/services/tools.py` | NEW — 5 tool definitions + executors + `chat_with_tools()` orchestrator |
| `app-services/shogun-core/app/handlers/text.py` | Replaced `rag_respond()` call with `chat_with_tools()` |
| `app-services/shogun-core/app/config.py` | Added `google_api_key`, `google_base_url`, `places_gateway_url` fields |
| `app-services/shogun-core/.env.example` | Documented the 3 new env vars |

---

## Tools Available

| Tool | Executor | Data source |
|------|----------|-------------|
| `search_trip_knowledge` | `_exec_search_trip_knowledge` | knowledge_items DB (710 items) |
| `find_nearby_places` | `_exec_find_nearby_places` | Google Places gateway (svcnode-01:8081) |
| `web_search` | `_exec_web_search` | Tavily gateway (svcnode-01:8084) |
| `get_trip_pois` | `_exec_get_trip_pois` | trip_pois DB |
| `get_itinerary` | `_exec_get_itinerary` | trip_itinerary DB |

---

## Design Decisions

**Single tool call per turn:** Telegram's response window is ~30s. With 2 Gemini
REST calls (20s each budget) + tool execution (10s cap for remote tools), the worst
case is ~50s if all timeouts fire. In practice: Gemini call 1 ~5s, tool 3-8s,
Gemini call 2 ~5s = ~15-18s. Single round is safe.

**Remote tool timeout (10s):** Places and Tavily are capped at 10s via
`asyncio.wait_for()`. On timeout, the tool result string tells Gemini to answer
from its own Japan expertise — the response degrades gracefully rather than failing.

**City injection:** If Gemini omits `city` and `anchor` for `search_trip_knowledge`
or `find_nearby_places`, the handler injects `city_context` (derived from today's
itinerary date). This prevents off-city results during single-city days.

**Fallback chain:** Gemini API key missing → rag.respond(). Gemini call 1 fails
→ rag.respond(). Unknown tool → rag.respond(). Gemini call 2 fails → return raw
tool result. All paths produce a usable response.

---

## Deployment

- Node: brainnode-01 (192.168.71.222)
- GOOGLE_API_KEY, PLACES_GATEWAY_URL, GOOGLE_BASE_URL added to live .env
  (values copied from shogun-web-api .env — same Google Cloud project)
- Container rebuilt and restarted — startup clean

---

## Test Cases (manual Telegram verification needed)

| Query | Expected tool | Pass? |
|-------|--------------|-------|
| "recommend ramen near our place in Osaka" | search_trip_knowledge (city=osaka) | — |
| "what's within 5 min walk of the hotel?" | find_nearby_places (current anchor) | — |
| "any craft beer bars in Osaka?" | search_trip_knowledge (category=craft_beer) | — |
| "sakura forecast for Osaka this weekend" | web_search | — |
| "what's on our itinerary tomorrow?" | get_itinerary | — |
| "key spots to visit in Kanazawa" | get_trip_pois (city=kanazawa) | — |
| casual chat "is it going to rain?" | no tool (direct LLM) | — |
