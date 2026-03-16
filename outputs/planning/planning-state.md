# Planning State — Shogun
Last updated: 2026-03-15

## Project Summary

Shogun is an AI travel concierge for the Ibbotson Japan trip (Mar 23–Apr 9).
Delivered via Telegram (shogun-core) and a web frontend (shogun-web).
The Telegram bot handles live location-aware recommendations; the web app gives
Brenda an itinerary editing surface and all three travelers a unified trip view.

**Current infrastructure: all 10 services running on Docker Desktop (Windows laptop).**
Laptop stays home in California unattended during the trip (Mar 23–Apr 9).
Public access via Cloudflare Tunnel → shogun.ibbytech.com (in progress — see blockers).
Startup/shutdown: `scripts/start-shogun.ps1` / `scripts/stop-shogun.ps1`

## Infrastructure — Current State (2026-03-15)

All 10 containers validated on Docker Desktop. Both repos pushed to GitHub (develop + master/main).

| Container | Status | Notes |
|-----------|--------|-------|
| platform-postgres | healthy | Named volume platform-postgres-data |
| platform-valkey | running | 127.0.0.1:6379 (localhost only) |
| platform-llm-gateway | running | Gemini 2.0 Flash |
| platform-telegram-gateway | running | Polling mode, no public URL needed |
| platform-places-google | running | Pulls image (harmless warning on build) |
| platform-tavily | running | |
| platform-scraper-api | running | |
| shogun-core | running | Containerized 2026-03-15 (was systemd on brainnode-01) |
| shogun-web-api | running | SHOGUN_BYPASS_AUTH=true (Cloudflare handles auth) |
| shogun-web-ui | running | http://localhost:3010 |

**Not running (intentional):** platform-reddit-gateway (DB setup needed first — Phase 1 below)
**Traefik:** Disabled. Will NOT be restored pre-trip. Cloudflare Tunnel proxies directly to shogun-web-ui:3000.

## RECOVERY COMPLETE — 2026-03-15
✅ All 10 containers running and validated
✅ Telegram bot live (polling mode)
✅ LLM pipeline working (Gemini 2.0 Flash via llm-gateway)
✅ Location trigger logic validated
✅ Web UI loading at localhost:3010
✅ Web AI chat working
✅ Database schema applied, Todd seeded (11 itinerary legs, 30 POIs, 8 preferences)
✅ Start/stop scripts with directory preservation
✅ Both repos committed and pushed (develop + master/main)

## Active Work — Pre-Trip (Departure Mar 23, 8 days)

| Item | Description | Phase | Status | Last Updated |
|------|-------------|-------|--------|--------------|
| Cloudflare Tunnel + Access | Public access to shogun.ibbytech.com from Japan. cloudflared container → web-ui. Google IdP auth. | Public Access | Blocked: Todd DNS + GCP | 2026-03-15 |
| Reddit Gateway | DB setup (pgvector, reddit schema, reddit_app user), .env Docker Desktop fixes, add to start script | Platform Phase 1 | Not started | 2026-03-15 |
| shogun-places-ingester | Add docker-compose.yml, wire up to platform_net, one-shot run for Osaka/Nara/Kanazawa/Tokyo neighborhoods | Platform Phase 2 | Not started | 2026-03-15 |
| Japan Knowledge Data Lake | New table knowledge_items in shogun_v1. Ingest pipeline: Tavily (Tabelog), Scraper, Reddit, Practical. | Data Lake Phase 3 | Not started | 2026-03-15 |
| RAG pipeline update | shogun-core to query knowledge_items alongside trip_pois for richer location responses | Data Lake Phase 3 | Not started | 2026-03-15 |
| Laptop reliability (unattended) | Windows power settings, Docker Desktop auto-start, Windows Update mitigation | Ops | Not started | 2026-03-15 |
| Printable itinerary | Standalone bilingual HTML — full trip details | MVP 6 | Not started | 2026-03-15 |

## Cloudflare Tunnel Plan — Decision Log (2026-03-15)

