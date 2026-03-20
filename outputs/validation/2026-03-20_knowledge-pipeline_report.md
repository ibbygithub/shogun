# Knowledge Pipeline — Validation Report
Date: 2026-03-20
Status: PASS

## Summary

Full knowledge pipeline ingestion and query engine rebuild completed.
710 knowledge_items across 5 cities. RAG validation: 5/5 test queries return
relevant results from the knowledge base.

---

## Phase 0: Query Engine Fixes

**File:** `app-services/shogun-web/shogun-web-api/routers/chat.py`
**Function:** `_exec_search_trip_knowledge`
**Commits:** `4cbc67c`, `5af71c0`

| Fix | Before | After |
|-----|--------|-------|
| City match | `city = %s` (case-sensitive) — all Brenda items invisible | `LOWER(city) = LOWER(%s)` — all items visible |
| Anchor support | Not in tool definition or query | `anchor` parameter added — accommodation-zone filtering |
| Match logic | AND (all tokens must match) | OR + stopword filter + match-count ranking |
| Result limit | 5 | 15 |
| Ordering | Alphabetical | Full phrase in topic → token match count → alpha |

**Root cause resolved:** 14 Brenda items stored with capitalised city names
(`'Osaka'`, `'Kyoto'`, etc.) were completely invisible to AI queries because the
old `city = 'osaka'` comparison is case-sensitive in PostgreSQL. LOWER() fix
makes all 710 items visible.

---

## Phase 1: Bulk Ingestion Results

**Script:** `tools/ingest_knowledge_pipeline.py --city {osaka|kanazawa|kyoto|nara}`

| City | Queries | Inserted | Skipped (dups) | Total in DB |
|------|---------|----------|----------------|-------------|
| Osaka | 40 | 193 | 4 | 347 |
| Kanazawa | 16 | 75 | 2 | 96 |
| Kyoto | 17 | 80 | 0 | 88 |
| Nara | 13 | 63 | 2 | 64 |
| **Phase 1 total** | **86** | **411** | **8** | |
| Tokyo | — | — | — | 111 (unchanged) |
| Sakai | — | — | — | 4 (manual) |
| **Grand total** | | | | **710** |

### Category distribution (new categories added)

| Category | Count | Primary city |
|----------|-------|-------------|
| dining | 138 | Osaka |
| shopping | 89 | Osaka, Nara |
| coffee_cafe | 35 | All cities |
| ceramics | 29 | Kanazawa, Kyoto |
| shopping_crafts | 24 | Kanazawa |
| tech_electronics | 15 | Osaka (Nipponbashi) |
| anime_manga | 15 | Osaka (Nipponbashi) |
| sake_brewery | 15 | Kanazawa, Nara, Osaka |
| craft_beer | 14 | Osaka, Kanazawa |
| jewelry_artisan | 14 | Osaka, Kyoto |
| eyewear_prescription | 5 | Osaka |
| convenience_store | 5 | Osaka |

---

## Phase 2: RAG Validation

All 5 test queries return 3 relevant results from the knowledge base.

| Query | City filter | Tokens used | Result |
|-------|------------|-------------|--------|
| "craft beer near osaka airbnb" | osaka | craft, beer, osaka, airbnb | ✅ 3 craft_beer results |
| "ESP32 microcontroller electronics Osaka" | osaka + tech_electronics | esp32, microcontroller, electronics, osaka | ✅ 3 tech_electronics results |
| "lunch Nanzenji Kyoto" | kyoto + dining | lunch, nanzenji, kyoto | ✅ Nanzenji Junsei top result |
| "geisha district Kanazawa what to see" | kanazawa | geisha, district, kanazawa | ✅ Higashi Chaya top result |
| "handmade jewelry Osaka bazaar" | osaka | handmade, jewelry, osaka, bazaar | ✅ 3 jewelry_artisan results |

---

## Known Limitations

- **Tavily content is snippet-level** (≤400 chars). The AI gets context, not full
  reviews. For specific restaurant decisions, web_search fallback provides richer
  detail.
- **Tokyo deferred.** 111 existing items are from the March 17 seed. Phase 3
  (Shimokitazawa vintage, Akihabara tech, Harajuku) blocked on Brenda's Tokyo plan.
- **Kanazawa ramen query** (query 14) returned only 2 results — Tavily returned
  Yokohama ramen results instead of Kanazawa. Low signal for this specific query.

---

## Open Items

- Tokyo Phase 3 ingestion: blocked on Brenda's Tokyo plan
- Kanazawa 8th-street ramen: consider manual addition once specific shops are researched
- Shogun-core (Telegram bot) also needs the same search_trip_knowledge fix —
  separate service, separate chat.py equivalent — verify or update if it has its own query
