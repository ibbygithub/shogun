---
name: shogun-dba
description: >
  Schema knowledge for shogun_v1, migration patterns, grant management, and the
  place/activity category taxonomy. Use this skill when creating or modifying
  database tables, writing migrations, managing grants for shogun_app, or working
  with the knowledge pipeline data model.
user-invocable: true
---

# Shogun DBA Skill

## Overview

shogun_v1 is a PostgreSQL 17 database on **dbnode-01** (192.168.71.221).
Schema: `public`. Owner: `postgres`. Application user: `shogun_app`.

All DBA work requires the **dba-agent** persona via SSH to dbnode-01.
shogun-core connects from brainnode-01 (192.168.71.222) using psycopg2 over TCP.

---

## Connection Patterns

### From shogun-core (application)

shogun-core uses `psycopg2` with `RealDictCursor`. Connection config is in
`app-services/shogun-core/app/config.py` via pydantic-settings, reading from `.env`:

```
DB_HOST=192.168.71.221    (dbnode-01 IP — direct TCP from brainnode-01)
DB_PORT=5432
DB_NAME=shogun_v1
DB_USER=shogun_app
DB_PASSWORD=<from .env>
```

Connection is per-request (no pool). Each helper in `app/db.py` calls
`get_connection()`, executes a query, and closes in a `try/finally` block.
`connect_timeout=5` is set.

### From dba-agent (administration)

```bash
ssh -i ~/.ssh/dba-agent_ed25519 dba-agent@192.168.71.221
sudo -u postgres psql -d shogun_v1
```

---

## Full Schema Reference

### Table: `users`

Telegram users registered with Shogun. One row per user.

```sql
CREATE TABLE users (
    id                  SERIAL          PRIMARY KEY,
    telegram_user_id    BIGINT          NOT NULL UNIQUE,
    display_name        TEXT            NOT NULL,
    full_name           TEXT,
    notification_active BOOLEAN         NOT NULL DEFAULT true,
    language_preference TEXT            NOT NULL DEFAULT 'en',
    created_utc         TIMESTAMPTZ     NOT NULL DEFAULT now()
);
```

**Key columns:**
- `telegram_user_id` — Stable Telegram numeric ID (from bot update payload). UNIQUE constraint.
- `notification_active` — If false, user receives no unsolicited location-triggered messages.
  Toggled via `/quiet` and `/active` commands.
- `display_name` — Short name Shogun uses in responses.

**No indexes beyond PK and UNIQUE on telegram_user_id.**


### Table: `user_preferences`

Trip-long preference store per user. Not in Valkey (survives TTL expiry).

