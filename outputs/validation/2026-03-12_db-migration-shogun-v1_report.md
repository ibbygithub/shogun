# Evidence: shogun_v1 Database Migration
**Date:** 2026-03-12
**Persona:** dba-agent
**Node:** dbnode-01 (192.168.71.221)
**Database:** shogun_v1

---

## Task Summary

Initial schema migration for the Shogun Japan trip concierge MVP.
Option B selected: preserve legacy tables alongside new schema.

---

## Migration Steps Executed

| Step | File | Result |
|:-----|:-----|:-------|
| 000 | rename_legacy_tables | `ALTER TABLE users RENAME TO users_v1_legacy` — SUCCESS |
| 002a | create_app_user | `CREATE ROLE shogun_app` — SUCCESS |
| 001 | initial_schema | All 4 tables + 7 indexes created — SUCCESS |
| 002 | grants | All GRANT statements — SUCCESS |

---

## Tables Created

| Table | Indexes | Status |
|:------|:--------|:-------|
| `users` | PRIMARY KEY on id, UNIQUE on telegram_user_id | ✅ Created |
| `user_preferences` | idx_user_pref_user_id, idx_user_pref_category | ✅ Created |
| `trip_itinerary` | idx_itinerary_date, idx_itinerary_city | ✅ Created |
| `trip_pois` | idx_pois_city, idx_pois_category, idx_pois_tags (GIN) | ✅ Created |

---

## Role Created

| Role | Attributes | Grants |
|:-----|:-----------|:-------|
| `shogun_app` | LOGIN, no superuser, 10 connections | CONNECT on shogun_v1, USAGE on public schema, SELECT/INSERT/UPDATE/DELETE on all 4 new tables, USAGE/SELECT on all 4 sequences |

---

## Legacy Tables Preserved (Option B)

`users_v1_legacy` — former `users` table from prior web-app version.
0 rows. All existing FK constraints from old tables (activities, documents,
expenses, survey_votes, surveys, trip_members) continue to resolve correctly.

Old tables NOT renamed (no naming conflicts):
activities, dev_logs, document_embeddings, documents, expenses,
ingestion_runs, locations, lodging_details, raw_ingestion, sources,
survey_options, survey_votes, surveys, trip_events, trip_members, trips

---

## Final Table Count

21 tables in shogun_v1.public:
- 4 new Shogun MVP tables
- 1 renamed legacy table (users_v1_legacy)
- 16 old tables preserved as-is

---

## Rollback

If migration must be reversed:
```sql
-- Drop new tables
DROP TABLE IF EXISTS trip_pois CASCADE;
DROP TABLE IF EXISTS trip_itinerary CASCADE;
DROP TABLE IF EXISTS user_preferences CASCADE;
DROP TABLE IF EXISTS users CASCADE;
-- Restore legacy users table
ALTER TABLE users_v1_legacy RENAME TO users;
-- Drop shogun_app role
DROP ROLE IF EXISTS shogun_app;
```

---

## Outcome

✅ MIGRATION COMPLETE — shogun_v1 ready for shogun-core Phase 3 build.
