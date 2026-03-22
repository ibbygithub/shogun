# Test Plan — Brief 1 (DB Schema) + Brief 3 (Telegram Commands)

**Date:** 2026-03-21
**Scope:** 3 new tables + /bug and /social commands with photo capture mode
**Prerequisites:** Migration run on dbnode-01, shogun-core rebuilt on brainnode-01

---

## Section 1: Database Schema (Brief 1)

### 1.1 Table Creation

| # | Test | Method | Expected Result |
|---|------|--------|-----------------|
| 1.1.1 | poi_guides table exists | `\d poi_guides` on dbnode-01 | Table with all 16 columns, SERIAL PK, FK to trip_pois(id) ON DELETE CASCADE |
| 1.1.2 | social_notes table exists | `\d social_notes` on dbnode-01 | Table with all 11 columns, SERIAL PK, FK to users(id) |
| 1.1.3 | bug_reports table exists | `\d bug_reports` on dbnode-01 | Table with all 11 columns, SERIAL PK, FK to users(id) |

### 1.2 Constraints and Indexes

| # | Test | Method | Expected Result |
|---|------|--------|-----------------|
| 1.2.1 | poi_guides unique constraint | `INSERT` two rows with same trip_poi_id | Second insert fails with unique violation on `uq_poi_guides_trip_poi` |
| 1.2.2 | poi_guides FK cascade | `DELETE FROM trip_pois WHERE id = X` (test row) | Corresponding poi_guides row is deleted |
| 1.2.3 | idx_poi_guides_trip_poi_id exists | `\di idx_poi_guides*` | btree index on trip_poi_id |
| 1.2.4 | idx_social_notes_user exists | `\di idx_social_notes*` | btree index on telegram_user_id |
| 1.2.5 | idx_social_notes_city exists | `\di idx_social_notes*` | btree index on city |
| 1.2.6 | idx_bug_reports_status exists | `\di idx_bug_reports*` | btree index on status |
| 1.2.7 | social_notes.note_type NOT NULL | `INSERT` with null note_type | Fails with NOT NULL violation |
| 1.2.8 | bug_reports.raw_text NOT NULL | `INSERT` with null raw_text | Fails with NOT NULL violation |

### 1.3 Grants

| # | Test | Method | Expected Result |
|---|------|--------|-----------------|
| 1.3.1 | shogun_app CRUD on poi_guides | Query `information_schema.table_privileges` | SELECT, INSERT, UPDATE, DELETE granted |
| 1.3.2 | shogun_app CRUD on social_notes | Query `information_schema.table_privileges` | SELECT, INSERT, UPDATE, DELETE granted |
| 1.3.3 | shogun_app CRUD on bug_reports | Query `information_schema.table_privileges` | SELECT, INSERT, UPDATE, DELETE granted |
| 1.3.4 | shogun_app sequence access | Query `information_schema.usage_privileges` or test INSERT as shogun_app | USAGE, SELECT on all 3 sequences |
| 1.3.5 | End-to-end: INSERT as shogun_app | Connect as shogun_app, INSERT into each table | All 3 inserts succeed, RETURNING id works |

### 1.4 Defaults

| # | Test | Method | Expected Result |
|---|------|--------|-----------------|
| 1.4.1 | poi_guides.photos default | INSERT without photos column | `'[]'::jsonb` stored |
| 1.4.2 | poi_guides.sources default | INSERT without sources column | `'[]'::jsonb` stored |
| 1.4.3 | poi_guides.completeness default | INSERT without completeness | `'pending'` stored |
| 1.4.4 | poi_guides.hours_verified default | INSERT without hours_verified | `false` stored |
| 1.4.5 | bug_reports.severity default | INSERT without severity | `'normal'` stored |
| 1.4.6 | bug_reports.status default | INSERT without status | `'open'` stored |
| 1.4.7 | All 3 tables timestamp defaults | INSERT without timestamp columns | `now()` populated |

---

## Section 2: /bug Command (Brief 3)

### 2.1 Command Parsing

