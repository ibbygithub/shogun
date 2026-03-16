# Database: shogun_v1
**Node:** dbnode-01 (192.168.71.221)
**Owner:** postgres
**App user:** shogun_app
**Schema:** public
**Last updated:** 2026-03-12

---

## Shogun MVP Tables (created 2026-03-12)

### `users`
Telegram users registered with Shogun. One row per user.

| Column | Type | Notes |
|:-------|:-----|:------|
| id | SERIAL PK | |
| telegram_user_id | BIGINT UNIQUE NOT NULL | Stable Telegram numeric ID |
| display_name | TEXT NOT NULL | Short name Shogun uses in responses |
| full_name | TEXT | Optional |
| notification_active | BOOLEAN DEFAULT true | false = no unsolicited location messages |
| language_preference | TEXT DEFAULT 'en' | |
| created_utc | TIMESTAMPTZ | |

### `user_preferences`
Trip-long preference store. Not in Valkey — survives TTL expiry.

| Column | Type | Notes |
|:-------|:-----|:------|
| id | SERIAL PK | |
| user_id | INTEGER FK → users(id) CASCADE | |
| category | TEXT | dietary / likes / dislikes / shopping / entertainment |
| preference_key | TEXT | e.g. eats, avoids, interest_type |
| preference_value | TEXT | e.g. fish, red_meat_as_protein, vintage_cameras |
| notes | TEXT | Freeform context from questionnaire |
| created_utc | TIMESTAMPTZ | |

**Indexes:** `idx_user_pref_user_id`, `idx_user_pref_category`

### `trip_itinerary`
Full trip schedule: flights, accommodation, activities, transit.

| Column | Type | Notes |
|:-------|:-----|:------|
| id | SERIAL PK | |
| leg_sequence | INTEGER | Explicit order (flights cross midnight) |
| leg_type | TEXT | flight / accommodation / activity / transit |
| date_local | DATE | Local date at destination |
| city | TEXT | Osaka / Kanazawa / Tokyo / Nara / Kyoto / Sakai / etc. |
| title | TEXT | Human-readable description |
| address_en | TEXT | |
| address_ja | TEXT | |
| contact_phone | TEXT | |
| confirmation_number | TEXT | |
| notes_en | TEXT | |
| notes_ja | TEXT | |
| start_time | TIME | Local time; null if all-day |
| end_time | TIME | |
| created_utc | TIMESTAMPTZ | |

**Indexes:** `idx_itinerary_date`, `idx_itinerary_city`

### `trip_pois`
Points of interest by city with crowd intelligence.

| Column | Type | Notes |
|:-------|:-----|:------|
| id | SERIAL PK | |
| city | TEXT | |
| name_en | TEXT NOT NULL | |
| name_ja | TEXT | |
| category | TEXT | restaurant / shrine / shopping / museum / park / market / etc. |
| lat | NUMERIC(10,7) | |
| lng | NUMERIC(10,7) | |
| address_en | TEXT | |
| address_ja | TEXT | |
| tags | TEXT[] DEFAULT '{}' | GIN-indexed. e.g. ghibli, anime, knife, madeline, early-morning-only |
| crowd_notes | TEXT | e.g. "arrive before 9am, tour buses after 9:30" |
| best_time_notes | TEXT | e.g. "dawn only — gates never close" |
| source | TEXT | manual / tavily / google_places |
| created_utc | TIMESTAMPTZ | |

**Indexes:** `idx_pois_city`, `idx_pois_category`, `idx_pois_tags` (GIN)

---

## App User: shogun_app

| Property | Value |
|:---------|:------|
| Role | shogun_app |
| Login | Yes |
| Superuser | No |
| Connection limit | 10 |
| CONNECT | shogun_v1 database |
| USAGE | public schema |
| CRUD | users, user_preferences, trip_itinerary, trip_pois |
| Sequences | users_id_seq, user_preferences_id_seq, trip_itinerary_id_seq, trip_pois_id_seq |

---

## Legacy Tables (preserved — Option B, 2026-03-12)

`users_v1_legacy` and 16 other tables from a prior web-app version of the project.
None of these are consumed by shogun-core. Do not modify without explicit task plan.

| Table | Rows | Notes |
|:------|-----:|:------|
| trip_events | 7 | Legacy data |
| lodging_details | 3 | Legacy data |
| sources | 2 | Legacy data |
| ingestion_runs | 2 | Legacy data |
| trips | 1 | Legacy data |
| users_v1_legacy | 0 | Renamed from users — old web-app schema |
| All others | 0 | Preserved as-is |

---

## Connection Method

```bash
# From dbnode-01 shell (dba-agent):
sudo -u postgres psql -d shogun_v1

# From laptop (via SSH):
ssh -i ~/.ssh/dba-agent_ed25519 dba-agent@192.168.71.221
# then: sudo -u postgres psql -d shogun_v1
```
