# Shogun + Platform — Disaster Recovery Checklist
Created: 2026-03-14
Situation: Proxmox host lost. Rebuilding from GitHub repos on Windows laptop + Docker Desktop.

---

## Architecture: 3 Logical Nodes → 1 Docker Host

The node model is preserved conceptually. Physically everything runs on Docker Desktop.

| Was | Now |
|-----|-----|
| svcnode-01 (Docker host) | Docker Desktop on laptop |
| dbnode-01 (bare metal Postgres) | `platform-postgres` container |
| brainnode-01 (shogun-core systemd) | `shogun-core` container |
| Pi-hole DNS for FQDNs | Container names on `platform_net` |
| Telegram webhook mode | **Telegram polling mode** (no public URL needed) |

> **Key insight:** Telegram gateway runs in polling mode. Bot dials OUT to Telegram.
> No public IP, no Cloudflare Tunnel needed for the bot. Works fine on laptop.

---

## PHASE 0 — Verify What's Already on the Laptop
*~10 minutes — do this first before anything else*

### 0.1 Confirm repos are present and current
```powershell
# In PowerShell
git -C C:\git\work\shogun log --oneline -5
git -C C:\git\work\platform log --oneline -5
```
Both should show recent commits. If they look stale, you need GitHub access first (Phase 1).

### 0.2 Check SSH keys on laptop
```powershell
ls ~/.ssh/
```
Look for:
- `devops-agent_ed25519_clean` + `.pub`  → DevOps persona key
- `dba-agent_ed25519` + `.pub`           → DBA persona key
- Any existing GitHub key

If both devops-agent keys exist → you may already have GitHub access (test in Phase 1).

### 0.3 Confirm Docker Desktop is running
```powershell
docker version
docker network ls
```

---

## PHASE 1 — GitHub SSH Key Setup
*~15 minutes*

> Skip this phase if `git pull` works already.

### 1.1 Generate GitHub SSH key (if needed)
```powershell
# In PowerShell
ssh-keygen -t ed25519 -C "ibbytech-laptop-github" -f "$HOME\.ssh\github_ibbytech_ed25519"
```

### 1.2 Add to SSH config
Create or edit `~/.ssh/config`:
```
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_ibbytech_ed25519
```

### 1.3 Add public key to GitHub
```powershell
# Copy public key to clipboard
Get-Content "$HOME\.ssh\github_ibbytech_ed25519.pub" | Set-Clipboard
```
Go to GitHub → Settings → SSH and GPG keys → New SSH key → paste.

### 1.4 Test and pull latest
```powershell
ssh -T git@github.com
git -C C:\git\work\shogun pull
git -C C:\git\work\platform pull
```

---

## PHASE 2 — Regenerate All Secrets
*~30 minutes — open these tabs in parallel*

Do NOT wait for backup extraction. Regenerate everything fresh.

### 2.1 External API Keys (go get these now)

| Key | Where | Variable name |
|-----|-------|---------------|
| Gemini API key | console.cloud.google.com → APIs → Gemini | `GOOGLE_API_KEY` |
| Google Places API key | console.cloud.google.com → APIs → Places | `GOOGLE_PLACES_API_KEY` |
| Tavily API key | app.tavily.com → API Keys (use Standard, NOT MCP) | `TAVILY_API_KEY` |
| OpenAI API key | platform.openai.com → API Keys | `OPENAI_API_KEY` |
| Telegram bot token | @BotFather → /mybots → your bot → API Token | `TELEGRAM_BOT_TOKEN` |

### 2.2 Passwords — Pick New Values Now
Write these down somewhere safe before proceeding.

| Variable | What it is | Notes |
|----------|-----------|-------|
| `POSTGRES_PASSWORD` | Postgres superuser password | Use strong random string |
| `SHOGUN_DB_PASSWORD` | shogun_app user password | Different from superuser |
| `PLACES_DB_PASSWORD` | places_app user password | Different from superuser |
| `VALKEY_PASSWORD` | Valkey auth password | Use strong random string |
| `TELEGRAM_SEND_SECRET` | Internal auth for POST /send | Any random string, 32+ chars |
| `FIRECRAWL_API_KEY` | Self-set key for scraper service | You choose this value |

