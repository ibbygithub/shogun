# Plan: Shogun Reboot — MVP 3
Date: 2026-03-10
Status: Draft

## Objective

Build shogun-core: the Telegram control plane that makes Shogun functional as
an AI concierge. Also establish Valkey as a shared platform service that
shogun-core (and future applications) consume for session and state management.

This completes the Shogun MVP — a single user can send live location updates
via Telegram and receive AI-generated, location-aware recommendations.

## Scope

**Included:**
- Valkey 8.x as a new platform service (platform repo)
- shogun-core FastAPI service (shogun repo, app-services/)
- Movement detection logic (distance delta, radius threshold)
- Combined trigger model (location radius + text commands)
- Intent detection via LLM gateway
- Place lookup via places gateway
- Conversational response via LLM gateway
- Session and conversation state in Valkey
- Telegram gateway pointed at shogun-core as UPSTREAM_URL

**Explicitly excluded:**
- Queue layer (inline processing only for MVP)
- Conversation persistence to Postgres (Valkey TTL is sufficient for MVP)
- Multi-user support
- Personal preference learning
- OSM places fallback
- Public HTTPS exposure (internal LAN for MVP, Cloudflare later)

## Current State

| Component | State |
|-----------|-------|
| telegram.platform.ibbytech.com | Running — needs UPSTREAM_URL set to shogun-core |
| places.platform.ibbytech.com | Running — shogun-core will call this |
| llm.platform.ibbytech.com | Running — shogun-core will call this |
| shogun-places-ingester | Running (or deployable) — populates Postgres places data |
| Valkey | Does not exist — Track 1 prerequisite |
| shogun-core | Does not exist — Track 2 |
| Postgres places schema | Exists on dbnode-01 — shogun-core reads from it |

## Architecture

```
[User] → Telegram → telegram.platform.ibbytech.com
                            │
                    POST / (event envelope)
                            │
                            ▼
                    shogun-core (svcnode-01, FastAPI)
                            │
              ┌─────────────┴──────────────────┐
              │                                │
        kind: location                   kind: text
              │                                │
     Check Valkey (last pos)         Load convo context (Valkey)
     Compute distance delta                    │
     If > threshold:                  LLM: intent detection
              │                                │
              └──────────┬─────────────────────┘
                         │
              ┌──────────▼──────────┐
              │                     │
        nearby_search           question / chat
              │                     │
   places.platform...        llm.platform...
              │                     │
              └──────────┬──────────┘
                         │
                LLM: format response
                         │
              Store state in Valkey
                         │
              { "reply_text": "..." }
                         │
              ← telegram gateway → User
```

## Valkey Key Schema (Shogun namespace)

```
shogun:user:{user_id}:location      TTL: 7 days
  { lat, lng, timestamp, accuracy }

shogun:user:{user_id}:last_trigger  TTL: 7 days
  timestamp (ISO) of last recommendation sent

shogun:user:{user_id}:session       TTL: 7 days
  { city, country, inferred from last geocode }

shogun:user:{user_id}:conversation  TTL: 24h (rolling on each message)
  List (capped at N messages) of { role, content, timestamp }
```

## Phases

---

### Phase 1: Valkey Platform Service
**Goal:** Valkey running on svcnode-01, reachable by platform_net consumers via REDIS_URL
**Entry criteria:** platform repo access; svcnode-01 devops-agent access
**Deliverables:**
- `platform/services/valkey/docker-compose.yml`
- `platform/services/valkey/.env.example`
- `platform/services/valkey/README.md`
- Valkey container running on platform_net (NOT exposed via Traefik)
- Health confirmed: `redis-cli -a <pass> ping` returns PONG
- platform README updated with Valkey entry
**Exit criteria:** Any service on platform_net can connect via `redis://:pass@platform-valkey:6379`
**Complexity:** Low
**Dependencies:** svcnode-01 running, platform_net exists (Traefik up)

---

