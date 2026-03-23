# Plan: Knowledge Pipeline — Full Pre-Trip Ingestion
Date: 2026-03-20
Status: Approved

## Objective

Populate `knowledge_items` with 200–300 curated, AI-searchable records covering
every city and destination zone on the trip itinerary. The AI concierge uses this
table as its primary knowledge source before falling back to live web search. A
rich, well-structured knowledge base means faster, more accurate, and more
personalized recommendations — grounded in actual trip context rather than generic
Japan travel advice.

## Scope

**In scope:**
- Phase 0: Fix `search_trip_knowledge` query engine — prerequisite for everything else
- Phase 1: Bulk Tavily-sourced ingestion for Osaka, Kanazawa, Kyoto, Nara
- Phase 2: RAG validation — confirm AI uses knowledge base effectively
- Phase 3: Tokyo expansion (deferred — still being built out by Brenda)

**Out of scope:**
- Google Places data — not a knowledge_items source (Places runs live at query time)
- Web UI Research tab implementation — separate feature, backlog
- Telegram /research command — separate feature, backlog
- Tokyo full ingestion — deferred until Brenda's Tokyo plan is finalized

---

## Traveler Interest Profile (Source of Query Matrix)

### Brenda
- Eyewear: Same-day vision check + prescription grinding in one visit (optical shop, not eye doctor)
- Knives: Collector-level buyer, knows specific artisan names; Sakai already covered
- Skincare: Japanese brands, in-store browsing
- Jewelry: Handmade, artisan, metal and mixed materials; interested in bazaars
- Food: Primarily vegetarian (animal stock fine), loves seafood, noodles, conveyor sushi, convenience store food

### Madeline
- Anime, manga, stickers, plushes
- Vintage and used clothing, antiques
- Food: Chicken, noodles, no seafood, convenience store exploration

### Todd
- Vintage and used clothing, antiques
- Tech gear: ESP32 microcontrollers, robot build kits (Nipponbashi is the Osaka equivalent of Akihabara)
- Local craft beer
- Authentic Japanese burger
- Beef dishes, noodles

### Shared
- Standing ramen bars, conveyor sushi, food halls (depachika)
- Convenience store food culture (shrimp burger, etc.)
- Independent coffee shops and cafes
- Street food
- No fast food chains unless stranded

---

## Approved Taxonomy

| Category | Covers | Notes |
|----------|--------|-------|
| `dining` | Ramen, izakaya, conveyor sushi, food hall, street food, kushikatsu | District embedded in topic string |
| `coffee_cafe` | Independent coffee shops, matcha cafes, kissaten | Separate from dining — distinct search intent |
| `craft_beer` | Beer bars, taprooms, local breweries | Todd-specific, high search frequency |
| `shopping` | Vintage clothing, antiques, stationery, general retail | |
| `anime_manga` | Figures, plushes, stickers, manga, retro games | Madeline primary |
| `tech_electronics` | ESP32, microcontrollers, robot kits, hobby electronics | Todd-specific; Nipponbashi/Akihabara territory |
| `skincare` | Japanese skincare brands and stores | Brenda |
| `jewelry_artisan` | Handmade jewelry, metal/mixed materials, craft bazaars | Brenda |
| `eyewear_prescription` | Same-day vision check + grinding | Distinct need; already 3 Osaka items seeded |
| `knife_shop` | Artisan-quality knives outside Sakai | Brenda; any city where quality knives appear |
| `ceramics` | Japanese pottery — functional and decorative | Kutani (Kanazawa), Kiyomizu-yaki (Kyoto), general |
| `shopping_crafts` | Gold leaf, lacquerware, traditional crafts | Already in schema |
| `sake_brewery` | Sake breweries and tasting rooms | |
| `museum` | Already in schema | |
| `temple` | Already in schema | |
| `shrine` | Already in schema | |
| `park` | Already in schema | |
| `sightseeing` | Already in schema | |
| `market` | Already in schema | |
| `neighborhood` | Already in schema | |
| `convenience_store` | One entry per accommodation zone — nearest combini, what to look for | Practical |

