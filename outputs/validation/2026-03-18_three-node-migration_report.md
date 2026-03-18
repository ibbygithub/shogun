# Validation Report — Three-Node Migration
**Date:** 2026-03-18
**Task:** Migrate from Docker Desktop (laptop) to svcnode-01 + brainnode-01 + dbnode-01
**Outcome:** ✅ PASS — all services running, DB restored, stack functional

---

## Infrastructure State After Migration

### brainnode-01 (192.168.71.222) — Shogun Application Tier

| Container | Status | Port |
|-----------|--------|------|
| shogun-core | ✅ Up | 127.0.0.1:8082 |
| shogun-web-api | ✅ Up | 0.0.0.0:8090 |
| shogun-web-ui | ✅ Up | 0.0.0.0:3010 |
| platform-cloudflared | ✅ Up | (tunnel) |

### svcnode-01 (192.168.71.220) — Platform Services Tier

| Container | Status | Port |
|-----------|--------|------|
| platform-valkey | ✅ Up | 0.0.0.0:6379 |
| platform-llm-gateway | ✅ Up | 0.0.0.0:8080 |
| platform-telegram-gateway | ✅ Up | 0.0.0.0:3001 |
| platform-tavily | ✅ Up | 0.0.0.0:8084 |
| platform-scraper-api | ✅ Up | 0.0.0.0:8083 |
| platform-reddit-gateway | ✅ Up | 0.0.0.0:8082 |
| platform-places-google | ✅ Up | internal only |

### dbnode-01 (192.168.71.221) — Database Tier

| Check | Result |
|-------|--------|
| PostgreSQL 17.7 | ✅ Running |
| shogun_v1 restored | ✅ 15 legs, 30 POIs, 170 knowledge items, 15 checklist, 8 prefs |
| shogun_app user | ✅ Created with correct password |
| Extensions | ✅ vector, pgcrypto, pg_stat_statements |
| pg_hba.conf | ✅ brainnode-01 (192.168.71.222) allowed |

---

## Smoke Test Results

| Test | Result |
|------|--------|
| shogun-core health | ✅ `{"ok":true}` |
| shogun-web-api health | ✅ `{"status":"ok"}` |
| shogun-web-ui HTTP 200 | ✅ |
| Itinerary API (DB read) | ✅ 15 legs from dbnode-01 |
| DB connection log | ✅ `DB connection OK (shogun_v1 @ 192.168.71.221)` |
| Cloudflare tunnel | ✅ 4 connections registered (sjc01, sjc07) |

---

## Migration Steps Executed

1. **Phase 0 — Data backup**: `pg_dump` of laptop postgres → committed to GitHub
2. **Phase 1 — Node assessment**: All three nodes confirmed reachable, Mar 08 state mapped
3. **Phase 2 — svcnode-01**: Platform repo updated to develop, 7 services started with cross-node port bindings
4. **Phase 3 — dbnode-01**: Schema wiped (DROP SCHEMA CASCADE), extensions recreated, restore dump applied, grants applied, pg_hba.conf updated
5. **Phase 4 — brainnode-01**: Docker installed, shogun repo cloned, .env files deployed with correct node IPs, 4 containers started

---

## Open Items — Action Required

| Item | Owner | Priority |
|------|-------|----------|
| Fix Cloudflare dashboard origin URL: change from `http://192.168.71.10:3010` to `http://shogun-web-ui:3000` | Todd (browser) | 🔴 High — Cloudflare won't work until this is done |
| Add `api.shogun.ibbytech.com` Cloudflare hostname → `http://shogun-web-api:8090` for external API access | Todd (browser) | 🔴 High — browser API calls broken externally |
| Rebuild shogun-web-ui with correct `NEXT_PUBLIC_API_URL=https://api.shogun.ibbytech.com` | Code | 🔴 High — after Todd adds the hostname |
| Make docker socket permission persistent on brainnode-01 (currently `chmod 666` — survives restart but not clean) | Ops | 🟡 Medium |
| Create start/stop scripts for three-node topology | Ops | 🟡 Medium |
| Stop laptop Docker stack (after Cloudflare verified from phone) | Todd | 🟡 After validation |

---

## Architecture Notes

- **Cloudflared** moved from svcnode-01 to **brainnode-01** so it can reach `shogun-web-ui` via Docker network name (`http://shogun-web-ui:3000`)
- **Platform services** now bind to `0.0.0.0` (not `127.0.0.1`) for cross-node access from brainnode-01
- **NEXT_PUBLIC_API_URL** set to `https://shogun.ibbytech.com` in current build — needs to be `https://api.shogun.ibbytech.com` once that hostname is configured in Cloudflare
- **Laptop Docker stack** still running — do NOT stop until Cloudflare is validated from an external device
