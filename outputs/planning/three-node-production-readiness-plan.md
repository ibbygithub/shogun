# Plan: Three-Node Production Readiness Audit
Date: 2026-03-20
Status: In Progress

## Objective

After emergency laptop Docker Desktop recovery (2026-03-15) and successful three-node
migration (2026-03-18), stale documentation and uncommitted code changes remain.
The AI agents working in this repo still believe Docker runs on the laptop.
Docker Desktop on the laptop is now permanently disabled.

This plan audits all documentation, consolidates git state, verifies the three-node
production stack, and validates all services — including chat tools — are fully green.

---

## Current State

### Infrastructure (confirmed live 2026-03-18 migration report)

| Node | Role | Services |
|------|------|----------|
| svcnode-01 (192.168.71.220) | Platform services — Docker | valkey, llm-gateway, telegram-gateway, tavily, scraper-api, reddit-gateway, places-google |
| brainnode-01 (192.168.71.222) | Shogun application tier — Docker | shogun-core, shogun-web-api, shogun-web-ui, platform-cloudflared |
| dbnode-01 (192.168.71.221) | PostgreSQL 17 only | shogun_v1 database |
| ibbytech-laptop | Control plane only — code editing, git, SSH | NO Docker, NO production workloads |

### Git State (as of plan creation)

| Location | Branch | Status |
|----------|--------|--------|
| laptop/shogun | develop | 3 modified files, 7 untracked — uncommitted AI brain fixes |
| brainnode-01/shogun | feature/20260317-ai-intelligence-overhaul | 6 commits ahead of origin (Google Maps work) |
| svcnode-01/platform | develop | 6 docker-compose.yml port binding changes — uncommitted |

### Documentation with Stale Laptop/Docker Desktop References

| File | Issue |
|------|-------|
| `.claude/CLAUDE.md` | brainnode-01 says "Python/systemd (no Docker)" — was pre-migration description |
| `.claude/assets/topology.json` | brainnode-01 roles list MCP servers/cron, not Shogun application services |
| `.claude/skills/shogun-dba/SKILL.md` | "From Docker Desktop (local dev)" connection section |
| `.claude/rules/11-shogun-system-context.md` | brainnode-01 listed as "Automation, ETL. NO Services." |
| `outputs/planning/planning-state.md` | Extensive Docker Desktop / localhost references throughout |
| `../ibbytech-foundation/.claude/rules/01-infrastructure.md` | brainnode-01 "Does NOT: run Docker" — now incorrect |

---

## Scope

**Included:**
- Documentation audit and update across shogun repo and ibbytech-foundation
- Git consolidation (commit, push, merge all in-flight work)
- svcnode-01 platform repo docker-compose commit
- Service health verification on all three nodes
- Full test suite (test_chat_tools.py + service endpoints)
- Validation evidence report

**Excluded:**
- Feature work or code changes beyond what is already in-flight
- Database schema changes
- Cloudflare / DNS configuration

---

## Phases

### Phase 1: Documentation Cleanup
**Goal:** No file in the repo instructs agents to use Docker Desktop on the laptop for Shogun services.

Files to update:
1. `.claude/CLAUDE.md` — brainnode-01 now runs Docker for Shogun application tier
2. `.claude/assets/topology.json` — correct brainnode-01 roles
3. `.claude/skills/shogun-dba/SKILL.md` — remove Docker Desktop connection section
4. `.claude/rules/11-shogun-system-context.md` — update brainnode-01 role
5. `outputs/planning/planning-state.md` — update infra summary to 3-node reality
6. `../ibbytech-foundation/.claude/rules/01-infrastructure.md` — brainnode-01 now runs Docker

**Exit criteria:** `grep -r "docker desktop\|windows laptop" .claude/ outputs/planning/planning-state.md` returns only historical/archived references.

---

### Phase 2: Git Consolidation
**Goal:** All in-flight code is committed, pushed, and merged to develop. Nodes are on develop.

Steps:
1. Laptop: create `feature/20260320-production-readiness`, commit AI brain fixes + doc updates, push
2. brainnode-01: push `feature/20260317-ai-intelligence-overhaul` to origin
3. Merge brainnode-01 feature branch → develop (Yellow Zone — confirmation required)
4. Merge laptop feature branch → develop (Yellow Zone — confirmation required)
5. brainnode-01: git pull develop, switch to develop
6. svcnode-01 platform: commit port-binding changes, push to platform develop

**Exit criteria:** `git log --oneline origin/develop` shows all work. Both nodes on develop.

---

### Phase 3: Deploy & Service Verification
**Goal:** All containers running the latest code with correct configuration.

Steps:
1. brainnode-01: `docker compose pull && docker compose up -d` for shogun services
2. svcnode-01: verify platform services still healthy (no restart needed unless config changed)
3. Health checks:
   - `curl http://brainnode-01:8082/health` — shogun-core
   - `curl http://brainnode-01:8090/health` — shogun-web-api
   - `curl http://brainnode-01:3010` — shogun-web-ui
   - `curl http://svcnode-01:8080/health` — llm-gateway
   - `curl http://svcnode-01:8084/health` — tavily

**Exit criteria:** All health endpoints return HTTP 200.

---

### Phase 4: Validation Tests
**Goal:** All 15 chat tool tests pass.

Steps:
1. Run `python tools/test_chat_tools.py` targeting brainnode-01:8090
2. Investigate any failures
3. Write validation evidence report to `outputs/validation/2026-03-20_production-readiness_report.md`

**Exit criteria:** test_chat_tools.py exits GREEN (15/15 pass).

---

## Risks

| Risk | Mitigation |
|------|------------|
| brainnode-01 docker-compose missing PLACES_GATEWAY_URL | Add to .env on brainnode-01 during Phase 3 |
| Merge conflict between two feature branches | Merge brainnode-01 branch first; laptop branch rebases on top |
| test_chat_tools.py endpoint mismatch | Verify SHOGUN_API_URL env in test script before running |

---

## Evidence
Output: `outputs/validation/2026-03-20_production-readiness_report.md`