### 2.3 Generate Random Secrets
```powershell
# Generate random 32-char strings for passwords/secrets
# Run this for each password you need
[System.Web.Security.Membership]::GeneratePassword(32,4)
# Or simpler:
-join ((48..57 + 65..90 + 97..122) | Get-Random -Count 32 | % {[char]$_})
```

### 2.4 Your Telegram User ID (needed for ALLOWED_USER_IDS)
Message @userinfobot on Telegram — it replies with your numeric ID.

---

## PHASE 3 — Create All .env Files
*~30 minutes — do this after Phase 2*

### URL Mapping: FQDNs → Container Names
All services now talk to each other via Docker container names, not FQDNs.

| Was (lab FQDN) | Now (Docker container name) |
|----------------|----------------------------|
| `valkey.platform.ibbytech.com` | `platform-valkey` |
| `llm.platform.ibbytech.com` | `http://platform-llm-gateway:8000` |
| `telegram.platform.ibbytech.com` | `http://platform-telegram-gateway:3001` |
| `scrape.platform.ibbytech.com` | `http://platform-scraper:8080` |
| `tavily.platform.ibbytech.com` | `http://platform-tavily:8000` |
| `192.168.71.221` (dbnode-01) | `platform-postgres` |
| `dbnode-01` | `platform-postgres` |

### 3.1 platform/services/llm-gateway/.env
```env
OPENAI_API_KEY=<from Phase 2>
OPENAI_BASE_URL=https://api.openai.com/v1
GOOGLE_API_KEY=<from Phase 2>
GOOGLE_BASE_URL=https://generativelanguage.googleapis.com
ANTHROPIC_API_KEY=<optional — skip if not using Claude>
ANTHROPIC_BASE_URL=https://api.anthropic.com
DEFAULT_EMBED_PROVIDER=openai
DEFAULT_EMBED_MODEL=text-embedding-3-small
DEFAULT_CHAT_PROVIDER=google
DEFAULT_CHAT_MODEL=gemini-2.0-flash
```

### 3.2 platform/services/telegram-gateway/.env
```env
TELEGRAM_BOT_TOKEN=<from Phase 2>
ALLOWED_USER_IDS=<your Telegram numeric ID>
UPSTREAM_URL=http://shogun-core:8082/telegram/events
TELEGRAM_MODE=polling
SEND_SECRET=<TELEGRAM_SEND_SECRET from Phase 2>
SEND_API_PORT=3001
UPSTREAM_TIMEOUT_MS=30000
CAP_CAN_SEARCH=true
CAP_CAN_SCRAPE=true
CAP_CAN_FETCH_FILES=true
```

### 3.3 platform/services/valkey/.env
```env
VALKEY_PASSWORD=<from Phase 2>
```

### 3.4 platform/services/places-google/.env
```env
GOOGLE_PLACES_API_KEY=<from Phase 2>
PORT=8081
GOOGLE_PLACES_BASE_URL=https://places.googleapis.com/v1
GOOGLE_NEARBY_FIELDMASK=places.id,places.displayName,places.location,places.types,places.rating,places.userRatingCount,places.priceLevel,places.primaryType,places.googleMapsUri,places.formattedAddress
GOOGLE_TEXTSEARCH_FIELDMASK=places.id,places.displayName,places.location,places.types,places.rating,places.userRatingCount,places.priceLevel,places.primaryType,places.googleMapsUri,places.formattedAddress
GOOGLE_DETAILS_FIELDMASK=id,displayName,formattedAddress,location,googleMapsUri,websiteUri,internationalPhoneNumber,rating,userRatingCount,priceLevel,primaryType,types,regularOpeningHours,paymentOptions
PGHOST=platform-postgres
PGPORT=5432
PGDATABASE=platform_v1
PGUSER=places_app
PGPASSWORD=<PLACES_DB_PASSWORD from Phase 2>
DEFAULT_LANGUAGE_CODE=en
DEFAULT_REGION_CODE=US
DEFAULT_RADIUS_M=2000
DEFAULT_MAX_RESULTS=50
CACHE_TTL_SECONDS=86400
```

