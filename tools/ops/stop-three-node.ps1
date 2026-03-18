# stop-three-node.ps1
# Stops all Shogun services across the three-node topology.
# Run from: ibbytech-laptop (Windows PowerShell)
# Personas: devops-agent (svcnode-01, brainnode-01)
#
# Stop order: brainnode-01 first (app tier), then svcnode-01 (platform tier).
# dbnode-01 PostgreSQL is NOT stopped — it is a systemd service, not managed here.

$ErrorActionPreference = "Stop"

$DEVOPS_KEY  = "$env:USERPROFILE\.ssh\devops-agent_ed25519_clean"
$SVCNODE     = "devops-agent@192.168.71.220"
$BRAINNODE   = "devops-agent@192.168.71.222"

function ssh-run {
    param([string]$host, [string]$cmd, [string]$label)
    Write-Host "  -> $label" -ForegroundColor Gray
    $result = ssh -i $DEVOPS_KEY -o StrictHostKeyChecking=accept-new $host $cmd
    if ($LASTEXITCODE -ne 0) {
        Write-Host "     FAILED (exit $LASTEXITCODE)" -ForegroundColor Red
    }
    return $LASTEXITCODE
}

Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "║  Shogun Three-Node Stack — STOP          ║" -ForegroundColor Yellow
Write-Host "╚══════════════════════════════════════════╝`n" -ForegroundColor Yellow

# ── Step 1: Stop Shogun app services on brainnode-01 ─────────────────────────
Write-Host "── [1/2] Shogun app services (brainnode-01) ────────────────" -ForegroundColor White

$shogunServices = @(
    "~/git-work/shogun/app-services/platform-cloudflared",
    "~/git-work/shogun/app-services/shogun-web/shogun-web-ui",
    "~/git-work/shogun/app-services/shogun-web/shogun-web-api",
    "~/git-work/shogun/app-services/shogun-core"
)

foreach ($path in $shogunServices) {
    $label = Split-Path $path -Leaf
    ssh-run $BRAINNODE "cd $path && docker compose down 2>&1 | tail -3" $label | Out-Null
}

# ── Step 2: Stop platform services on svcnode-01 ─────────────────────────────
Write-Host "`n── [2/2] Platform services (svcnode-01) ────────────────────" -ForegroundColor White

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
    ssh-run $SVCNODE "cd $path && docker compose down 2>&1 | tail -3" $svc | Out-Null
}

Write-Host "`n✅ Stack stopped. PostgreSQL on dbnode-01 is still running (systemd service)." -ForegroundColor Green
