# stop-shogun.ps1
# Gracefully stops the full Shogun + Platform stack.
# Shogun services are stopped first, then platform.
# Postgres data and Valkey AOF are preserved in Docker volumes.
#
# Usage: .\scripts\stop-shogun.ps1

$SHOGUN   = "C:\git\work\shogun"
$PLATFORM = "C:\git\work\platform"

Push-Location   # Save caller's working directory — restored at end

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

Step "Stopping Shogun services"
Set-Location "$SHOGUN\app-services\shogun-web\shogun-web-ui";  docker compose down
Set-Location "$SHOGUN\app-services\shogun-web\shogun-web-api"; docker compose down
Set-Location "$SHOGUN\app-services\shogun-core";               docker compose down

Step "Stopping Platform services"
Set-Location "$PLATFORM\services\scraper";         docker compose down
Set-Location "$PLATFORM\services\tavily";          docker compose down
Set-Location "$PLATFORM\services\places-google";   docker compose down
Set-Location "$PLATFORM\services\telegram-gateway"; docker compose down
Set-Location "$PLATFORM\services\llm-gateway";     docker compose down
Set-Location "$PLATFORM\services\valkey";          docker compose down

Step "Stopping infra (Postgres + network)"
Set-Location "$PLATFORM\infra\compose"
docker compose -f docker-compose.infra.yml down

Write-Host "`nAll services stopped. Data volumes preserved.`n" -ForegroundColor Green
Pop-Location    # Return to caller's original directory