### 3.5 platform/services/scraper/.env
```env
FIRECRAWL_API_KEY=<FIRECRAWL_API_KEY you chose in Phase 2>
OPENAI_API_KEY=<from Phase 2>
```

### 3.6 platform/services/tavily/.env
```env
TAVILY_API_KEY=<from Phase 2>
```

### 3.7 shogun/app-services/shogun-core/.env
```env
DB_HOST=platform-postgres
DB_PORT=5432
DB_NAME=shogun_v1
DB_USER=shogun_app
DB_PASSWORD=<SHOGUN_DB_PASSWORD from Phase 2>
VALKEY_HOST=platform-valkey
VALKEY_PORT=6379
VALKEY_PASSWORD=<from Phase 2>
LLM_GATEWAY_URL=http://platform-llm-gateway:8000
TELEGRAM_GATEWAY_URL=http://platform-telegram-gateway:3001
TELEGRAM_SEND_SECRET=<TELEGRAM_SEND_SECRET from Phase 2>
TELEGRAM_BOT_TOKEN=<from Phase 2>
TAVILY_GATEWAY_URL=http://platform-tavily:8000
SCRAPER_GATEWAY_URL=http://platform-scraper:8080
APP_HOST=0.0.0.0
APP_PORT=8082
LOG_LEVEL=info
```

### 3.8 shogun/app-services/shogun-web/shogun-web-api/.env
```env
SHOGUN_BYPASS_AUTH=true
DATABASE_URL=postgresql://shogun_app:<SHOGUN_DB_PASSWORD>@platform-postgres/shogun_v1
VALKEY_URL=redis://:< VALKEY_PASSWORD>@platform-valkey:6379
LLM_GATEWAY_URL=http://platform-llm-gateway:8000
NEXT_PUBLIC_API_URL=http://localhost:8083
```

---

## PHASE 4 — Add PostgreSQL to Platform Stack + Start Platform
*~30 minutes*

### 4.1 Add postgres to platform infra compose
Edit `platform/infra/compose/docker-compose.infra.yml` — add postgres service:

```yaml
  postgres:
    image: postgres:17
    container_name: platform-postgres
    restart: unless-stopped
    environment:
      POSTGRES_PASSWORD: <POSTGRES_PASSWORD from Phase 2>
      POSTGRES_USER: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5432:5432"
    networks:
      - platform_net

volumes:
  postgres_data:
```