```sql
CREATE TABLE user_preferences (
    id               SERIAL      PRIMARY KEY,
    user_id          INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category         TEXT        NOT NULL
                     CHECK (category IN ('dietary', 'likes', 'dislikes', 'shopping', 'entertainment')),
    preference_key   TEXT        NOT NULL,
    preference_value TEXT        NOT NULL,
    notes            TEXT,
    created_utc      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**CHECK constraint on category:** `dietary`, `likes`, `dislikes`, `shopping`, `entertainment`

**Indexes:**
- `idx_user_pref_user_id` — btree on `(user_id)`
- `idx_user_pref_category` — btree on `(user_id, category)`

**Design rationale:** Key-value pattern allows flexible preference storage without
schema changes. `preference_key` examples: `eats`, `avoids`, `interest_type`.
`preference_value` examples: `fish`, `red_meat_as_protein`, `vintage_cameras`.


### Table: `trip_itinerary`

Full trip schedule: flights, accommodation, activities, transit.

```sql
CREATE TABLE trip_itinerary (
    id                  SERIAL      PRIMARY KEY,
    leg_sequence        INTEGER     NOT NULL,
    leg_type            TEXT        NOT NULL
                        CHECK (leg_type IN ('flight', 'accommodation', 'activity', 'transit')),
    date_local          DATE        NOT NULL,
    city                TEXT        NOT NULL,
    title               TEXT        NOT NULL,
    address_en          TEXT,
    address_ja          TEXT,
    contact_phone       TEXT,
    confirmation_number TEXT,
    notes_en            TEXT,
    notes_ja            TEXT,
    start_time          TIME,
    end_time            TIME,
    created_utc         TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**CHECK constraint on leg_type:** `flight`, `accommodation`, `activity`, `transit`

**Indexes:**
- `idx_itinerary_date` — btree on `(date_local)`
- `idx_itinerary_city` — btree on `(city)`

**Design rationale:**
- `leg_sequence` is explicit ordering. Gaps allowed for inserts. Not auto-derived
  from date because flights cross midnight.
- `date_local` is the local date at the destination, NOT UTC.
- `start_time` / `end_time` are local time; null if all-day.
- Cities: Osaka, Nara, Kyoto, Kanazawa, Tokyo, Sakai, etc.


### Table: `trip_pois`

Points of interest by city with crowd intelligence and user-layer tags.

```sql
CREATE TABLE trip_pois (
    id              SERIAL          PRIMARY KEY,
    city            TEXT            NOT NULL,
    name_en         TEXT            NOT NULL,
    name_ja         TEXT,
    category        TEXT            NOT NULL,
    lat             NUMERIC(10, 7),
    lng             NUMERIC(10, 7),
    address_en      TEXT,
    address_ja      TEXT,
    tags            TEXT[]          NOT NULL DEFAULT '{}',
    crowd_notes     TEXT,
    best_time_notes TEXT,
    source          TEXT,
    created_utc     TIMESTAMPTZ     NOT NULL DEFAULT now()
);
```

**Indexes:**
- `idx_pois_city` — btree on `(city)`
- `idx_pois_category` — btree on `(category)`
- `idx_pois_tags` — **GIN** on `(tags)`

**Category values (no CHECK constraint, convention-enforced):**
`restaurant`, `shrine`, `shopping`, `market`, `museum`, `park`, `temple`, etc.

**Tags array examples:** `ghibli`, `anime`, `knife`, `food`, `vintage-camera`,
`shopping`, `crowd-warning`, `madeline`, `brenda`, `todd`, `early-morning-only`,
`retro-gaming`.

**Source values:** `manual`, `tavily`, `google_places`.


### Table: `knowledge_items`

Trip knowledge base for AI RAG search. Covers local tips, restaurants, shops,
temples, transit, events. Used by `search_trip_knowledge` in the chat AI.

```sql
CREATE TABLE knowledge_items (
    id              SERIAL      PRIMARY KEY,
    anchor          TEXT,
    city            TEXT,
    category        TEXT,
    topic           TEXT,
    source_url      TEXT,
    content_summary TEXT,
    raw_content     TEXT,
    tavily_score    FLOAT,
    ingested_utc    TIMESTAMPTZ DEFAULT now()
);
```

**Indexes:**
- `idx_knowledge_city` — btree on `(city)`
- `idx_knowledge_category` — btree on `(category)`
- `uidx_knowledge_anchor_cat_url` — **UNIQUE** btree on
  `(COALESCE(anchor, ''), COALESCE(category, ''), COALESCE(source_url, ''))`
- `uidx_knowledge_items` — **UNIQUE** btree on
  `(city, topic, COALESCE(source_url, ''))`

**Design rationale:**
- `anchor` ties knowledge to a geographic anchor point (e.g. `tokyo-sugamo`,
  `dotonbori`, `ghibli-museum`). NULL means interest-based, not location-anchored.
- Two unique indexes enforce deduplication: one by anchor/category/source_url,
  another by city/topic/source_url.
- `tavily_score` is the relevance score from Tavily search results.
- `raw_content` stores full scraped text; `content_summary` is an AI-readable
  1-3 sentence summary of actionable knowledge.
- Seeded by `tools/seed_tokyo_knowledge.py` and
  `app-services/shogun-web/shogun-web-api/tools/seed_osaka_kanazawa_knowledge.py`.


### Table: `wishlist_items`

User-submitted wishlist items for the trip. Can be approved/rejected.

```sql
CREATE TABLE wishlist_items (
    id                    SERIAL      PRIMARY KEY,
    requested_by          INTEGER     NOT NULL REFERENCES users(id),
    city                  TEXT,
    description           TEXT        NOT NULL,
    ai_research           TEXT,
    status                TEXT        NOT NULL DEFAULT 'pending'
                          CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by           INTEGER     REFERENCES users(id),
    reviewed_at           TIMESTAMPTZ,
    itinerary_note        TEXT,
    created_utc           TIMESTAMPTZ NOT NULL DEFAULT now(),
    category              VARCHAR(30) DEFAULT 'general',
    needs_reservation     BOOLEAN     NOT NULL DEFAULT false,
    reservation_confirmed BOOLEAN     NOT NULL DEFAULT false
);
```

**CHECK constraint on status:** `pending`, `approved`, `rejected`

**Indexes:**
- `idx_wishlist_status` — btree on `(status)`
- `idx_wishlist_requested_by` — btree on `(requested_by)`

**FK constraints:**
- `requested_by` -> `users(id)` (no CASCADE — blocks user deletion if items exist)
- `reviewed_by` -> `users(id)` (no CASCADE)


### Table: `checklist_items`

Packing checklist for the trip. Items toggled packed/unpacked.

```sql
CREATE TABLE checklist_items (
    id          SERIAL      PRIMARY KEY,
    category    TEXT        NOT NULL DEFAULT 'misc',
    item_name   TEXT        NOT NULL,
    packed      BOOLEAN     NOT NULL DEFAULT false,
    notes       TEXT,
    created_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Indexes:**
- `idx_checklist_category` — btree on `(category)`
- `idx_checklist_packed` — btree on `(packed)`

**Category values (convention, no CHECK):**
`documents`, `clothing`, `electronics`, `toiletries`, `misc`

**Note:** No FK to users. Checklist is shared across all travelers.


### Table: `budget_items`

Trip expense tracking. No FK to users (shared budget).

```sql
CREATE TABLE budget_items (
    id          SERIAL          PRIMARY KEY,
    trip_date   DATE,
    category    VARCHAR(30)     NOT NULL DEFAULT 'other',
    description TEXT            NOT NULL,
    amount_jpy  INTEGER         NOT NULL,
    created_utc TIMESTAMPTZ     NOT NULL DEFAULT now()
);
```

**Budget category values (enforced in application code, not DB CHECK):**
`food`, `transport`, `accommodation`, `activity`, `shopping`, `other`

**No indexes beyond PK.**

---

## Table Relationships

```
users (1) ──< user_preferences (N)     [ON DELETE CASCADE]
users (1) ──< wishlist_items (N)       [requested_by, reviewed_by — no CASCADE]

trip_itinerary  — standalone (no FKs)
trip_pois       — standalone (no FKs)
knowledge_items — standalone (no FKs)
checklist_items — standalone (no FKs)
budget_items    — standalone (no FKs)
```

Only `user_preferences` cascades on user deletion. `wishlist_items` blocks
deletion of referenced users (both `requested_by` and `reviewed_by`).

---

## Knowledge Item Category Taxonomy

Categories used across all knowledge seeds and trip_pois:

| Category | Used In | Description |
|:---------|:--------|:------------|
| `restaurant` | knowledge_items, trip_pois | Restaurants, cafes, food stalls, bakeries |
| `shopping` | knowledge_items, trip_pois | Shops, markets, malls, specialty stores |
| `temple` | knowledge_items, trip_pois | Temples, shrines, castles, gardens, historic sites |
| `museum` | knowledge_items, trip_pois | Museums, galleries, cultural exhibitions |
| `transit` | knowledge_items, trip_itinerary | Train routes, bus loops, IC cards, airport transfers |
| `vintage` | knowledge_items | Vintage clothing shops (Shimokitazawa, Koenji) |
| `skincare` | knowledge_items | Skincare/beauty shops (Cosme, Matsumoto Kiyoshi) |
| `street_food` | knowledge_items | Street food vendors, food alleys |
| `events` | knowledge_items | Seasonal events, hanami, festivals |
| `local_market` | knowledge_items | Neighborhood markets, shopping streets |
| `pharmacy` | knowledge_items | Pharmacies near specific locations |
| `sakura` | knowledge_items | Cherry blossom spots, bloom forecasts |

**trip_pois additional categories (convention):**
`shrine`, `park`, `market`

**Knowledge anchors (geographic groupings):**
Tokyo: `tokyo-sugamo`, `tokyo-ueno`, `ghibli-museum`, plus NULL (interest-based)
Osaka: `dotonbori`, `namba`, `shinsekai`, `shinsaibashi`, etc.
Kanazawa: no anchors used (all NULL)

---

## shogun_app Role and Grant Management

### Role definition

```sql
CREATE ROLE shogun_app
    WITH LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    CONNECTION LIMIT 10;
```

### Current grants (from 002_grants.sql)

```sql
GRANT CONNECT ON DATABASE shogun_v1 TO shogun_app;
GRANT USAGE   ON SCHEMA   public    TO shogun_app;

-- Full CRUD on the four original MVP tables
GRANT SELECT, INSERT, UPDATE, DELETE
    ON users, user_preferences, trip_itinerary, trip_pois
    TO shogun_app;

-- Sequence access for SERIAL inserts
GRANT USAGE, SELECT
    ON SEQUENCE users_id_seq, user_preferences_id_seq,
               trip_itinerary_id_seq, trip_pois_id_seq
    TO shogun_app;
```

### Tables NOT yet granted to shogun_app

The following tables were added after the initial grant migration and may need
grants depending on whether shogun-core accesses them:

- `wishlist_items` — created 2026-03-13
- `checklist_items` — created 2026-03-16
- `knowledge_items` — created 2026-03-16 (seed script)
- `budget_items` — created by shogun-web

**When adding a new table, always add a grant migration:**

```sql
-- Template: grant for new table
GRANT SELECT, INSERT, UPDATE, DELETE ON <table_name> TO shogun_app;
GRANT USAGE, SELECT ON SEQUENCE <table_name>_id_seq TO shogun_app;
```

---

## Migration Conventions

### File naming

Migrations live in `database/migrations/`. Two naming patterns exist:

1. **Numbered prefix (original schema):** `000_`, `001_`, `002_`, `002a_`
2. **Date prefix (post-initial):** `YYYYMMDD_<description>.sql`

Use the date prefix pattern for all new migrations.

### File header template

Every migration file must include this header:

```sql
-- ============================================================
-- Migration: YYYYMMDD_<description>.sql
-- Database:  shogun_v1 (dbnode-01, 192.168.71.221)
-- Schema:    public
-- Persona:   dba-agent
--
-- Purpose: <what this migration does>
--
-- Rollback: <rollback instructions>
-- ============================================================
```

### Execution patterns

**On dbnode-01 (three-node topology):**
```bash
ssh -i ~/.ssh/dba-agent_ed25519 dba-agent@192.168.71.221
sudo -u postgres psql -d shogun_v1 -f /path/to/migration.sql
```

### Rules

- Wrap DDL in `BEGIN; ... COMMIT;` for atomicity
- Always include rollback instructions (commented DROP statements at bottom)
- Use `IF NOT EXISTS` / `IF EXISTS` for idempotent operations
- Include `COMMENT ON TABLE` and `COMMENT ON COLUMN` for all new objects
- Never run migrations as `shogun_app` — always as `postgres` via dba-agent
- After creating tables, create a separate grant migration or append to 002_grants.sql

### Migration execution order

```
000_rename_legacy_tables.sql     — Renames old users table
001_initial_schema.sql           — Creates users, user_preferences, trip_itinerary, trip_pois
002a_create_app_user.sql         — Creates shogun_app role (run first if role missing)
002_grants.sql                   — Grants for shogun_app on initial tables
20260313_wishlist_items.sql      — Creates wishlist_items
20260316_checklist_and_knowledge.sql — Creates checklist_items, knowledge_items
```

---

## Data Validation Queries

### Row counts (expected from 2026-03-18 backup)

```sql
SELECT 'users' AS t, count(*) FROM users
UNION ALL SELECT 'user_preferences', count(*) FROM user_preferences
UNION ALL SELECT 'trip_itinerary', count(*) FROM trip_itinerary
UNION ALL SELECT 'trip_pois', count(*) FROM trip_pois
UNION ALL SELECT 'knowledge_items', count(*) FROM knowledge_items
UNION ALL SELECT 'checklist_items', count(*) FROM checklist_items
UNION ALL SELECT 'wishlist_items', count(*) FROM wishlist_items
UNION ALL SELECT 'budget_items', count(*) FROM budget_items;
```

Expected: users=1, user_preferences=8, trip_itinerary=15, trip_pois=30,
knowledge_items=170, checklist_items=15, wishlist_items=0, budget_items=0.

### FK integrity checks

```sql
-- Orphaned user_preferences (should return 0)
SELECT count(*) FROM user_preferences up
LEFT JOIN users u ON u.id = up.user_id
WHERE u.id IS NULL;

-- Orphaned wishlist requested_by (should return 0)
SELECT count(*) FROM wishlist_items wi
LEFT JOIN users u ON u.id = wi.requested_by
WHERE u.id IS NULL;
```

### Knowledge items by city/category

```sql
SELECT city, category, count(*)
FROM knowledge_items
GROUP BY city, category
ORDER BY city, category;
```

### Null checks for required fields

```sql
-- Users with missing display_name
SELECT count(*) FROM users WHERE display_name IS NULL;

-- POIs with missing name_en or city
SELECT count(*) FROM trip_pois WHERE name_en IS NULL OR city IS NULL;

-- Itinerary legs with missing title or city
SELECT count(*) FROM trip_itinerary WHERE title IS NULL OR city IS NULL;

-- Knowledge items with missing content_summary
SELECT count(*) FROM knowledge_items WHERE content_summary IS NULL;
```

---

## Query Patterns Used by shogun-core

These are the actual query patterns from `app-services/shogun-core/app/db.py`:

### Look up user by Telegram ID

```sql
SELECT * FROM users WHERE telegram_user_id = %s;
```

### Get user preferences

```sql
SELECT category, preference_key, preference_value, notes
FROM user_preferences WHERE user_id = %s
ORDER BY category, preference_key;
```

### Get today's itinerary

```sql
SELECT leg_type, city, title, address_en, address_ja,
       start_time, end_time, notes_en
FROM trip_itinerary WHERE date_local = %s
ORDER BY leg_sequence;
```

### Determine current city from date

```sql
SELECT city FROM trip_itinerary
WHERE leg_type = 'accommodation' AND date_local <= %s
ORDER BY date_local DESC LIMIT 1;
```

### Get POIs by city (with optional category filter)

```sql
SELECT name_en, name_ja, category, address_en, lat, lng,
       tags, crowd_notes, best_time_notes
FROM trip_pois WHERE city = %s [AND category = %s];
```

---

## Legacy Tables

17 tables from a prior web-app version exist in shogun_v1. They are preserved
(Option B from migration 000) and should NOT be modified.

The only renamed table is `users_v1_legacy` (was `users`). All other legacy
tables retain their original names: `activities`, `documents`, `expenses`,
`survey_votes`, `surveys`, `trip_members`, `trip_events`, `lodging_details`,
`sources`, `ingestion_runs`, `trips`, etc.

Legacy tables with data: `trip_events` (7), `lodging_details` (3), `sources` (2),
`ingestion_runs` (2), `trips` (1). All others have 0 rows.

---

## Backup and Restore

Full backup location: `database/backups/`

Current backup: `2026-03-18_shogun_v1_full_restore.sql`
- Generated from dbnode-01 PostgreSQL 17 before three-node migration (2026-03-18)
- Uses `--clean --if-exists` (DROP + recreate)
- Does NOT include extensions (pgvector, pgcrypto, pg_stat_statements)
- Transport to dbnode-01: via git only (no SCP/SFTP per transport rules)

### Creating a new backup

```bash
# On dbnode-01 as dba-agent:
sudo -u postgres pg_dump -d shogun_v1 --clean --if-exists \
  -f /tmp/YYYY-MM-DD_shogun_v1_full_restore.sql
```

Then copy to `database/backups/` via git workflow.
