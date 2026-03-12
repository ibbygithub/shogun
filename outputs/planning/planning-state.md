# Planning State — Shogun
Last updated: 2026-03-12

## Project Summary

Shogun is a single-user AI concierge delivered via Telegram. It responds to
live location updates and text commands with location-aware recommendations
(food, nearby places) and conversational AI responses. It is also the reference
consumer application for the IbbyTech platform — every capability Shogun needs
is first evaluated as a candidate platform service before being built app-local.
Platform owns infrastructure; Shogun owns application logic.

## Active Work

| Item | Description | Phase | Status | Last Updated |
|------|-------------|-------|--------|--------------|
| Claude Code foundation setup | .claude/CLAUDE.md, settings.json, foundation link established | Bootstrap | Complete | 2026-03-12 |
| DNS Infrastructure | Configure nodes to use Pi-hole DNS + set FQDNs on all 3 nodes | Pre-MVP 3 | svcnode-01 done. dbnode-01/brainnode-01 owner-managed | 2026-03-10 |
| Valkey (Redis) | Add as shared platform service in platform repo | Platform Track 1 | Ready | 2026-03-10 |
| shogun-core | Telegram control plane — movement logic, intent detection, LLM orchestration | MVP 3 | Pending Valkey | 2026-03-10 |

## Open Decisions

- **Valkey deployment:** Confirmed as shared platform service on svcnode-01. Awaiting DNS completion.
- **shogun-core FQDN:** Will be `svcnode-01.ibbytech.com:8082` for internal access. Public FQDN (`shogun.ibbytech.com`) deferred until Cloudflare phase.
- **Conversation context TTL:** Suggested 24h idle TTL. Pending confirmation.
- **Location trigger threshold:** 150m + 5-minute cooldown (revised from 100m to account for GPS drift). Pending confirmation.
- **LLM model:** Gemini 2.0 Flash confirmed.
- **Postgres for shogun-core:** Valkey sufficient for MVP. Postgres conversation persistence is backlog.

## DNS Infrastructure — Decision

