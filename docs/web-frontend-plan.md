# Shogun Web Frontend — Advance Planning Document

**Status:** Planning only — no code. This document captures architecture decisions, technology choices, phased scope, and open questions for the web frontend initiative.

**Date:** 2026-03-10
**Branch:** `claude/plan-web-frontend-Yh68u`

---

## 1. Why a Web Frontend?

Shogun currently uses Telegram as its only user interface. Telegram is excellent for mobile/push interactions but has hard limits:

- No custom visualization (maps, tables, grids)
- No admin or operational view (service health, data browser)
- No keyboard-heavy workflows (seed config, bulk operations)
- No way to onboard users without a Telegram account
- No shareable URLs or bookmarkable state

A web frontend unlocks:

1. **Ops/admin panel** — real-time health of all platform services
2. **Places data browser** — explore ingested Google Places data with a map
3. **Chat interface** — browser-based alternative to Telegram for the AI concierge
4. **Configuration UI** — manage seeds, neighborhoods, enrichment settings
5. **Foundation for future apps** — shared design system and component library

---

## 2. User Personas

| Persona | Primary Goal | Key Workflows |
|---|---|---|
| **Operator (you, MVP)** | Keep the system healthy and fed with good data | Health dashboard, seed ingestion, places browser, log tail |
| **Traveler/End User** | Get local recommendations, track a trip | Chat, map view, saved places |
| **Developer (future)** | Extend Shogun or build a new app on the platform | API explorer, component library docs |

The MVP web frontend serves the **Operator** persona only. End-user and developer personas are future phases.

---

## 3. Capability Inventory

### Phase 1 — Ops Dashboard (Operator MVP)

Immediate value, no end-user exposure needed.

- **Service Health Board** — live `/health` polling for all platform services (LLM Gateway, Places Service, Telegram Gateway). Show: status, last check time, provider key presence, DB connectivity.
- **Places Browser** — table + map view of `places.google_places`. Filterable by city, neighborhood, category, rating. Linked to neighborhood anchors.
- **Seed Ingestion Trigger** — UI to fire `POST /v1/ingest/seeds` and watch live stats stream back.
- **Neighborhood Anchor Map** — visualize resolved anchors as pins on a map.

### Phase 2 — Chat Interface

Browser-based AI concierge chat as an alternative to Telegram.

- WebSocket or SSE connection to Shogun Core
- Message history (stored in Postgres or browser local storage)
- Context display (current location if user grants it, active neighborhoods)
- Streaming token output from LLM

### Phase 3 — Configuration UI

Reduce need to hand-edit JSON files.

- Seed file editor (add/edit neighborhoods, categories)
- Neighborhood anchor resolution preview (show geocoded result before committing)
- Enrichment settings (radius, top_n per category)

### Phase 4 — End User Trip Planner (Future App Pattern)

This transitions from internal ops to a product surface. Useful for validating the "future apps" design pattern:

- Trip planning (select city, dates, interests)
- Day-by-day itinerary view
- Map with recommended stops
- Share/export

---

## 4. Architecture

### 4.1 Overall Shape

```
Browser (Next.js SPA/SSR)
    │
    │  HTTPS (Traefik)
    ▼
Web API / BFF Service          ← NEW: thin Node.js/Express or Next.js API routes
    │
    ├── LLM Gateway Service    (POST /v1/chat, POST /v1/embeddings)
    ├── Places Google Service  (GET/POST places endpoints)
    ├── Telegram Ingress       (health, future: relay events)
    └── Shogun Core            (future: domain logic, chat sessions)
```

The BFF (Backend for Frontend) is a lightweight service that:
- Aggregates data from multiple backend services
- Handles auth / session validation
- Exposes clean, frontend-optimized endpoints (no raw DB access from the browser)
- Manages WebSocket connections for real-time chat

### 4.2 New Services Required

| Service | Role | Notes |
|---|---|---|
| `web-frontend` | Static/SSR Next.js app | Served via Traefik |
| `web-api` (BFF) | Backend for frontend | Aggregates platform services; handles auth |

Both deploy as Docker containers on the existing Docker Compose / Traefik stack.

### 4.3 Auth Strategy

**MVP (single operator):** HTTP Basic auth or a shared API token (header-based). Simple, no user database required. Traefik BasicAuth middleware is already available.

**Future (multi-user):** JWT-based session auth. User table in Postgres. OAuth2 (Google) as provider. Keep this out of scope for Phase 1.

### 4.4 Real-Time Strategy