> Skip Traefik for now — comment it out or remove it. Use direct ports.
> Remove the Traefik labels from all services too (or leave them — they'll just be ignored).

### 4.2 Start the platform_net network + postgres first
```powershell
cd C:\git\work\platform\infra\compose
docker compose -f docker-compose.infra.yml up -d postgres
# Wait 15 seconds for postgres to initialize
docker logs platform-postgres --tail 20
```

### 4.3 Create databases and users
```powershell
# Connect to postgres container
docker exec -it platform-postgres psql -U postgres
```
Then run:
```sql
-- Create databases
CREATE DATABASE platform_v1;
CREATE DATABASE shogun_v1;

-- Create app users
CREATE USER places_app WITH PASSWORD '<PLACES_DB_PASSWORD>';
CREATE USER shogun_app WITH PASSWORD '<SHOGUN_DB_PASSWORD>';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE platform_v1 TO places_app;
GRANT ALL PRIVILEGES ON DATABASE shogun_v1 TO shogun_app;

-- Also grant schema permissions (needed for Postgres 15+)
\c platform_v1
GRANT ALL ON SCHEMA public TO places_app;
\c shogun_v1
GRANT ALL ON SCHEMA public TO shogun_app;

\q
```

### 4.4 Start platform services
```powershell
# Start Valkey
cd C:\git\work\platform\services\valkey
docker compose up -d

# Start LLM gateway
cd C:\git\work\platform\services\llm-gateway
docker compose up -d

# Start Telegram gateway
cd C:\git\work\platform\services\telegram-gateway
docker compose up -d

# Start Places gateway
cd C:\git\work\platform\services\places-google
docker compose up -d

# Start Scraper + Firecrawl
cd C:\git\work\platform\services\scraper
docker compose up -d

# Start Tavily
cd C:\git\work\platform\services\tavily
docker compose up -d
```

### 4.5 Quick health check on platform
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```
All platform containers should show `Up`.

---

## PHASE 5 — Start Shogun Services
*~30 minutes*

### 5.1 Start shogun-core
```powershell
cd C:\git\work\shogun\app-services\shogun-core
docker compose up -d --build
```

### 5.2 Start shogun-web-api
```powershell
cd C:\git\work\shogun\app-services\shogun-web\shogun-web-api
docker compose up -d --build
```

### 5.3 Start shogun-web-ui
```powershell
cd C:\git\work\shogun\app-services\shogun-web\shogun-web-ui
docker compose up -d --build
```

---

## PHASE 6 — Database Schema + Data Ingest
*~45 minutes*

### 6.1 Run schema migrations
Schema files should be in the shogun repo. Find and run them:
```powershell
# Find migration/schema files
Get-ChildItem -Path C:\git\work\shogun -Recurse -Include "*.sql" | Select-Object FullName
```

Apply against the running postgres container:
```powershell
# Example - adjust path as needed
docker exec -i platform-postgres psql -U postgres -d shogun_v1 < C:\git\work\shogun\db\schema.sql
```

### 6.2 Re-seed Todd's user profile
The seeded itinerary and user data from March was NOT in any backup.
Re-run the data ingest scripts:
```powershell
# Find ingest scripts
Get-ChildItem -Path C:\git\work\shogun -Recurse -Include "*.py" | Where-Object Name -match "ingest|seed"
```

---

## PHASE 7 — Validate
*~30 minutes*

### 7.1 Telegram bot alive
Send a text message to the Shogun bot. Should respond.

### 7.2 Location trigger works
Share live location in Telegram. Should get a recommendation within 30 seconds.

### 7.3 LLM pipeline works
Ask Shogun something in Japanese travel context. Should get a coherent response.

### 7.4 Web UI accessible
Open browser: `http://localhost:3000`
Dashboard, itinerary, and city pages should load.

### 7.5 Web AI chat works
Use the chat interface in shogun-web. Should get LLM responses.

---

## Secrets Master Reference

Keep this populated as you complete Phase 2. Store securely (not in Git).

```
# External API Keys
GOOGLE_API_KEY (Gemini)    =
GOOGLE_PLACES_API_KEY      =
TAVILY_API_KEY             =
OPENAI_API_KEY             =
TELEGRAM_BOT_TOKEN         =

# Database
POSTGRES_PASSWORD (superuser) =
SHOGUN_DB_PASSWORD (shogun_app) =
PLACES_DB_PASSWORD (places_app) =

# Internal Tokens
VALKEY_PASSWORD            =
TELEGRAM_SEND_SECRET       =
FIRECRAWL_API_KEY (self-set) =

# Your Telegram User ID (for ALLOWED_USER_IDS)
TODD_TELEGRAM_ID           =

# GitHub SSH key location
~/.ssh/github_ibbytech_ed25519
```

---

## What Is NOT Needed for Shogun Recovery

Skip these — they add complexity without helping Shogun run:

- **Traefik** — skip, use direct ports
- **Loki / Grafana** — skip, not needed for the trip
- **Reddit gateway** — skip unless specifically needed
- **Cloudflare Tunnel** — not needed; Telegram runs in polling mode
- **3-node physical separation** — everything on Docker Desktop is fine for the trip

---

## After the Trip

Once the trip is done and you have time:
- Rebuild Proxmox or acquire alternative hypervisor
- Restore the 3-node physical architecture
- Re-establish node SSH personas (devops-agent, dba-agent)
- Move services back to proper nodes
- Re-enable Traefik for FQDN routing
- Plan Cloudflare cutover properly