| # | Test | Input | Expected Result |
|---|------|-------|-----------------|
| 2.1.1 | No description | `/bug` | Returns usage text: "Usage: /bug <describe the issue>..." |
| 2.1.2 | Empty after /bug | `/bug   ` (whitespace only) | Returns usage text |
| 2.1.3 | Valid bug report | `/bug AI is returning HTML in chat` | Inserts row, returns "Bug #N reported" with component + severity |
| 2.1.4 | Unregistered user | `/bug something` (no user) | Returns "You're not registered in Shogun. Ask Todd to add you." |

### 2.2 Component Classification

| # | Test | Input Description | Expected Component |
|---|------|-------------------|-------------------|
| 2.2.1 | Core keywords | "AI response is too slow" | `core` (matches "ai", "response") |
| 2.2.2 | Web-UI keywords | "Dashboard page is blank" | `web-ui` (matches "dashboard", "page") |
| 2.2.3 | Web-API keywords | "API endpoint returns 500" | `web-api` (matches "api", "endpoint", "500") |
| 2.2.4 | Telegram keywords | "Bot command not responding" | `telegram` (matches "bot", "command") |
| 2.2.5 | Data keywords | "POI data is missing for Kyoto" | `data` (matches "poi", "data", "missing") |
| 2.2.6 | No match | "Colors look weird" | `unknown` |
| 2.2.7 | First-match wins | "AI chat on web page" | `core` (matches "ai" before "web"/"page") |

### 2.3 Severity Detection

| # | Test | Input Description | Expected Severity |
|---|------|-------------------|------------------|
| 2.3.1 | Normal | "AI response is slow" | `normal` |
| 2.3.2 | Urgent — "broken" | "Search is broken" | `urgent` |
| 2.3.3 | Urgent — "crash" | "App crash on photo send" | `urgent` |
| 2.3.4 | Urgent — "down" | "Bot is down" | `urgent` |
| 2.3.5 | Urgent — "critical" | "Critical data loss" | `urgent` |

### 2.4 Database Persistence

| # | Test | Method | Expected Result |
|---|------|--------|-----------------|
| 2.4.1 | Row inserted | Query `bug_reports` after /bug | Row exists with correct reporter_id, telegram_user_id, raw_text |
| 2.4.2 | ai_summary truncated | Send /bug with 600-char description | ai_summary is first 500 chars |
| 2.4.3 | reported_utc populated | Check row after insert | Timestamp within last minute |
| 2.4.4 | DB error handling | Simulate DB down (or invalid FK) | Returns "Failed to record bug report. Please try again." |

---

## Section 3: /social Command (Brief 3)

### 3.1 Inline Text Note

| # | Test | Input | Expected Result |
|---|------|-------|-----------------|
| 3.1.1 | Text note | `/social Amazing ramen at this tiny shop!` | Inserts social_notes row with note_type='text', returns "Note #N saved!" |
| 3.1.2 | City auto-tagged | `/social` text note on a day with city in itinerary | city column populated from itinerary |
| 3.1.3 | Unregistered user | `/social test` (no user) | Returns registration prompt |

### 3.2 Capture Mode Entry

| # | Test | Input | Expected Result |
|---|------|-------|-----------------|
| 3.2.1 | Enter mode | `/social` (no args) | Returns "Social capture mode active (5 minutes)" message |
| 3.2.2 | Valkey flag set | Check `shogun:social:{uid}` after `/social` | Key exists with TTL ~300s |
| 3.2.3 | TTL auto-expire | Wait 5+ minutes after `/social` | Key no longer exists in Valkey |

### 3.3 Text Capture in Social Mode

| # | Test | Input | Expected Result |
|---|------|-------|-----------------|
| 3.3.1 | Text during mode | Enter `/social`, then send "Great view from the tower" | Inserts social_notes row, returns "Note #N saved to your trip journal!" |
| 3.3.2 | Mode cleared after capture | Send text in social mode, then send another text | Second text goes to normal LLM chat (not captured) |
| 3.3.3 | Bypasses LLM | Text in social mode | No LLM call made, text saved directly to DB |