---

## Spatial Model

Two tiers. This is the core architectural decision for how knowledge is organized.

### Tier 1 — Accommodation zones (anchor-tagged)
Covers the immediate neighborhood around where the family sleeps. Answers "what's
near our place?" queries. Uses the `anchor` field.

| Anchor | Neighborhood | What to cover |
|--------|-------------|---------------|
| `osaka-airbnb` | Nakazakicho / Tenjinbashisuji / Umeda | Ramen, izakaya, cafe, vintage clothing, craft beer, convenience store, eyewear (supplement existing 3), ceramics |
| `kanazawa-hotel` | Higashi Chaya walkable zone | Sake tasting, gold leaf, ceramics, seafood lunch, geisha district orientation |
| `nara-park` | Near Kintetsu Nara Station / Nara Park entrance | Lunch after temples, cafe, Higashimuki shopping |
| `tokyo-sugamo` | Sugamo / Toshima-ku | (Phase 3 — Tokyo deferred) |

### Tier 2 — Destination zones (city-tagged, anchor=NULL)
Covers every place the itinerary takes them — regardless of distance from accommodation.
Uses `city` field + district name embedded in `topic` string. AI finds these via
text search.

---

## Query Matrix

### OSAKA

**Zone 1 — Accommodation (anchor: osaka-airbnb)**

| Category | Tavily Query | Domain hints |
|----------|-------------|--------------|
| `dining` | "ramen standing bar Nakazakicho Osaka" | tabelog.com |
| `dining` | "izakaya Tenjinbashisuji local dinner Osaka" | tabelog.com |
| `dining` | "best ramen Umeda Osaka standing noodles" | tabelog.com, timeout.com |
| `coffee_cafe` | "independent coffee shop Nakazakicho Osaka third wave" | — |
| `craft_beer` | "craft beer bar Umeda Osaka local tap" | — |
| `shopping` | "vintage clothing shop Nakazakicho Osaka thrift" | — |
| `ceramics` | "Japanese pottery ceramics shop Osaka Umeda" | — |
| `jewelry_artisan` | "handmade jewelry artisan market Osaka" | — |
| `convenience_store` | "FamilyMart Lawson Nakazakicho Airbnb area Osaka convenience store" | — |

**Zone 2 — Dotonbori / Namba / Shinsaibashi (destination, 3/27 evening)**

| Category | Tavily Query | Domain hints |
|----------|-------------|--------------|
| `dining` | "street food Dotonbori Osaka must eat" | — |
| `dining` | "kushikatsu best restaurant Shinsekai Osaka" | tabelog.com |
| `dining` | "takoyaki best Dotonbori Osaka" | — |
| `dining` | "ramen Namba Osaka local favorite" | tabelog.com |
| `dining` | "conveyor sushi Shinsaibashi Namba Osaka" | — |
| `dining` | "food hall depachika Shinsaibashi Osaka" | — |
| `coffee_cafe` | "cafe Namba Dotonbori Osaka specialty" | — |
| `shopping` | "Shinsaibashi shopping street what to buy Osaka" | — |
| `ceramics` | "ceramics pottery shop Shinsaibashi Osaka" | — |

**Zone 3 — Nipponbashi / Denden Town (destination, 3/28 tech + anime)**

| Category | Tavily Query | Domain hints |
|----------|-------------|--------------|
| `tech_electronics` | "ESP32 microcontroller electronics shop Nipponbashi Osaka" | — |
| `tech_electronics` | "robot kit hobby electronics components Denden Town Osaka" | — |
| `tech_electronics` | "Akihabara Osaka Nipponbashi electronics store guide" | — |
| `anime_manga` | "anime figure shop Nipponbashi Osaka best stores" | — |
| `anime_manga` | "retro game shop Nipponbashi Osaka vintage" | — |
| `anime_manga` | "manga stickers plush Denden Town Osaka" | — |
| `shopping` | "vintage antique shop Nipponbashi Osaka" | — |
| `dining` | "ramen lunch Nipponbashi Osaka cheap eat" | tabelog.com |

