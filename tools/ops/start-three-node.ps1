# start-three-node.ps1
# Starts all Shogun services across the three-node topology.
# Run from: ibbytech-laptop (Windows PowerShell)
# Personas: devops-agent (svcnode-01, brainnode-01)
#
# Node roles:
#   dbnode-01   (192.168.71.221) — PostgreSQL (systemd, auto-starts, not managed here)
#   svcnode-01  (192.168.71.220) — Platform services (Docker Compose)
#   brainnode-01 (192.168.71.222) — Shogun app services (Docker Compose)

$ErrorActionPreference = "Stop"

$DEVOPS_KEY  = "$env:USERPROFILE\.ssh\devops-agent_ed25519_clean"
$SVCNODE     = "devops-agent@192.168.71.220"
$BRAINNODE   = "devops-agent@192.168.71.222"
$DBNODE_IP   = "192.168.71.221"

function ssh-run {
    param([string]$host, [string]$cmd, [string]$label)
    Write-Host "`n==> [$label]" -ForegroundColor Cyan
    $result = ssh -i $DEVOPS_KEY -o StrictHostKeyChecking=accept-new $host $cmd
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    FAILED (exit $LASTEXITCODE)" -ForegroundColor Red
    } else {
        Write-Host $result
    }
    return $LASTEXITCODE
}

Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "║  Shogun Three-Node Stack — START         ║" -ForegroundColor Yellow
Write-Host "╚══════════════════════════════════════════╝`n" -ForegroundColor Yellow

# ── Step 1: Verify database reachable ─────────────────────────────────────────
Write-Host "── [1/3] Database (dbnode-01) ──────────────────────────────" -ForegroundColor White
$pg = ssh -i $DEVOPS_KEY -o StrictHostKeyChecking=accept-new `
    "dba-agent@$DBNODE_IP" `
    "sudo -u postgres psql -d shogun_v1 -c 'SELECT COUNT(*) FROM trip_itinerary;' -t 2>&1" 2>&1
if ($pg -match "\d+") {
    Write-Host "    PostgreSQL OK — trip_itinerary rows: $($pg.Trim())" -ForegroundColor Green
} else {
    Write-Host "    WARNING: Could not verify PostgreSQL — $pg" -ForegroundColor Yellow
    Write-Host "    Continuing anyway — PostgreSQL is a systemd service and may already be up." -ForegroundColor Yellow
}

# ── Step 2: Platform services on svcnode-01 ───────────────────────────────────
Write-Host "`n── [2/3] Platform services (svcnode-01) ────────────────────" -ForegroundColor White

$platformServices = @(
    "valkey",
    "llm-gateway",
    "telegram-gateway",
    "tavily",
    "scraper",
    "reddit-gateway",
    "places-google"
)

foreach ($svc in $platformServices) {
    $path = "/opt/git/work/platform/services/$svc"
    ssh-run $SVCNODE "cd $path && docker compose up -d 2>&1 | tail -3" $svc | Out-Null
}

# ── Step 3: Shogun app services on brainnode-01 ───────────────────────────────
Write-Host "`n── [3/3] Shogun app services (brainnode-01) ────────────────" -ForegroundColor White

# Ensure Docker socket is accessible (idempotent)
ssh-run $BRAINNODE "sudo /bin/chmod 666 /var/run/docker.sock" "docker-socket-perms" | Out-Null

$shogunServices = @(
    "~/git-work/shogun/app-services/shogun-core",
    "~/git-work/shogun/app-services/shogun-web/shogun-web-api",
    "~/git-work/shogun/app-services/shogun-web/shogun-web-ui",
    "~/git-work/shogun/app-services/platform-cloudflared"
)

foreach ($path in $shogunServices) {
    $label = Split-Path $path -Leaf
    ssh-run $BRAINNODE "cd $path && docker compose up -d 2>&1 | tail -3" $label | Out-Null
}

# ── Final status check ────────────────────────────────────────────────────────
Write-Host "`n── Container status ─────────────────────────────────────────" -ForegroundColor White
Write-Host "`nsvcnode-01:" -ForegroundColor Cyan
ssh -i $DEVOPS_KEY $SVCNODE "docker ps --format 'table {{.Names}}\t{{.Status}}'"
Write-Host "`nbrainnode-01:" -ForegroundColor Cyan
ssh -i $DEVOPS_KEY $BRAINNODE "docker ps --format 'table {{.Names}}\t{{.Status}}'"

Write-Host "`n✅ Stack start complete." -ForegroundColor Green
