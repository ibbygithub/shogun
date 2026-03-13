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
- **Node (app):** brainnode-01 (192.168.71.222) — shogun-core runs here as Python/systemd (no Docker). Application tier. Confirmed 2026-03-12.
- **Node (platform):** svcnode-01 (192.168.71.220) — platform services only (gateways, Valkey, Traefik). Shogun consumes these via FQDN.
- **Node (db):** dbnode-01 (192.168.71.221) — shogun_v1 database — persona: dba-agent

---

## Platform Services Consumed

Check `../platform/.claude/services/_index.md` before building anything new.

| Service | FQDN | Used for |
|:--------|:-----|:---------|
| Telegram Gateway | telegram.platform.ibbytech.com | Event ingress, bot interface |
| Google Places Gateway | places.platform.ibbytech.com | Place discovery, neighborhood anchors |
| LLM Gateway | llm.platform.ibbytech.com | Chat completions, intent detection (Gemini 2.0 Flash) |
| Scraper | scrape.platform.ibbytech.com | Web content extraction via Firecrawl |
| Reddit Gateway | reddit.platform.ibbytech.com | Available if Shogun needs Reddit data |
| Valkey | valkey.platform.ibbytech.com:6379 | Conversation context, session state (24h TTL) |
| Tavily | tavily.platform.ibbytech.com | Web search (kanji + English), Tabelog domain search. TAVILY_API_KEY required. |

---

## Database Routing

- **Primary database:** shogun_v1 on dbnode-01
- **Schema:** public (Shogun owns this schema entirely)
- **App user:** [to be confirmed at first DB task — check shogun_v1 role grants]
- **Google Places data:** DO NOT write to shogun_v1. Read via Google Places REST
  gateway. `platform_v1.places` is canonical — resolved 2026-03-12.

---

## Known Infrastructure State — Last Verified 2026-03-12

- **svcnode-01 Shogun checkout:** Merged to develop 2026-03-12. svcnode-01 updated to develop branch.
- **DNS Infrastructure:** All 3 nodes confirmed pointing at Pi-hole. valkey.platform.ibbytech.com resolves on all nodes. Confirmed 2026-03-12.
- **Valkey:** Deployed and validated 2026-03-12. 6/6 checks passing.
- **shogun_v1 database:** Active. places schema DROPPED 2026-03-12.
  All place data now via platform_v1.places through REST gateway.
- **mcp_shogun / mcp_group:** Dormant. MCP deployment deferred.
  Do not modify without approved MCP architecture task plan.

---

## Open Architecture Decisions

- **Deploy branch resolution:** Merged to `develop` 2026-03-12. develop → main
  promotion pending explicit instruction. svcnode-01 node checkout needs updating
  after push — switch to develop or main on the node before next deployment.
- **Conversation context TTL:** ✅ 24h idle TTL confirmed 2026-03-12.
- **User profile storage:** ✅ Dietary, likes, dislikes → shogun_v1 DB (trip-long constants). Schema design pending for shogun-core build.
- **Location trigger threshold:** ✅ 150m + 5-minute cooldown confirmed 2026-03-12.
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
| Python / FastAPI | shogun-core application service on brainnode-01 (systemd, no Docker) | Platform standard; async-capable | 2026-03-10 |
| Gemini 2.0 Flash | LLM completions, intent detection, vision, voice transcription | Multimodal — handles text, images, audio natively | 2026-03-09 |
| Valkey 8.x | Conversation context per user (24h idle TTL) | Deployed 2026-03-12 | 2026-03-12 |
| PostgreSQL 17 / shogun_v1 | User profiles, itinerary, trip POIs | Platform standard | 2026-02-15 |
| Telegram bot | User interface — text, voice, photo, location | Low-friction family interface | 2026-03-09 |
| Tavily | Web search platform service — kanji + English, domain-restricted for Tabelog | Standard API key (not MCP). Env var: TAVILY_API_KEY | 2026-03-12 |
| Direct REST calls | Platform service consumption | MCP deferred post-trip. No MCP until post-MVP. | 2026-03-09 |

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