**Zone 4 — Shinsekai / Tsutenkaku (destination, 3/28)**

| Category | Tavily Query | Domain hints |
|----------|-------------|--------------|
| `dining` | "kushikatsu Shinsekai Osaka authentic rules" | — |
| `dining` | "street food Shinsekai Osaka local guide" | — |
| `sightseeing` | "Shinsekai Osaka atmosphere guide what to see" | — |
| `knife_shop` | "Tower Knives Osaka Shinsekai artisan knives" | — |

**Zone 5 — Sakuranomiya / Osaka Castle (destination, 3/27 afternoon)**

| Category | Tavily Query | Domain hints |
|----------|-------------|--------------|
| `dining` | "lunch near Osaka Castle restaurants walk" | tabelog.com |
| `park` | "Sakuranomiya park cherry blossom food stalls street food" | — |
| `sightseeing` | "Osaka Castle Nishinomaru Garden sakura tips" | — |

**Zone 6 — Interest threads (non-anchored, general Osaka)**

| Category | Tavily Query | Notes |
|----------|-------------|-------|
| `craft_beer` | "best craft beer bars Osaka local brewery guide 2025" | — |
| `shopping` | "best vintage clothing Osaka thrift second-hand" | — |
| `sake_brewery` | "sake tasting Osaka brewery visit" | — |
| `dining` | "authentic Japanese burger Osaka best" | Todd |
| `ceramics` | "Osaka ceramics pottery Japanese souvenir shop" | — |
| `jewelry_artisan` | "handmade jewelry maker stall Osaka bazaar" | — |
| `skincare` | "Japanese skincare store Osaka Cosme best brands" | Brenda |

---

### KANAZAWA (highlights only — 30–40 items target)

**Zone 1 — Higashi Chaya geisha district (priority)**

| Category | Tavily Query |
|----------|-------------|
| `sightseeing` | "Higashi Chaya geisha district Kanazawa guide what to do" |
| `shopping_crafts` | "gold leaf shop Higashi Chaya Kanazawa buy" |
| `sake_brewery` | "sake tasting Kanazawa Higashi Chaya brewery" |
| `coffee_cafe` | "cafe tea house Higashi Chaya Kanazawa" |
| `ceramics` | "Kutani ware ceramics shop Kanazawa Higashi Chaya" |
| `dining` | "lunch restaurant Higashi Chaya Kanazawa local" |

**Zone 2 — Omicho Market**

| Category | Tavily Query |
|----------|-------------|
| `market` | "Omicho Market Kanazawa seafood what to eat guide" |
| `dining` | "sushi breakfast Omicho Market Kanazawa morning" |
| `dining` | "Kanazawa local food what to eat specialty dishes" |

**Zone 3 — Kenroku-en / Kanazawa Castle / Old Town**

| Category | Tavily Query |
|----------|-------------|
| `sightseeing` | "Kenroku-en garden Kanazawa tips best time" |
| `shopping_crafts` | "lacquerware shop Kanazawa old town buy" |
| `ceramics` | "Kutani pottery workshop Kanazawa buy authentic" |
| `shopping_crafts` | "gold leaf workshop experience Kanazawa hands-on" |
| `dining` | "Kanazawa ramen 8th street style local guide" |
| `craft_beer` | "craft beer Kanazawa bar local" |

---

### KYOTO (day trip 3/29 — Philosophers Path route)

**Zone 1 — Ginkakuji / Start of Philosophers Path**