### 3.4 Photo Capture in Social Mode

| # | Test | Input | Expected Result |
|---|------|-------|-----------------|
| 3.4.1 | Photo without caption | Enter `/social`, send photo | Inserts row: note_type='photo', photo_file_id set, text_content NULL |
| 3.4.2 | Photo with caption | Enter `/social`, send photo with caption "Sakura!" | Inserts row: note_type='photo_text', photo_file_id set, text_content="Sakura!" |
| 3.4.3 | Photo with location | Enter `/social`, send photo with location data in payload | latitude + longitude columns populated |
| 3.4.4 | Mode cleared after photo | Send photo in social mode, then send another photo | Second photo goes to normal Gemini analysis |
| 3.4.5 | Return message — no location | Photo without location | "Photo #N saved to your trip journal!" |
| 3.4.6 | Return message — with location | Photo with location | "Photo #N saved to your trip journal! (location tagged)" |
| 3.4.7 | Return message — with caption | Photo with caption "Beautiful temple" | Message includes caption excerpt |

### 3.5 Edge Cases

| # | Test | Scenario | Expected Result |
|---|------|----------|-----------------|
| 3.5.1 | /social then /help | Enter social mode, send /help | /help is handled by command router (commands take priority over social mode because / prefix is checked first) |
| 3.5.2 | /social then /bug | Enter social mode, send /bug report | /bug executes normally (commands bypass social capture) |
| 3.5.3 | No photos in payload | Social mode + photo message with empty photos array | _save_social_photo handles gracefully (file_id=None) |
| 3.5.4 | DB error on capture | Social mode + DB unreachable | Returns error message, social mode NOT cleared (user can retry) |

---

## Section 4: /help Update

| # | Test | Input | Expected Result |
|---|------|-------|-----------------|
| 4.1 | /help includes /bug | Send `/help` | Output contains "/bug [description] — report an issue with Shogun" |
| 4.2 | /help includes /social | Send `/help` | Output contains "/social — save photos and notes for your trip journal" |
| 4.3 | Command ordering | Send `/help` | /bug and /social appear between /research and /quiet |

---

## Section 5: Integration / End-to-End

| # | Test | Scenario | Expected Result |
|---|------|----------|-----------------|
| 5.1 | Full /bug flow | Send `/bug Bot photo analysis is broken` via Telegram | Receive confirmation with bug ID, component=telegram or core, severity=urgent ("broken"), row in DB |
| 5.2 | Full /social text flow | Send `/social Incredible tonkotsu at this spot` via Telegram | Receive "Note #N saved!", row in social_notes with city auto-tagged |
| 5.3 | Full /social photo flow | Send `/social` → send photo with caption "Best matcha" | Receive capture mode message, then "Photo #N saved!" with caption excerpt |
| 5.4 | Social mode timeout | Send `/social`, wait 6 minutes, send text | Text goes to normal LLM chat (not captured) |
| 5.5 | Normal photo after social clear | Complete a social capture, send another photo | Photo analyzed by Gemini as usual |

---

## Verification Queries (DB)

Run after migration to confirm schema:

```sql
-- 1. Confirm all 3 tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('poi_guides', 'social_notes', 'bug_reports')
ORDER BY table_name;

-- 2. Confirm grants for shogun_app
SELECT grantee, table_name, privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'shogun_app'
  AND table_name IN ('poi_guides', 'social_notes', 'bug_reports')
ORDER BY table_name, privilege_type;

-- 3. Confirm sequence grants
SELECT grantee, object_name, privilege_type
FROM information_schema.usage_privileges
WHERE grantee = 'shogun_app'
  AND object_name LIKE '%_id_seq'
ORDER BY object_name;

-- 4. Confirm indexes
SELECT indexname, tablename
FROM pg_indexes
WHERE tablename IN ('poi_guides', 'social_notes', 'bug_reports')
ORDER BY tablename, indexname;

-- 5. Confirm FK relationships
SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
  ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('poi_guides', 'social_notes', 'bug_reports');
```
