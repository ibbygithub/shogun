# Tokyo Knowledge Base Seeding — Validation Report
**Date:** 2026-03-17
**Task:** Team 5 — Seed Tokyo knowledge base (knowledge_items table)
**Status:** COMPLETE — all checks PASS

---

## What Was Done

1. **Schema check** — `knowledge_items` table did not exist. Created via seed script on first run.
2. **Unique index created** — `uidx_knowledge_anchor_cat_url` on `(COALESCE(anchor,''), COALESCE(category,''), COALESCE(source_url,''))` for deduplication.
3. **Tavily API format confirmed** — endpoint is `POST /v1/search` (not `/search`), gateway at `http://platform-tavily:8084`.
4. **Seed script written** — `tools/seed_tokyo_knowledge.py` — 20 topics across 4 anchors, 5 results each.
5. **Script executed** inside `shogun-web-api` container — 100 records inserted, 0 errors.

---

## Seed Results by Category

| City   | Category     | Count |
|--------|--------------|-------|
| tokyo  | vintage      | 10    |
| tokyo  | skincare     | 10    |
| tokyo  | shopping     | 10    |
| tokyo  | temple       | 15    |
| tokyo  | restaurant   | 15    |
| tokyo  | street_food  | 5     |
| tokyo  | events       | 5     |
| tokyo  | local_market | 5     |
| tokyo  | pharmacy     | 5     |
| tokyo  | museum       | 5     |
| tokyo  | market       | 5     |
| tokyo  | sakura       | 5     |
| tokyo  | transit      | 5     |
| **TOTAL** |           | **100** |

---

## Anchors Seeded

| Anchor          | Topics Seeded | Categories |
|-----------------|---------------|------------|
| (interest-based / NULL) | 10 | vintage, skincare, street_food, shopping, temple, events |
| tokyo-sugamo    | 4 | restaurant, temple, local_market, pharmacy |
| tokyo-ueno      | 4 | museum, market, restaurant, sakura |
| ghibli-museum   | 2 | restaurant, transit |

---

## Verification Checks

| Check | Result |
|-------|--------|
| Total records >= 20 | PASS (100) |
| vintage >= 3 | PASS (10) |
| skincare >= 3 | PASS (10) |
| street_food >= 3 | PASS (5) |
| temple >= 3 | PASS (15) |
| museum >= 3 | PASS (5) |

---

## Infrastructure Notes

- `knowledge_items` table now exists in `shogun_v1` on `platform-postgres`.
- Collation version mismatch warning on `platform-postgres` (2.41 vs 2.36) is pre-existing — not blocking.
- Tavily gateway (`platform-tavily:8084`) healthy and responsive throughout seeding.
- Script is idempotent — re-running will skip existing `(anchor, category, source_url)` combinations via `ON CONFLICT DO NOTHING`.

---

## Files

- Seed script: `tools/seed_tokyo_knowledge.py`
- This report: `outputs/validation/2026-03-17_tokyo-knowledge-seeded_report.md`