| Category | Tavily Query |
|----------|-------------|
| `coffee_cafe` | "coffee cafe near Ginkakuji Kyoto morning open early" |
| `sightseeing` | "Ginkakuji Silver Pavilion Kyoto tips morning visit" |
| `temple` | "Honen-in temple quiet Philosophers Path detour Kyoto" |

**Zone 2 — Nanzenji / Eikando**

| Category | Tavily Query |
|----------|-------------|
| `dining` | "tofu kaiseki restaurant Nanzenji Kyoto lunch traditional" |
| `dining` | "lunch Nanzenji area Kyoto affordable local" |
| `temple` | "Nanzenji temple Eikando Kyoto visit guide tips" |
| `sightseeing` | "Meiji aqueduct Nanzenji Kyoto photo spot" |

**Zone 3 — Gion / Maruyama / Yasaka**

| Category | Tavily Query |
|----------|-------------|
| `dining` | "lunch restaurant Gion Kyoto traditional hidden" |
| `dining` | "street food Higashiyama Gion Kyoto snacks" |
| `coffee_cafe` | "third wave coffee Gion Kyoto specialty" |
| `shopping` | "antique shop Gion Kyoto old" |
| `jewelry_artisan` | "artisan craft jewelry Gion Kyoto handmade" |

**Zone 4 — Higashiyama Streets / Kiyomizudera**

| Category | Tavily Query |
|----------|-------------|
| `ceramics` | "Kiyomizu-yaki pottery shop Higashiyama Sannenzaka Kyoto buy" |
| `dining` | "matcha sweets cafe Sannenzaka Ninenzaka Kyoto" |
| `shopping` | "souvenir shop Higashiyama Kyoto what to buy traditional" |
| `shopping_crafts` | "lacquerware textiles Higashiyama Kyoto craft" |
| `sightseeing` | "Kiyomizudera wooden stage Kyoto sunset tips" |

---

### NARA (day trip 3/25)

**Zone 1 — Nara Park / Todai-ji area**

| Category | Tavily Query |
|----------|-------------|
| `dining` | "lunch near Nara Park after deer temples restaurant" |
| `dining` | "Nara local food specialty what to eat" |
| `sightseeing` | "Nara deer park tips etiquette guide" |
| `coffee_cafe` | "cafe near Nara Park Todai-ji rest stop" |

**Zone 2 — Naramachi historic district**
(Currently zero items in DB — this neighborhood deserves its own cluster)

| Category | Tavily Query |
|----------|-------------|
| `neighborhood` | "Naramachi Nara historic district guide what to see" |
| `shopping` | "craft shop Naramachi Nara traditional artisan" |
| `ceramics` | "pottery craft shop Naramachi Nara" |
| `dining` | "restaurant cafe Naramachi Nara hidden local" |
| `shopping` | "antique shop Naramachi Nara vintage" |

**Zone 3 — Higashimuki / Kintetsu Station area**

| Category | Tavily Query |
|----------|-------------|
| `shopping` | "Higashimuki shopping arcade Nara what to buy" |
| `dining` | "ramen noodles near Kintetsu Nara station" |
| `dining` | "street food near Nara station cheap eat" |

---

## Volume and Cost Estimates

| City | Queries | Est. items (3–5 results each) | Tavily cost |
|------|---------|-------------------------------|-------------|
| Osaka | 38 | 115–190 | ~$1.60 |
| Kanazawa | 15 | 45–75 | ~$0.63 |
| Kyoto | 17 | 51–85 | ~$0.71 |
| Nara | 13 | 39–65 | ~$0.55 |
| **Total** | **83** | **250–415** | **~$3.49** |

Target stored after dedup and threshold: **200–280 items**
Previously ingested (Brenda manual): ~80 items already in DB
Combined total target: **280–360 items** across Osaka, Kanazawa, Kyoto, Nara

---

## Ingestion Script Design

One script: `tools/ingest_knowledge_pipeline.py`

