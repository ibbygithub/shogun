# Execution Brief 1 — Database Schema (3 New Tables)

**Agent:** DBA Agent on dbnode-01
**Persona:** `dba-agent` via SSH key `~/.ssh/dba-agent_ed25519`
**Target:** dbnode-01 (192.168.71.221) — PostgreSQL 17, database `shogun_v1`
**Estimated time:** 15-20 minutes
**Dependencies:** None — run first

---

## Task

Create three new tables in `shogun_v1` and grant access to `shogun_app`.

## SSH Connection

```bash
ssh -i ~/.ssh/dba-agent_ed25519 dba-agent@192.168.71.221
psql -U postgres -d shogun_v1
```

## SQL to Execute

```sql
-- =============================================================
-- Table 1: poi_guides — Rich AI-generated guide for each POI
-- =============================================================
CREATE TABLE poi_guides (
  id              SERIAL PRIMARY KEY,
  trip_poi_id     INT NOT NULL REFERENCES trip_pois(id) ON DELETE CASCADE,
  poi_type        TEXT,                     -- museum, shrine, shopping_district, park, market, neighborhood, landmark, event
  overview        TEXT,                     -- What it is, why it matters
  why_go          TEXT,                     -- Interest profile + narrative
  whats_there     TEXT,                     -- Sub-areas, exhibits, shops, activities
  hours_info      TEXT,                     -- Hours, closed days, seasonal notes
  admission_info  TEXT,                     -- Cost, tickets, reservations
  time_estimate   TEXT,                     -- 'quick_stop', 'standard_visit', 'deep_visit'
  transit_info    TEXT,                     -- Nearest station, neighborhood context
  tips            TEXT,                     -- Best time, crowds, cash/card, caveats
  trip_context    TEXT,                     -- Why this fits YOUR itinerary day
  photos          JSONB DEFAULT '[]'::jsonb, -- [{url, attribution, source}]
  official_url    TEXT,
  sources         JSONB DEFAULT '[]'::jsonb, -- [{url, title}]
  hours_verified  BOOLEAN DEFAULT FALSE,
  completeness    TEXT DEFAULT 'pending',    -- 'full', 'partial', 'minimal', 'pending'
  generated_utc   TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT uq_poi_guides_trip_poi UNIQUE (trip_poi_id)
);

CREATE INDEX idx_poi_guides_trip_poi_id ON poi_guides(trip_poi_id);

-- =============================================================
-- Table 2: social_notes — Trip photo/text capture for social media
-- =============================================================
CREATE TABLE social_notes (
  id               SERIAL PRIMARY KEY,
  user_id          INT REFERENCES users(id),
  telegram_user_id BIGINT,
  note_type        TEXT NOT NULL,            -- 'photo', 'text', 'photo_text'
  text_content     TEXT,
  photo_file_id    TEXT,                     -- Telegram file_id for retrieval
  photo_url        TEXT,                     -- Downloaded/proxied URL if resolved
  latitude         FLOAT,
  longitude        FLOAT,
  address          TEXT,                     -- Reverse-geocoded address
  city             TEXT,
  captured_utc     TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_social_notes_user ON social_notes(telegram_user_id);
CREATE INDEX idx_social_notes_city ON social_notes(city);

-- =============================================================
-- Table 3: bug_reports — Issue tracking with future agent handoff
-- =============================================================
CREATE TABLE bug_reports (
  id               SERIAL PRIMARY KEY,
  reporter_id      INT REFERENCES users(id),
  telegram_user_id BIGINT,
  raw_text         TEXT NOT NULL,            -- Exactly what user typed
  component        TEXT,                     -- AI-classified: core, web-ui, web-api, telegram, data, unknown
  severity         TEXT DEFAULT 'normal',    -- 'normal', 'urgent'
  status           TEXT DEFAULT 'open',      -- 'open', 'in_progress', 'resolved', 'wontfix'
  ai_summary       TEXT,                     -- AI-normalized description
  resolution       TEXT,
  reported_utc     TIMESTAMPTZ DEFAULT now(),
  resolved_utc     TIMESTAMPTZ
);

CREATE INDEX idx_bug_reports_status ON bug_reports(status);

-- =============================================================
-- Grants for shogun_app (application user)
-- =============================================================
GRANT SELECT, INSERT, UPDATE, DELETE ON poi_guides TO shogun_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON social_notes TO shogun_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON bug_reports TO shogun_app;
GRANT USAGE, SELECT ON SEQUENCE poi_guides_id_seq TO shogun_app;
GRANT USAGE, SELECT ON SEQUENCE social_notes_id_seq TO shogun_app;
GRANT USAGE, SELECT ON SEQUENCE bug_reports_id_seq TO shogun_app;
```

## Verification Queries

After creating tables, run these to confirm:

```sql
-- Confirm all 3 tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name IN ('poi_guides', 'social_notes', 'bug_reports')
ORDER BY table_name;

-- Confirm grants
SELECT grantee, table_name, privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'shogun_app' AND table_name IN ('poi_guides', 'social_notes', 'bug_reports')
ORDER BY table_name, privilege_type;

-- Confirm trip_pois count (should be ~111)
SELECT city, count(*) FROM trip_pois GROUP BY city ORDER BY count(*) DESC;
```

## Migration File

Save the SQL to a migration file on the laptop repo:

**File:** `C:\git\work\shogun\database\migrations\20260321_poi_guides_social_bugs.sql`

Copy the SQL above into this file for version control.

## Done Criteria

- [ ] All 3 tables created in shogun_v1
- [ ] All grants applied to shogun_app
- [ ] Verification queries return expected results
- [ ] Migration file saved to repo
- [ ] No errors in psql output