| Feature | Mechanism | Rationale |
|---|---|---|
| Service health polling | Short-polling (5s interval) | Simple; health endpoints are cheap |
| Chat message streaming | Server-Sent Events (SSE) | Unidirectional, works through Traefik, no WS upgrade needed |
| Seed ingestion progress | SSE | Same as chat streaming |
| Live location updates | WebSocket (future) | Bidirectional; deferred to Phase 3+ |

---

## 5. Technology Choices

### 5.1 Frontend Framework

**Choice: Next.js 15 (App Router)**

Rationale:
- TypeScript-first from day one
- File-based routing; easy to grow
- App Router supports React Server Components for zero-JS data fetching pages (places browser, dashboard)
- API Routes (`/api/*`) can serve as a lightweight BFF, eliminating the need for a separate BFF container in Phase 1
- Strong ecosystem; works well with all candidate UI libraries
- SSR reduces TTFB for map/places pages without a SPA shell

Alternative considered: **Vite + React SPA**. Simpler for pure SPA. Rejected because SSR/RSC is valuable for places data (large tables, map initial load) and the project will likely need server-side logic anyway.

### 5.2 Styling

**Choice: Tailwind CSS v4**

Rationale:
- Utility-first keeps CSS co-located with components
- Consistent with most modern Next.js projects; best tooling support
- Easy to extract a design token set for future shared component library

### 5.3 Component Library

**Choice: shadcn/ui**

Rationale:
- Copy-into-repo model — components are owned, not black-boxed
- Built on Radix UI primitives (accessible, headless)
- Works natively with Tailwind
- Easy to theme for future apps with different brand colors

Alternative considered: Mantine, Ant Design. Rejected: heavier, more opinionated styles harder to adapt across future apps.

### 5.4 Map Rendering

**Choice: MapLibre GL JS (with react-map-gl wrapper)**

Rationale:
- Open-source (BSD), no per-tile API key or usage billing for the map renderer itself
- Can use free tile sources (OpenFreeMap, Protomaps) for the base layer
- Google Places data is displayed *on* the map but map tiles don't need to be Google's
- Alternative: Google Maps JS API — has tighter integration with Places data but adds billing complexity for map tiles and is proprietary

Decision point: If Google Maps tile styling is essential, switch to Google Maps JS API. Otherwise MapLibre + OpenFreeMap tiles is the default choice.

### 5.5 Server State / Data Fetching

**Choice: TanStack Query (React Query v5)**

Rationale:
- Handles caching, background refetch, stale-while-revalidate
- Works seamlessly with Next.js App Router
- Polling intervals for health checks are first-class features
- Integrates well with SSE hooks for streaming

### 5.6 Client State

**Choice: Zustand**

Rationale:
- Minimal boilerplate; single store file for MVP
- Works with React Server Components model (client store only for true client state)
- Scales to complex state if needed

### 5.7 Testing

| Layer | Tool |
|---|---|
| Unit / component | Vitest + React Testing Library |
| E2E | Playwright |
| API mocking | MSW (Mock Service Worker) |

---

## 6. Future Apps — Monorepo Strategy

The goal is to share UI components, types, and design tokens across Shogun's web frontend and any future apps (trip planner, admin tools, partner portal, etc.).

### 6.1 Structure

```
/apps
  /shogun-web          ← Main Shogun ops + user interface
  /trip-planner        ← Future standalone app
/packages
  /ui                  ← Shared component library (shadcn/ui base)
  /types               ← Shared TypeScript types/contracts
  /config              ← Shared ESLint, Prettier, Tailwind config
  /api-client          ← Generated or hand-written SDK for platform APIs
```

### 6.2 Tooling

**Choice: pnpm workspaces + Turborepo**

Rationale:
- pnpm workspaces: efficient disk usage (hard links), fast installs
- Turborepo: incremental builds, task pipelines (build → test → deploy only changed packages)
- Widely adopted for this pattern; good Next.js integration

Alternative: Nx. More powerful but heavier setup. Defer unless the project grows to 5+ apps.

### 6.3 Design System Token Set

Define at the `packages/config` level:
- Color palette (primary, surface, muted, destructive, success)
- Typography scale
- Spacing scale
- Border radius, shadows
- Dark mode variants

Each app can override tokens. The `shogun-web` app uses a "clean, functional" aesthetic (not consumer-facing; no marketing gloss needed). Future consumer apps can apply a branded theme.

---

## 7. Infrastructure Integration

