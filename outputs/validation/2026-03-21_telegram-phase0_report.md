# Telegram Upgrade — Phase 0 Validation Report
Date: 2026-03-21
Status: PASS

## Summary

Phase 0 of the Telegram upgrade plan deployed successfully. The `search_trip_knowledge`
query engine (LOWER() city match, OR token logic, stopword filter, LIMIT 15, relevance
ranking) is now live in shogun-core. All 710 knowledge_items are now accessible from
Telegram. Tavily fires only when the DB returns nothing.

---

## Changes Deployed (commit f15515e)

| File | Change |
|------|--------|
| `app-services/shogun-core/app/db.py` | Added `search_trip_knowledge()` — ported from shogun-web-api with LOWER() city, OR token logic, stopword filter, relevance ranking, LIMIT 15 |
| `app-services/shogun-core/app/services/rag.py` | DB-first food/place branch: calls knowledge_items before Tavily. Tavily only fires on empty DB result. |
| `app-services/shogun-core/app/handlers/text.py` | Fixed missing `city_context=city` in `rag_respond()` call — was always passing None |

---

## Bug Fixed (pre-existing, not previously flagged)

`text.py` was computing `city` from `db.get_city_for_date()` for weather, but NOT
forwarding it to `rag_respond()`. Every knowledge DB query was running with `city=None`,
which would have returned results across all cities (or none with a city filter). The
LOWER() case-insensitive city filter is now applied correctly.

---

## Deployment

- Node: brainnode-01 (192.168.71.222)
- Container: shogun-core rebuilt and restarted
- Startup: Clean — DB connection confirmed, scheduler started
- Log: `DB connection OK (shogun_v1 @ 192.168.71.221)`

---

## Query Flow (post-Phase 0)

```
User message → keyword detection
  → food/place keyword? YES
      → search_trip_knowledge(query, city=today_city)
          → DB returns results? → inject as context → LLM
          → DB empty?           → Tavily (Tabelog) → LLM
  → event/sakura keyword?    → Tavily (open) → LLM
  → neither?                 → plain LLM
```

---

## Open Items

- Phase 0 adds DB-first to the existing keyword-detection RAG path only.
  Queries that don't hit `_FOOD_KEYWORDS` still bypass knowledge entirely
  (e.g., "sake brewery" or "craft beer" — these aren't in the keyword set).
  Phase 1 (Gemini function calling) resolves this — the LLM decides when
  to call `search_trip_knowledge`, not a hardcoded keyword list.
- Manual Telegram test pending (user to verify with a food query in Osaka context).