Invoked per city to allow incremental runs and error recovery:
```
python tools/ingest_knowledge_pipeline.py --city osaka
python tools/ingest_knowledge_pipeline.py --city kanazawa
python tools/ingest_knowledge_pipeline.py --city kyoto
python tools/ingest_knowledge_pipeline.py --city nara
```

### Script behavior per query:
1. For each (city, zone, anchor, category, query) entry in the matrix
2. Deduplicate check: if a knowledge_items row exists with matching (city, category, topic ~= query) within 7 days → skip
3. Call Tavily gateway (`tavily.platform.ibbytech.com/search`) with query + optional domain filter
4. For each result:
   - If tavily_score >= 0.5 → insert
   - If total results < 3 → insert all regardless of score (sparse is better than empty)
5. Insert into `knowledge_items`: city (lowercase), anchor (if tier 1), category, topic (result title + district), content_summary (Tavily snippet), source_url, tavily_score
6. Log: query run, results received, items inserted/skipped

### Topic field construction (critical for retrieval quality)
Topic must embed: place name + district/neighborhood + category in plain English.
Format: `"{Place Name} — {category keyword} — {District}, {City}"`

Examples:
- `"Osaka Brewing Co. — craft beer bar — Namba, Osaka"`
- `"Nishiki Kiln — Kiyomizu-yaki ceramics — Higashiyama, Kyoto"`
- `"Marutamachi Roastery — coffee cafe — Gion, Kyoto"`

This ensures text search on "craft beer Namba" or "ceramics Kyoto" hits correctly.

### Deduplication key
Before inserting, check: `city + category + source_url` (existing constraint). If source_url is NULL (Tavily items with no URL), check `city + category + topic` to prevent identical entries.

---

## Phases

### Phase 0 — Fix search_trip_knowledge query engine
**Goal:** The AI can actually find the items we load.
**Entry criteria:** This plan approved.
**Deliverables:** Updated `_exec_search_trip_knowledge` in `chat.py`
**Changes required:**
  1. Case-insensitive city match: `LOWER(city) = LOWER(%s)`
  2. Add `anchor` parameter to tool definition and query
  3. Increase LIMIT from 5 to 15
  4. Relevance ordering: topic matches before content_summary matches
  5. Multi-word query handling: split on spaces, AND logic per token, or use PostgreSQL `to_tsvector`
**Exit criteria:** Query `city='osaka'` returns existing Brenda items (currently invisible due to case bug). Query `anchor='osaka-airbnb'` returns accommodation-zone items.
**Complexity:** Low
**Dependency:** None

---

### Phase 1a — Osaka ingestion
**Goal:** 115–190 Osaka knowledge items covering all 6 destination zones.
**Entry criteria:** Phase 0 complete and validated.
**Deliverables:** `tools/ingest_knowledge_pipeline.py` with Osaka matrix; Osaka items in DB
**Exit criteria:** `python tools/ingest_knowledge_pipeline.py --city osaka` completes without errors; COUNT of Osaka knowledge_items >= 130 (existing ~41 + new ~90+)
**Complexity:** Medium
**Dependency:** Phase 0

---

### Phase 1b — Kanazawa, Kyoto, Nara ingestion
**Goal:** 135–225 items covering all day-trip and secondary city zones.
**Entry criteria:** Phase 1a complete (script proven, Tavily gateway confirmed working).
**Deliverables:** Same script, kanazawa/kyoto/nara city flags run
**Exit criteria:**
  - Kanazawa knowledge_items (lowercase) >= 50 total (existing 21 + new ~30)
  - Kyoto knowledge_items >= 40 total (existing 8 + new ~35)
  - Nara knowledge_items >= 25 total (existing 1 + new ~25)
**Complexity:** Low (same script, new city flags)
**Dependency:** Phase 1a

---

