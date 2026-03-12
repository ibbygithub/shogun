# Project Shogun — Agent Behavior Rules

## Foundation Reference
Engineering standards: ../ibbytech-foundation
Launch command: claude --add-dir ../ibbytech-foundation

## Session Startup
Run `/start-session` at the start of every session.
Rules, behavioral directives, and skills are loaded from `../ibbytech-foundation`.

---

## Project Identity

- **Project:** Shogun — AI travel concierge for Japan trips. Telegram-delivered,
  location-aware, single user (family, ~3 users).
- **Principle:** Shogun is the reference consumer of IbbyTech platform services.
  Every capability need is evaluated as a platform service first. Shogun owns
  application logic; platform owns infrastructure.
- **Node (app):** svcnode-01 (192.168.71.220) — Docker containers — persona: devops-agent
- **Node (db):** dbnode-01 (192.168.71.221) — shogun_v1 database — persona: dba-agent
- **brainnode-01:** Not yet onboarded — no Shogun workloads on this node yet.

---

## Platform Services Consumed

Check `../platform/.claude/services/_index.md` before building anything new.

| Service | FQDN | Used for |
|:--------|:-----|:---------|
| Telegram Gateway | telegram.platform.ibbytech.com | Event ingress, bot interface |
| Google Places Gateway | places.platform.ibbytech.com | Place discovery, neighborhood anchors |
| LLM Gateway | llm.platform.ibbytech.com | Chat completions, intent detection |
| Scraper | scrape.platform.ibbytech.com | Web content when needed |
| Reddit Gateway | reddit.platform.ibbytech.com | Available if Shogun needs Reddit data |

---

## Database Routing

- **Primary database:** shogun_v1 on dbnode-01
- **Schema:** public (Shogun owns this schema entirely)
- **App user:** [to be confirmed at first DB task — check shogun_v1 role grants]
- **Google Places data:** DO NOT write to shogun_v1. Read via Google Places REST
  gateway. `platform_v1.places` is canonical — resolved 2026-03-12.

---

## Known Infrastructure State — Last Verified 2026-03-12

- **svcnode-01 Shogun checkout:** Branch `feature/gateway-pure-search-endpoints`,
  2 commits ahead of origin. Deploy branch state UNRESOLVED. Must resolve before
  any new service is deployed from this branch.
- **DNS Infrastructure:** svcnode-01 pointed at Pi-hole. dbnode-01 and brainnode-01
  owner-managed (not yet updated). Node FQDNs: svcnode-01.ibbytech.com,
  dbnode-01.ibbytech.com, brainnode-01.ibbytech.com.
- **Valkey:** Confirmed as shared platform service, pending DNS completion before
  shogun-core can be wired up.
- **shogun_v1 database:** Active. places schema DROPPED 2026-03-12.
  All place data now via platform_v1.places through REST gateway.
- **mcp_shogun / mcp_group:** Dormant. MCP deployment deferred.
  Do not modify without approved MCP architecture task plan.

---

## Open Architecture Decisions

- **Deploy branch resolution:** svcnode-01 Shogun checkout is on
  `feature/gateway-pure-search-endpoints` with 2 unmerged commits. Must decide:
  merge to main, cherry-pick, or reset before any new deployment.
- **Conversation context TTL:** 24h idle TTL suggested. Pending confirmation.
- **Location trigger threshold:** 150m + 5-minute cooldown. Pending confirmation.
- **shogun-core FQDN:** `svcnode-01.ibbytech.com:8082` for internal access.
  Public FQDN (`shogun.ibbytech.com`) deferred until Cloudflare phase.
- **MCP tool calling:** Deferred to OpenRouter planning session.
  Shogun uses direct REST calls for now. No MCP tool calling until post-MVP.
- **Postgres conversation persistence:** Valkey sufficient for MVP. Postgres
  conversation history is backlog — deferred post-MVP.

---

## Technology Registry (Approved)

| Technology | Role | Rationale | Date |
|------------|------|-----------|------|
| Python / FastAPI | shogun-core application service | Platform standard; async-capable | 2026-03-10 |
| Gemini 2.0 Flash | LLM completions, intent detection | Strong results, low cost, multimodal | 2026-03-09 |
| Valkey 8.x | Shared session/state store | Apache 2.0, Redis-protocol-compatible | 2026-03-10 |
| PostgreSQL 17 / shogun_v1 | Application database | Platform standard | 2026-02-15 |
| Telegram bot | User interface | Low-friction family interface | 2026-03-09 |
| Direct REST calls | Platform service consumption | No MCP adapter needed for MVP | 2026-03-09 |

---

## Project-Specific Rules

**Platform service-first principle:** Every time Shogun needs a capability,
evaluate it as a platform service candidate first. If it belongs on platform,
build it there. Shogun is client one; future apps follow.

**Inline processing (MVP):** Shogun uses synchronous inline processing for MVP.
No queue layer. LLM calls must complete within ~25s to avoid Telegram timeout.

**No local copies of platform services:** Shogun does not maintain copies of
llm-gateway, places-google, or telegram-ingress. Platform repo is the source
of truth for all deployed services.