- **DNS manager on lab nodes:** systemd-resolved (confirmed active, /etc/resolv.conf is symlink)
- **Current DNS:** 192.168.68.1 (router) → public DNS. Pi-holes (192.168.71.110, .115) NOT in use on lab nodes.
- **Namecheap A records:** Point to private IPs (192.168.71.220). Resolution works today via public DNS chain.
- **Decision:** Point all lab nodes at Pi-hole for DNS. Add local DNS records in Pi-hole for node FQDNs. Do NOT add node FQDNs to Namecheap (private IPs don't belong in public DNS).
- **Node FQDNs to set:**
  - svcnode-01 → 192.168.71.220
  - dbnode-01 → 192.168.71.221
  - brainnode-01 → 192.168.71.222
- **Procedure:** Edit `/etc/systemd/resolved.conf` on each node (requires root). Awaiting `cat /etc/systemd/resolved.conf` + `resolvectl status` output from svcnode-01 before issuing exact commands.

## Technology Registry

| Technology | Role in this project | Rationale | Date |
|------------|----------------------|-----------|------|
| Python / FastAPI | shogun-core application service | Consistent with platform services; async-capable | 2026-03-10 |
| Valkey 8.x | Shared platform cache / session store | Apache 2.0, Redis-protocol-compatible, Linux Foundation governed. Redis license changed to SSPL in 7.4+; Valkey is the enterprise-appropriate fork. | 2026-03-10 |
| PostgreSQL 17 | Persistent place storage | Already in use via platform (dbnode-01). places schema exists. | 2026-03-10 |
| Telegram Gateway (platform) | Event ingress | Platform service at telegram.platform.ibbytech.com | 2026-03-10 |
| Places Gateway (platform) | Place discovery | Platform service at places.platform.ibbytech.com | 2026-03-10 |
| LLM Gateway (platform) | Chat + intent detection | Platform service at llm.platform.ibbytech.com | 2026-03-10 |

## Decision Log

### Google Places routing — 2026-03-12
- Capability need: Canonical home for Google Places data
- Decision: `platform_v1.places` is canonical. Shogun does NOT write place data
  to shogun_v1. Reads via Google Places REST gateway only.
- `shogun_v1.places` schema dropped 2026-03-12.
- Tables: `google_places`, `google_place_snapshots`, `neighborhood_anchors` — all in platform_v1.
- Risk accepted: None — Shogun was already using the gateway; no data lost (test data only).

### Platform-services removal — 2026-03-10
- Capability need: Clarify what Shogun owns vs. what platform owns
- Options considered: Keep copies in shogun repo; remove and rely on platform
- Decision: Remove platform-services/ from shogun repo entirely
- Reasoning: llm-gateway, places-google, and telegram-ingress are all deployed
  from the platform repo. Shogun copies were older, diverged versions. Platform
  is the source of truth.
- Risk accepted: None — platform services are confirmed running.

### Shogun as reference consumer — 2026-03-10
- Capability need: Architectural principle for what goes in platform vs. shogun
- Decision: Every time Shogun needs a capability, evaluate it as a platform
  service first. Shogun is client one; future apps follow.
- Reasoning: Prevents app-level sprawl; builds platform capability incrementally
  from real use cases rather than speculation.
- Risk accepted: Slight overhead on each new capability decision. Acceptable.

### Valkey over Redis — 2026-03-10
- Capability need: Fast shared session/state store for shogun-core and future platform consumers
- Options considered: Redis 7.2 (BSD), Redis 7.4+ (SSPL), Valkey 8.x (Apache 2.0), Redis Stack, Memcached
- Decision: Valkey 8.x as a shared platform service
- Reasoning: Protocol- and client-identical to Redis. Apache 2.0 licensing is
  enterprise-appropriate for a long-term platform. Linux Foundation governance
  (AWS, Google, Oracle backing) makes it the more durable choice. No migration
  cost — same client libraries, same wire protocol.
- Risk accepted: Slightly less name recognition than Redis operationally.
  No technical risk.

### Processing model — 2026-03-10
- Decision: Inline (synchronous) processing for MVP
- Reasoning: Single-user. Queue infrastructure adds operational complexity with
  no benefit at this scale.
- Risk accepted: If processing takes too long, Telegram gateway will timeout
  waiting for reply_text. Must ensure LLM calls complete within ~25s.

### Trigger model — 2026-03-10
- Decision: Combined — live location radius threshold + text commands
- Reasoning: Location updates drive automatic recommendations; text commands
  enable explicit requests and conversation.

### LLM role — 2026-03-10
- Decision: Intent detection + conversation (not just summarization)
- Reasoning: Allows text commands to be natural language rather than rigid
  slash-command syntax. Enables Shogun to feel like a concierge rather than
  a query tool.

## Backlog

- **OSM Places service:** Platform has no OSM gateway. Shogun had an empty placeholder.
  Deferred until Google Places coverage proves insufficient.
- **Queue layer:** If single-user inline proves too slow (LLM timeout), revisit
  with a lightweight queue. Candidate: Valkey pub/sub (already in platform).
  Do not add complexity preemptively.
- **Conversation persistence to Postgres:** Valkey conversation context is
  ephemeral (TTL-based). If permanent history is needed, add a shogun schema
  in Postgres. Deferred to post-MVP.
- **shogun-core FQDN:** Needs confirmation before Telegram gateway is pointed at it.
- **Multi-region / multi-city Shogun:** Currently Japan-only seeds. Broadening
  scope is post-MVP.

## Planning Documents

| Document | Path | Status |
|----------|------|--------|
| Shogun Reboot Plan | outputs/planning/shogun-reboot-plan.md | Draft |
| Risk Register | outputs/planning/shogun-risks.md | Draft |