### Phase 2 — RAG validation
**Goal:** Confirm the AI uses the knowledge base for real queries — not hallucination, not live web search as first resort.
**Entry criteria:** Phase 1b complete.
**Deliverables:** Validation report in `outputs/validation/`
**Test queries (representative sample):**
  - "What craft beer bars are near our Osaka Airbnb?" → should cite knowledge base item
  - "Where can I find ESP32 microcontrollers in Osaka?" → should cite Nipponbashi tech item
  - "Recommend a lunch spot for our Kyoto day trip near Nanzenji" → should cite Kyoto item
  - "What's special about Kanazawa's geisha district?" → should cite Higashi Chaya item
  - "Brenda wants handmade jewelry in Osaka" → should cite jewelry_artisan item
**Exit criteria:** >= 4 of 5 test queries return a knowledge_items citation in `tool_actions` badge showing `search_trip_knowledge` was called; responses reference specific places by name.
**Complexity:** Low
**Dependency:** Phase 1b

---

### Phase 3 — Tokyo expansion (deferred)
**Goal:** ~70 additional Tokyo items beyond the existing 100 — covering Shimokitazawa (vintage), Akihabara (tech/anime), Harajuku/Omotesando, Ueno/Ameyoko.
**Entry criteria:** Brenda's Tokyo plan finalized.
**Complexity:** Low (same script, tokyo flag)
**Dependency:** Tokyo trip plan received

---

## Dependencies

| Dependency | Status | Owner |
|------------|--------|-------|
| Tavily gateway reachable from scripts | Confirmed live | Platform |
| DATABASE_URL accessible from laptop tools | Confirmed (via container exec) | Infra |
| Phase 0 query engine fix | Not started | Coding agent |
| Brenda's Tokyo itinerary | Not started | Brenda |

---

## Risks

**Risk:** Tavily returns low-quality or outdated results for specific niche queries (ESP32 shops, artisan knife makers outside Sakai).
**Mitigation:** Log raw Tavily scores. For niche queries, use Tabelog or specific Japan hobbyist site domains. Manual supplement for high-priority items (Todd's tech gear).

**Risk:** knowledge_items count grows beyond useful AI retrieval range — too many items, AI gets diluted results.
**Mitigation:** LIMIT 15 in query + relevance ordering (Phase 0) prevents this. Quality of topic string matters more than volume.

**Risk:** City name casing inconsistency across old and new data causes silent retrieval gaps.
**Mitigation:** Phase 0 fix (LOWER() normalization) resolves this. Ingestion script standardizes on lowercase city names.

**Risk:** Departure Mar 23 — only 2–3 days for all phases.
**Mitigation:** Phase 0 is a 1-hour fix. Phase 1a/1b are script runs, not development. Phase 2 is a 30-minute chat test. Timeline is achievable if execution starts Mar 21.

---

## Out of Scope

- Web UI Research tab (backlog)
- Telegram /research command (backlog)
- Tokyo trip plan (deferred — Brenda still building)
- Google Places as a knowledge_items source — confirmed architectural decision: Places runs live, not pre-loaded
- Firecrawl full-page scrape — Tavily snippets sufficient for MVP knowledge base

---

## Execution Handoff Notes

**For the coding agent executing Phase 0:**
All changes are in one function: `_exec_search_trip_knowledge` in
`app-services/shogun-web/shogun-web-api/routers/chat.py` (line 604).
Also update the tool definition at line 212 to add `anchor` as an optional parameter.
Redeploy required: `docker compose up -d --build shogun-web-api` on brainnode-01.

**For the coding agent executing Phase 1:**
Script location: `tools/ingest_knowledge_pipeline.py` (new file).
Execution: runs on the laptop (control plane), connects to shogun_v1 via
`docker exec shogun-web-api python3` pattern established in this session.
Tavily gateway: `http://tavily.platform.ibbytech.com/search` — POST with
`{"query": "...", "include_domains": [...], "max_results": 5}` and header
`Authorization: Bearer {TAVILY_API_KEY}`.
