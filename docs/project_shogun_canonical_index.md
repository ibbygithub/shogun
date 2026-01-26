# Project Shogun — Canonical Index

**Status:** Authoritative snapshot (Option A)
**Purpose:** Freeze what has been clearly decided so far into durable working documents.

---

## What This Index Is

This document is the *entry point* for Project Shogun’s canvas-based documentation. It intentionally contains **only confirmed decisions** and points to focused canvases that will be created next.

Chat remains exploratory. Canvases are canonical.

---

## Confirmed Decisions (Locked)

### Product Intent

- Shogun is an **AI concierge** focused on **location-aware, contextual responses**.
- MVP validates **movement-based updates** (radius logic) and **local discovery** (food / nearby info).
- MVP is **single-user**, **single primary use case**, production-oriented.

### Messaging & Platform

- Interface: **Telegram Bot**
- Transport: **Webhooks only** (no polling)
- Location input:
  - One-time location
  - **Live Location (preferred)**
- Shogun does **not** poll GPS.
- Update cadence is **client-controlled and variable** (seconds to \~1 minute).

### Privacy & Reality Constraints

- Shogun reacts only to **pushed events** from Telegram.
- Location accuracy and frequency are **not guaranteed**.
- System must tolerate missed or delayed updates.

### Architecture (High-Level)

- Telegram → Webhook → FastAPI control plane
- Work is **queued**, not handled inline
- Backend runs **headless on Linux**, 24/7
- State is minimal and explicit (no hidden memory assumptions)

### Infrastructure & Resource Model (MVP)

- MVP includes standing up **reusable infrastructure resources** via **Docker containers**.
- These resources expose capabilities through **API-accessible services**, intended for reuse across:
  - Future Shogun iterations
  - Other products and agents
- Initial resource types include (non-exhaustive):
  - Web scrapers
  - Parsers / normalizers
  - Embedders
- Resources are integrated using **MCP-style service boundaries** and containerized deployment.
- Multiple external service providers are supported and evaluated, including:
  - OpenAI
  - Google
  - Anthropic
- For the MVP, the goal is **capability validation and integration**, not provider lock-in or optimization.

### Movement Model (Conceptual)

- Movement is inferred by **distance delta** between updates
- Radius-based triggers (e.g., \~100 meters)
- Logic must handle:
  - Irregular updates
  - No movement
  - Large jumps

---

## Out of Scope (MVP)

- Multi-user concurrency
- Personal preference learning
- Long-term memory or profiling
- Non-location-based recommendations
- UI beyond Telegram chat responses

---

## Upcoming Focused Canvases (To Be Created)

1. **Project Shogun — MVP Definition**

   - Goals, non-goals, success criteria

2. **Project Shogun — Location & Movement Model**

   - Distance calculations
   - Thresholds
   - Edge cases

3. **Project Shogun — System Architecture**

   - Control plane vs workers
   - Queues
   - Failure modes

4. **Project Shogun — Repo & Folder Structure**

   - Backend layout
   - Outputs / logs
   - Validation artifacts

These will be created as **separate canvases**, each authoritative for its domain.

---

## Operating Rule Going Forward

- Decisions land in canvas.
- Exploration stays in chat.
- Canvases are updated deliberately, not automatically.

*End of index.*

document repo is for this and any other generated canvas document is c:\git\work\shogun\docs\
other directories for code are c:\git\work\shogun\repo , infrastructure is c:\git\work\shogun\infra , platform services is c:\git\work\shogun\platform-services