### Phase 2: shogun-core Scaffold
**Goal:** FastAPI service running, reachable from Telegram gateway, returns static reply
**Entry criteria:** Phase 1 complete; shogun-core FQDN confirmed
**Deliverables:**
- `shogun/app-services/shogun-core/app.py` (FastAPI skeleton)
- `shogun/app-services/shogun-core/Dockerfile`
- `shogun/app-services/shogun-core/docker-compose.yml`
- `shogun/app-services/shogun-core/requirements.txt`
- `shogun/app-services/shogun-core/.env.example`
- `/health` endpoint live
- `/` POST endpoint accepting Telegram event envelope, returning `{}`
- Telegram gateway UPSTREAM_URL pointed at shogun-core
**Exit criteria:** Send a Telegram message → shogun-core receives it → logs show the envelope → no crash
**Complexity:** Low
**Dependencies:** Phase 1; Valkey REDIS_URL available; FQDN decision

---

### Phase 3: Location + State Layer
**Goal:** shogun-core tracks position, detects movement, throttles recommendations
**Entry criteria:** Phase 2 complete
**Deliverables:**
- Valkey connection layer (connection pooling, error handling)
- Location state read/write (last position, last trigger timestamp)
- Distance calculation (Haversine)
- Threshold logic: if delta > threshold AND time since last trigger > cooldown → flag as triggered
- No place lookup yet — just log "TRIGGER" or "NO_TRIGGER" per update
**Exit criteria:** Walk test — move location → logs show TRIGGER. Stay still → NO_TRIGGER.
**Complexity:** Medium
**Dependencies:** Phase 2

---

### Phase 4: Place Discovery + Response
**Goal:** On trigger, fetch nearby places and send a formatted reply to user
**Entry criteria:** Phase 3 complete; places data in Postgres (shogun-places-ingester has run)
**Deliverables:**
- places gateway client (text search or nearby based on session context)
- Basic response formatter (list of top N places, name + address + rating)
- LLM call to format the raw places list into a natural Telegram message
- Reply returned to Telegram gateway as `{ "reply_text": "..." }`
**Exit criteria:** Walk test → recommendation message appears in Telegram with real place data
**Complexity:** Medium
**Dependencies:** Phase 3; places data seeded in Postgres

---

### Phase 5: Text Commands + Intent Detection
**Goal:** Text messages handled by LLM intent detection; conversational flow works
**Entry criteria:** Phase 4 complete
**Deliverables:**
- Conversation context read/write in Valkey
- LLM intent detection call (system prompt defines intents: nearby_search, question, status, unknown)
- Intent routing:
  - `nearby_search` → same place discovery + response path as Phase 4
  - `question` → conversational LLM response using context
  - `status` → system status reply (last location, last trigger time)
  - `unknown` → clarifying reply
- Conversation context updated after every exchange
**Exit criteria:** Send "find me ramen" → gets place results. Send "what time is it in Tokyo?" → gets conversational answer.
**Complexity:** High
**Dependencies:** Phase 4; LLM gateway tested for intent detection

---

## Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| Valkey on svcnode-01 | Platform track | Pending |
| Telegram gateway UPSTREAM_URL update | Platform config | Pending Phase 2 |
| shogun-core FQDN | Decision pending | Open |
| places data in Postgres | shogun-places-ingester | Deployable |
| Location trigger threshold (meters) | Decision pending | Open |
| Conversation TTL | Decision pending | Suggested: 24h |

## Risks

See `outputs/planning/shogun-risks.md`

## Open Items

- Confirm shogun-core FQDN (suggest: internal only for MVP, no Traefik exposure,
  Telegram gateway reaches it via Docker network or LAN IP)
- Confirm location trigger threshold (suggested: 150m to avoid noise from GPS drift)
- Confirm conversation context TTL (suggested: 24h idle)
- Confirm LLM model for intent detection (suggested: Gemini 2.0 Flash — fast, low cost)

## Out of Scope

- Queue layer — revisit if inline proves too slow
- Conversation persistence to Postgres — post-MVP
- Multi-user — post-MVP
- Cloudflare / public exposure — post-MVP
- OSM places fallback — post-MVP
