# Firecrawl — Restart Policy Fix
Date: 2026-03-14
Branch: hotfix/20260314-firecrawl-restart-policy
Persona: devops-agent (svcnode-01)
Status: COMPLETE — All 4 containers up with restart: unless-stopped

---

## Trigger

Hardware crash on svcnode-01. All platform containers recovered automatically
via existing restart policies. Firecrawl's 4 containers (api, worker, redis,
playwright-service) did not recover because the upstream docker-compose.yaml
had no restart policy defined on any service.

---

## Root Cause

`/opt/firecrawl/docker-compose.yaml` — no `restart:` directive on any service.
Docker default is `no` (never restart). On host reboot or OOM kill, all 4
containers stay dead.

---

## Fix Applied

Created `/opt/firecrawl/docker-compose.override.yaml` with `restart: unless-stopped`
on all 4 services. Docker Compose automatically merges base + override files.
The upstream `docker-compose.yaml` is left untouched — the override survives
future `git pull` operations on the Firecrawl repo.

```yaml
services:
  playwright-service:
    restart: unless-stopped
  api:
    restart: unless-stopped
  worker:
    restart: unless-stopped
  redis:
    restart: unless-stopped
```

Override file path: `/opt/firecrawl/docker-compose.override.yaml`

---

## Verification

```
firecrawl-worker-1               Up (stable)   RestartPolicy: unless-stopped ✅
firecrawl-api-1                  Up (stable)   RestartPolicy: unless-stopped ✅
firecrawl-redis-1                Up (stable)   RestartPolicy: unless-stopped ✅
firecrawl-playwright-service-1   Up (stable)   RestartPolicy: unless-stopped ✅
```

Restart policy confirmed via `docker inspect firecrawl-api-1`.

---

## Impact

- `platform-scraper-api` backend restored — web scraping functional again
- Firecrawl will now auto-recover after any future host reboot or crash
- No change to upstream Firecrawl code or configuration

---

## Rollback

To remove restart policy: delete `/opt/firecrawl/docker-compose.override.yaml`
and run `docker compose up -d` to recreate containers without it.
