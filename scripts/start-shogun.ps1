# start-shogun.ps1
# Starts the full Shogun + Platform stack on Docker Desktop (laptop mode).
# Always uses `docker compose up -d` — never `docker restart`.
# This ensures each service re-reads its .env file on every start.
#
# Usage: .\scripts\start-shogun.ps1
# Run from anywhere — uses absolute paths.

$ErrorActionPreference = "Stop"

$SHOGUN   = "C:\git\work\shogun"
$PLATFORM = "C:\git\work\platform"

Push-Location   # Save caller's working directory — restored at end

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function OK($msg)   { Write-Host "    $msg" -ForegroundColor Green }
function Fail($msg) { Write-Host "    ERROR: $msg" -ForegroundColor Red; exit 1 }

# ── 1. Platform network + Postgres ──────────────────────────────────────────
Step "Platform network + Postgres"
Set-Location "$PLATFORM\infra\compose"
docker compose -f docker-compose.infra.yml up -d
if ($LASTEXITCODE -ne 0) { Fail "infra failed" }

Step "Cloudflare Tunnel"
docker compose -f docker-compose.infra.yml up -d cloudflared
if ($LASTEXITCODE -ne 0) { Fail "cloudflared failed" }

Step "Waiting for Postgres to be healthy..."
$retries = 0
do {
    Start-Sleep -Seconds 3
    $health = docker inspect --format="{{.State.Health.Status}}" platform-postgres 2>$null
    $retries++
    if ($retries -gt 10) { Fail "Postgres did not become healthy" }
} while ($health -ne "healthy")
OK "Postgres healthy"

# ── 2. Platform services ─────────────────────────────────────────────────────
Step "Valkey"
Set-Location "$PLATFORM\services\valkey"
docker compose up -d
if ($LASTEXITCODE -ne 0) { Fail "valkey failed" }

Step "LLM Gateway"
Set-Location "$PLATFORM\services\llm-gateway"
docker compose up -d
if ($LASTEXITCODE -ne 0) { Fail "llm-gateway failed" }

Step "Telegram Gateway"
Set-Location "$PLATFORM\services\telegram-gateway"
docker compose up -d
if ($LASTEXITCODE -ne 0) { Fail "telegram-gateway failed" }

Step "Places Gateway"
Set-Location "$PLATFORM\services\places-google"
docker compose up -d
if ($LASTEXITCODE -ne 0) { Fail "places-google failed" }

Step "Tavily"
Set-Location "$PLATFORM\services\tavily"
docker compose up -d
if ($LASTEXITCODE -ne 0) { Fail "tavily failed" }

Step "Scraper"
Set-Location "$PLATFORM\services\scraper"
docker compose up -d
if ($LASTEXITCODE -ne 0) { Fail "scraper failed" }

Step "Reddit Gateway"
Set-Location "$PLATFORM\services\reddit-gateway"
docker compose up -d
if ($LASTEXITCODE -ne 0) { Fail "reddit-gateway failed" }

# ── 3. Shogun services ───────────────────────────────────────────────────────
Step "shogun-core"
Set-Location "$SHOGUN\app-services\shogun-core"
docker compose up -d
if ($LASTEXITCODE -ne 0) { Fail "shogun-core failed" }

Step "shogun-web-api"
Set-Location "$SHOGUN\app-services\shogun-web\shogun-web-api"
docker compose up -d
if ($LASTEXITCODE -ne 0) { Fail "shogun-web-api failed" }

Step "shogun-web-ui"
Set-Location "$SHOGUN\app-services\shogun-web\shogun-web-ui"
docker compose up -d
if ($LASTEXITCODE -ne 0) { Fail "shogun-web-ui failed" }

# ── 4. Status ────────────────────────────────────────────────────────────────
Step "Final status"
docker ps --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}"

Write-Host "`nShogun is up. Web UI: http://localhost:3010`n" -ForegroundColor Green
Pop-Location    # Return to caller's original directory
