# Project Shogun — Canonical Index

**Status:** Active — updated post-reboot (2026-03-10)
**Purpose:** Single entry point for confirmed decisions and current repo structure.

---

## What This Index Is

This document is the *entry point* for Project Shogun's documentation.
It contains **only confirmed decisions** and reflects current repo state.

Chat remains exploratory. This index is canonical.

---

## Confirmed Decisions (Locked)

### Product Intent

- Shogun is an **AI concierge** focused on **location-aware, contextual responses**.
- MVP validates **movement-based updates** (radius logic) and **local discovery** (food / nearby info).
- MVP is **single-user**, **single primary use case**, production-oriented.

### Messaging & Platform

- Interface: **Telegram Bot**
- Transport: **Webhooks** (polling fallback for dev)
- Location input:
  - One-time location
  - **Live Location (preferred)**
- Shogun does **not** poll GPS.
- Update cadence is **client-controlled and variable** (seconds to ~1 minute).

### Privacy & Reality Constraints

- Shogun reacts only to **pushed events** from Telegram.
- Location accuracy and frequency are **not guaranteed**.
- System must tolerate missed or delayed updates.

### Architecture (Confirmed)

```
Telegram → telegram.platform.ibbytech.com → shogun-core (UPSTREAM_URL)
                                                   ↓
                                         Movement / radius logic
                                                   ↓
                              places.platform.ibbytech.com  (place discovery)
                                                   ↓
                                llm.platform.ibbytech.com   (LLM response)
                                                   ↓
                                         Reply text → Telegram
```

- Telegram events are received by **platform's telegram-gateway** and forwarded as structured JSON envelopes to `shogun-core`
- `shogun-core` is Shogun's control plane — it owns movement logic, orchestration, and state
- All external API calls go through **platform gateways**, never directly to vendors
- Work is **queued or handled inline** (TBD per load); no polling

### Infrastructure Model

- Platform (`c:\git\work\platform`) owns and deploys all shared gateway services
- Shogun (`c:\git\work\shogun`) owns only Shogun application services
- Shogun **consumes** platform services via HTTP; it does not host them
- Code moves between machines via **Git push/pull only**

### Platform Services Shogun Consumes

| Service | FQDN | Used For |
|:---|:---|:---|
| Telegram Gateway | `telegram.platform.ibbytech.com` | Receive Telegram events → forward to shogun-core |
| Places Google | `places.platform.ibbytech.com` | Geocode, nearby search, place details |
| LLM Gateway | `llm.platform.ibbytech.com` | Chat completions (Gemini/OpenAI/Anthropic) |
| Scraper | `scrape.platform.ibbytech.com` | Web scraping (future use) |

### Movement Model

- Movement is inferred by **distance delta** between location updates
- Radius-based triggers (~100 meters default)
- Logic must handle: irregular updates, no movement, large jumps

---

## Out of Scope (MVP)

- Multi-user concurrency
- Personal preference learning
- Long-term memory or profiling
- Non-location-based recommendations
- UI beyond Telegram chat responses

---

## Repo Structure (Current)

```
shogun/
├── app-services/
│   └── shogun-places-ingester/     ← Seeds neighborhoods → Postgres via platform places gateway
│   └── shogun-core/                ← TO BUILD: Telegram event processor + movement + LLM orchestration
├── docs/
│   ├── project_shogun_canonical_index.md   ← THIS FILE
│   ├── handoff/                    ← Closed milestone records (MVP 1, 2.1)
│   ├── MVP/                        ← MVP scope documents (some outdated)
│   ├── DB/                         ← DB schema and data policy docs
│   └── architecture/               ← Architecture diagrams
├── infra/                          ← Infrastructure config (review for relevance)
└── repo/                           ← Miscellaneous backup files (review for cleanup)
```

**Retired:**
- `platform-services/` — removed 2026-03-10. Services now owned by platform repo.

---

## Milestone Status

| Milestone | Status | Notes |
|:---|:---|:---|
| MVP 1 — Telegram ingress validation | CLOSED | Telegram gateway live on platform |
| MVP 2.1 — Platform infra + places DB | CLOSED | places-google on platform, DB schema stable |
| MVP 2.2 — Geographic correctness | CLOSED | JP anchor logic + strict mode in shogun-places-ingester |
| MVP 3 — shogun-core (control plane) | **IN PROGRESS** | Define and build shogun-core |

---

## Operating Rule

- Decisions land here.
- Exploration stays in chat.
- This index is updated deliberately, not automatically.

---

## Directory Reference

| Purpose | Path |
|:---|:---|
| Documentation | `c:\git\work\shogun\docs\` |
| Application services | `c:\git\work\shogun\app-services\` |
| Infrastructure | `c:\git\work\shogun\infra\` |
| Platform repo | `c:\git\work\platform\` |

*End of index.*