### Architecture decision
- **Option chosen:** Cloudflare Tunnel + Access (Option C) — public access from Japan
- **Traefik:** NOT needed. cloudflared container proxies directly to `http://shogun-web-ui:3000`
- **Auth:** Cloudflare Access + Google IdP. App keeps `SHOGUN_BYPASS_AUTH=true` — Cloudflare is the auth wall.
- **Flow:** Phone in Japan → shogun.ibbytech.com → Cloudflare edge → Access auth → Tunnel → cloudflared → shogun-web-ui:3000

### What Todd must do first (browser work, no code)
1. **Move ibbytech.com DNS to Cloudflare nameservers** — change in Namecheap → Domain → Nameservers.
   Currently DNS is Namecheap-managed. Cloudflare Access REQUIRES the zone on Cloudflare DNS.
   Allow 24-48h propagation (usually faster). This is the longest lead-time item — do it first.
2. **Cloudflare Zero Trust** — dash.cloudflare.com → Zero Trust → enable free tier (up to 50 users)
   → Networks → Tunnels → Create tunnel → name it `shogun-laptop` → choose Docker connector → copy TUNNEL_TOKEN
   → Add public hostname: `shogun.ibbytech.com` → Service: `http://shogun-web-ui:3000`
3. **Google Cloud Console** — check https://console.cloud.google.com for existing project.
   Need OAuth 2.0 client ID + secret for Cloudflare Access Google IdP.
4. **Cloudflare Access Application** — attach Google IdP, set policy to allow specific Google emails.

### What Claude Code does after Todd has TUNNEL_TOKEN
- Add cloudflared Docker container to `platform/infra/compose/docker-compose.infra.yml`
- One env var: TUNNEL_TOKEN
- Add to start-shogun.ps1 (starts with infra layer)
- Test from phone

## Blockers (Cloudflare)

- **ibbytech.com DNS zone on Cloudflare:** ❌ Currently Namecheap-managed — Todd must move nameservers
- **Cloudflare Zero Trust enabled:** TBD — Todd
- **TUNNEL_TOKEN obtained:** TBD — Todd (from Zero Trust dashboard after creating tunnel)
- **Google Cloud OAuth client ID + secret:** TBD — Todd (check console.cloud.google.com for existing project)
- **Brenda and Madeline Google email addresses:** TBD — needed for Access policy
- **Brenda and Madeline Telegram IDs:** TBD — needed for seeding user profiles

## Laptop Unattended Risk (Mar 23–Apr 9)

| Risk | Mitigation |
|------|------------|
| Windows Update auto-restart | Set maintenance window to 3-5am, disable auto-restart |
| Docker Desktop not starting after reboot | Enable "Start Docker Desktop when you log in" + Windows auto-login |
| Laptop sleeps | Power settings: disable sleep on AC power, screen off is OK |
| Power outage | Nothing to do — acknowledge risk |

## Data Lake Plan — Phase 3 (post Reddit + places-ingester)

**New table:** `shogun_v1.public.knowledge_items` (city, topic, source_url, content_summary, raw_content, ingested_utc)

**Ingest sources:**
| Layer | Tool | Content |
|-------|------|---------|
| Google Places depth | shogun-places-ingester | Osaka Tenjinbashi, Nara center, Kanazawa Higashi Chaya, Tokyo Sugamo |
| Tabelog restaurant data | Tavily (domain:tabelog.com) + Scraper | Top restaurants near each accommodation |
| Reddit intel | Reddit gateway | r/JapanTravel, r/osaka, r/Tokyo — last 90 days |
| Practical travel | Tavily (EN+JP) | IC card, 2026 sakura forecast by city, pharmacy kanji |

**Ingest script:** `shogun-core/tools/ingest_knowledge.py --city osaka` (re-runnable, one-shot)
**Final re-run:** Mar 22 (day before departure) for latest sakura forecasts + Reddit intel

## Trip Itinerary Reference

| Leg | Date | City | Title |
|-----|------|------|-------|
| 1-2 | Mar 23 | SFO→LAX→KIX | Flights — arrive Osaka area |
| 3 | Mar 24 | Osaka | Tenjinbashi Queen Airbnb — check in |
| 4 | Mar 25 | Nara | Day trip — deer park, Todai-ji, Kasugataisha |
| 5 | Mar 26 | Osaka | Universal Studios Japan — Nintendo World |
| 6 | Mar 30 | Osaka→Kanazawa | Transit |
| 7 | Mar 30 | Kanazawa | Hotel Sanraku Kanazawa |
| 8 | Apr 1 | Kanazawa→Tokyo | Transit |
| 9 | Apr 1 | Tokyo | Sugamo Airbnb (Toshima-ku) |
| 10 | Apr 3 | Tokyo | Ghibli Museum — Mitaka (TIMED ENTRY NOON) |
| 11 | Apr 9 | Tokyo→SFO | JL2 HND → SFO |

