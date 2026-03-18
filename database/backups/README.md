# Database Backups

## 2026-03-18_shogun_v1_full_restore.sql

**Purpose:** Full restore artifact for shogun_v1 — generated 2026-03-18 from
laptop Docker postgres (platform-postgres container) before migrating back to
three-node topology (dbnode-01).

**Source:** `platform-postgres` Docker container, laptop Docker Desktop
**Generated:** 2026-03-18
**Postgres version:** 17.9

### Data snapshot

| Table | Rows |
|-------|------|
| users | 1 |
| trip_itinerary | 15 |
| trip_pois | 30 |
| user_preferences | 8 |
| budget_items | 0 |
| wishlist_items | 0 |
| checklist_items | 15 |
| knowledge_items | 170 |

Knowledge items breakdown: 100 Tokyo + 70 Osaka/Kanazawa

### How to apply to dbnode-01

Persona: `dba-agent`

```bash
ssh -i ~/.ssh/dba-agent_ed25519 dba-agent@192.168.71.221

# On dbnode-01:
sudo -u postgres psql -d shogun_v1 -f /tmp/2026-03-18_shogun_v1_full_restore.sql
```

**Important:** The dump uses `--clean --if-exists` — it will DROP and recreate
all tables before inserting data. Safe to apply to the Mar 08 backup state.
Extensions (pgvector, pgcrypto, pg_stat_statements) are NOT in this dump —
they must already exist on dbnode-01. Run grants (002_grants.sql, 002a_create_app_user.sql)
after applying if the shogun_app user doesn't exist on dbnode-01.

### Delivery to dbnode-01

Transport rule: no SCP/SFTP. Use git.

```bash
# On dbnode-01 — pull from git, then apply:
cd /opt/git/work/shogun
git pull origin feature/20260317-ai-intelligence-overhaul
sudo -u postgres psql -d shogun_v1 \
  -f database/backups/2026-03-18_shogun_v1_full_restore.sql
```