### 7.1 Docker Compose Placement

New compose file: `platform-services/web-frontend-service/docker-compose.yml`

Follows the same pattern as existing services:
- Traefik labels for domain routing
- Connected to `platform_net`
- `.env` for secrets (API token for BFF auth, etc.)

### 7.2 Domain Routing (Traefik)

| Service | Proposed Domain |
|---|---|
| Web Frontend | `app.platform.ibbytech.com` |
| Web API (BFF) | `api.platform.ibbytech.com` |

Traefik already handles TLS termination for other services; same pattern applies.

### 7.3 Auth at the Edge (MVP)

For the operator MVP, Traefik BasicAuth middleware is sufficient. The BFF doesn't need to implement auth logic — Traefik handles it before requests reach the container.

---

## 8. API Contracts Needed from Backend

The BFF needs to expose these to the frontend. Backend services either already have these or need them added:

### Already Exists

- `GET /health` — LLM Gateway, Places Service (both exist)
- `POST /v1/ingest/seeds` — Places Service (exists)

### Needs to Be Added to Places Service

- `GET /v1/places` — list with filters (city, neighborhood, type, rating range), pagination
- `GET /v1/places/:place_id` — single place detail
- `GET /v1/neighborhoods` — list resolved anchors
- `GET /v1/ingest/status` — last ingestion run stats (avoid re-triggering to check results)

### New BFF Endpoints (aggregate)

- `GET /api/health` — aggregated health across all services
- `GET /api/places` — proxied + enriched places list
- `GET /api/neighborhoods` — proxied neighborhoods + anchors
- `POST /api/ingest` — triggers seed ingestion, streams SSE progress
- `POST /api/chat` — sends message to Shogun Core, streams SSE response (Phase 2)

---

## 9. Key Open Questions

| # | Question | Impact | Recommendation |
|---|---|---|---|
| 1 | Does the BFF live in Next.js API routes or as a separate Node.js container? | Phase 1 scope + Docker complexity | **Start with Next.js API routes.** Extract to separate container if the BFF logic grows or needs independent scaling. |
| 2 | MapLibre + OpenFreeMap vs Google Maps JS API? | Tile billing, styling effort | **Default MapLibre.** Revisit if Google Maps visual fidelity is required. |
| 3 | Is Phase 1 purely operator-internal (no public URL)? | Auth complexity | **Yes, LAN-only for Phase 1**, same as other services. BasicAuth via Traefik. |
| 4 | When does the monorepo split happen? | Repo restructure effort | **Start with a single `/web` directory in the shogun repo.** Move to a true monorepo when the second app is actively being built. |
| 5 | Does the chat interface bypass Telegram entirely, or relay through it? | Architecture complexity | **Phase 2 decision.** Relay through Telegram keeps a single conversation history. Native chat bypasses Telegram but requires Shogun Core to support multiple input channels. |
| 6 | Should places data be served directly from a BFF query to Postgres, or strictly through the Places Service API? | Backend coupling | **Always through the Places Service API.** Avoids direct DB coupling from the BFF. Places Service adds read endpoints to support this. |

---

## 10. Phased Delivery Summary

| Phase | Deliverable | Prerequisites | Key Decision |
|---|---|---|---|
| **1** | Ops dashboard: health, places browser, ingest trigger | Places Service read endpoints, BFF scaffold | BFF in Next.js API routes vs standalone |
| **2** | Chat interface (web alternative to Telegram) | Shogun Core with HTTP/WS interface | Relay via Telegram vs native channel |
| **3** | Config UI (seed editor, anchor preview) | Places Service write endpoints | UX for JSON-heavy seed format |
| **4** | End-user trip planner (first "future app") | Monorepo setup, shared UI package | Monorepo tooling finalized |

---

## 11. What This Plan Does NOT Include

- Any code, scaffolding, or file generation (this is a planning document)
- Decisions on Shogun Core architecture (separate concern)
- Multi-user auth system (deferred post-Phase 1)
- Mobile app or PWA (not planned)
- Analytics or telemetry (not planned for MVP)

---

## 12. Next Steps (When Ready to Build)

1. Confirm answers to open questions in Section 9, especially #1 (BFF location) and #2 (map tiles)
2. Add read endpoints to Places Service (`GET /v1/places`, `GET /v1/neighborhoods`)
3. Scaffold Next.js app in `platform-services/web-frontend-service/`
4. Implement Phase 1 ops dashboard
5. Revisit and update this document before starting Phase 2