POIs seeded: 30 total — osaka(6), tokyo(10), nara(4), kanazawa(4), kyoto(5), sakai(1)

## Technology Registry

| Technology | Role in this project | Rationale | Date |
|------------|----------------------|-----------|------|
| Python / FastAPI | shogun-core + shogun-web-api | Consistent with platform services; async-capable | 2026-03-10 |
| Valkey 8.x | Conversation context per user (24h idle TTL) | Apache 2.0, Redis-protocol compatible | 2026-03-10 |
| PostgreSQL 17 | User profiles, itinerary, trip POIs, knowledge items | Platform standard | 2026-03-10 |
| Gemini 2.0 Flash | LLM completions, intent detection, vision, voice transcription | Multimodal | 2026-03-09 |
| Telegram bot | User interface — text, voice, photo, location | Polling mode — no public URL needed | 2026-03-09 |
| Next.js (React SSR) | shogun-web-ui frontend | SSR fast on mobile | 2026-03-13 |
| Cloudflare Access + Google IdP | Web authentication (edge-level) | Auth at edge; app never handles credentials | 2026-03-13 |
| Cloudflare Tunnel (cloudflared) | Public exposure of shogun.ibbytech.com — Docker container | No inbound ports; works with dynamic home IP; NO Traefik needed | 2026-03-15 |
| Open-Meteo | Weather data (free, no API key) | No rate limits; Valkey-cached 30min | 2026-03-13 |
| Tavily | Web search — kanji + English, Tabelog domain search | TAVILY_API_KEY required | 2026-03-12 |

## Decision Log

### Traefik — deferred permanently (pre-trip) — 2026-03-15
- Decision: Traefik will NOT be restored before the Japan trip
- Reasoning: Services communicate via container names on platform_net — no routing needed.
  Cloudflare Tunnel proxies directly to shogun-web-ui:3000 — Traefik adds no value here.
  Complexity/risk not justified with 8 days to departure.
- Re-evaluation: Restore when Proxmox lab is rebuilt post-trip (3-node separation).
  Compose config is already written — it's a re-enable, not a rewrite.

### Cloudflare Tunnel architecture — 2026-03-15
- Capability need: External access to shogun.ibbytech.com from Japan (phones, laptop)
- Options: (A) Traefik + mkcert internal only; (B) Traefik + LAN DNS; (C) Cloudflare Tunnel direct
- Decision: Option C — cloudflared container → shogun-web-ui:3000 directly
- No Traefik required. SHOGUN_BYPASS_AUTH stays true — Cloudflare Access is the auth layer.
- Risk: ibbytech.com DNS must move from Namecheap to Cloudflare. Allow 48h propagation.
- Risk: Laptop unattended for 17 days. Windows reliability mitigations required (see above).

### Laptop as production host — 2026-03-15
- Decision: Windows laptop stays home in California, running Docker Desktop, for Mar 23–Apr 9
- Reasoning: Fastest path. No VPS cost. cloudflared handles dynamic IP and reconnection.
- Risk accepted: Windows Update reboot could take down all services. Mitigation: maintenance window + auto-start config.
- Alternative considered: Hetzner CX22 VPS (~$4/mo). Deferred — user may switch before departure.

## Planning Documents

| Document | Path | Status |
|----------|------|--------|
| Migration Guide | outputs/planning/migration-guide.md | Complete |
| Disaster Recovery Checklist | outputs/planning/disaster-recovery-checklist.md | Complete |
| Shogun Web Plan | outputs/planning/shogun-web-plan.md | Approved |
| City Theme Specification | outputs/planning/shogun-web-city-themes.md | Approved |
| Coding Agent Execution Brief | outputs/planning/shogun-web-agent-brief.md | Approved |
| Risk Register | outputs/planning/shogun-risks.md | Draft |
