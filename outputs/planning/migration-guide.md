# Shogun — Migration Guide
Last updated: 2026-03-15

How to move the full Shogun + Platform stack to a new Docker host.

---

## What Was Built

Everything runs as Docker containers on a single host (laptop in current config).
Two Git repos contain all source code and compose files:

| Repo | What's in it |
|------|-------------|
| `github.com/[org]/platform` | All platform services: LLM gateway, Telegram gateway, Places gateway, Tavily, Scraper, Valkey, Traefik |
| `github.com/[org]/shogun` | shogun-core, shogun-web-api, shogun-web-ui, DB migrations, seed scripts, startup scripts |

### The 10 containers

| Container | Repo | Image built from |
|-----------|------|-----------------|
| `platform-postgres` | platform/infra/compose | `postgres:17` (pulled) |
| `platform-valkey` | platform/services/valkey | `valkey/valkey:8-alpine` (pulled) |
| `platform-llm-gateway` | platform/services/llm-gateway | Dockerfile in repo |
| `platform-telegram-gateway` | platform/services/telegram-gateway | Dockerfile in repo |
| `platform-places-google` | platform/services/places-google | Dockerfile in repo |
| `platform-tavily` | platform/services/tavily | Dockerfile in repo |
| `platform-scraper-api` | platform/services/scraper | Dockerfile in repo |
| `shogun-core` | shogun/app-services/shogun-core | Dockerfile in repo |
| `shogun-web-api` | shogun/app-services/shogun-web/shogun-web-api | Dockerfile in repo |
| `shogun-web-ui` | shogun/app-services/shogun-web/shogun-web-ui | Dockerfile in repo |

### What is NOT in Git (must be moved manually)

| Asset | Location on current host | Notes |
|-------|--------------------------|-------|
| `.env` files | One per service directory | All secrets — see table below |
| PostgreSQL data | Docker volume `platform-postgres-data` | Dump and restore |
| Valkey AOF | Docker volume `platform-valkey-data` | Optional — session state only, can start fresh |

---

## .env File Locations

Every `.env` file has a `.env.example` committed to Git as a template.

| File location | Key secrets it holds |
|---------------|---------------------|
| `platform/infra/compose/.env` | `POSTGRES_PASSWORD` (superuser) |
| `platform/services/llm-gateway/.env` | `GOOGLE_API_KEY`, `OPENAI_API_KEY` |
| `platform/services/telegram-gateway/.env` | `TELEGRAM_BOT_TOKEN`, `SEND_SECRET`, `ALLOWED_USER_IDS` |
| `platform/services/places-google/.env` | `GOOGLE_PLACES_API_KEY`, `PGPASSWORD` (places_app) |
| `platform/services/tavily/.env` | `TAVILY_API_KEY` |
| `platform/services/scraper/.env` | `FIRECRAWL_API_KEY`, `OPENAI_API_KEY` |
| `platform/services/valkey/.env` | `VALKEY_PASSWORD` |
| `shogun/app-services/shogun-core/.env` | All of the above + `DB_PASSWORD`, `TELEGRAM_SEND_SECRET` |
| `shogun/app-services/shogun-web/shogun-web-api/.env` | `DATABASE_URL`, `VALKEY_URL`, `LLM_GATEWAY_URL` |

---

## Migration Steps (New Host)

### Prerequisites on new host
- Docker + Docker Compose installed
- Git installed
- At least 4GB RAM, 20GB disk

### Step 1 — Clone repos
```bash
mkdir -p /opt/git/work
cd /opt/git/work
git clone git@github.com:[org]/platform.git
git clone git@github.com:[org]/shogun.git
git checkout develop   # on both repos
```

### Step 2 — Copy .env files
Copy every `.env` file from the old host to the same relative path on the new host.
Use the `.env.example` in each service directory as the reference for what's needed.

If migrating from the laptop, zip and transfer via a USB drive or private file share.
**Never commit .env files to Git.**

### Step 3 — Restore the database (optional but recommended)
On the old host, dump the data:
```bash
docker exec platform-postgres pg_dumpall -U postgres > shogun_backup.sql
```

On the new host, after Postgres is running:
```bash
cat shogun_backup.sql | docker exec -i platform-postgres psql -U postgres
```

If you skip this, run the migration scripts and seed scripts fresh (see below).

### Step 4 — Start the stack
If on Linux/Mac:
```bash
# Adapt start-shogun.ps1 paths for Linux — or run compose commands manually
# Same order: infra → platform services → shogun services
```

If on another Windows machine:
```powershell
.\scripts\start-shogun.ps1
```

### Step 5 — If starting fresh (no DB restore)
Run schema migrations and seed data:
```bash
# Schema (run in order)
cat database/migrations/001_initial_schema.sql | docker exec -i platform-postgres psql -U postgres -d shogun_v1
cat database/migrations/002_grants.sql         | docker exec -i platform-postgres psql -U postgres -d shogun_v1
cat database/migrations/20260313_wishlist_items.sql | docker exec -i platform-postgres psql -U postgres -d shogun_v1
cat platform/services/places-google/sql/001_create_places_schema.sql | docker exec -i platform-postgres psql -U postgres -d platform_v1

# Seed data (run from shogun repo)
docker exec shogun-core python tools/seed_itinerary.py
docker exec shogun-core python tools/seed_pois.py
# seed_users.py requires TELEGRAM_USER_ID_BRENDA and TELEGRAM_USER_ID_MADELINE in .env first
docker exec shogun-core python tools/seed_users.py
```

---

## Returning to 3-Node Architecture (Post-Trip)

When Proxmox is rebuilt (or a new hypervisor is set up), the migration is:

1. Stand up three Linux VMs: svcnode-01, dbnode-01, brainnode-01
2. Move Postgres container → bare metal Postgres on dbnode-01
3. Move shogun-core container → Python/systemd on brainnode-01
4. Move all remaining containers → svcnode-01 (Docker host)
5. Restore Pi-hole DNS for internal FQDNs
6. Re-enable Traefik for hostname routing
7. Remove `localhost:3010` direct port binding — everything routes through Traefik
8. Add Cloudflare Tunnel for public exposure

The Docker Compose files are already written for this architecture — they're just running
in single-host mode now. Switching back is a `.env` URL update, not a rewrite.

---

## Startup / Shutdown

```powershell
# Start everything
.\scripts\start-shogun.ps1

# Stop everything (preserves data)
.\scripts\stop-shogun.ps1
```

Web UI: http://localhost:3010
Telegram: live (polling mode, works as long as laptop is on)
