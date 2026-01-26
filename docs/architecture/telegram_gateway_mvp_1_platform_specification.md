# Telegram Gateway — MVP1 Platform Specification

**Status:** Vetted design (no implementation yet)

**Purpose:**
Define a reusable, project-agnostic Telegram platform service that can support multiple bots (4–10 over 6–12 months) while keeping business logic isolated in per-project upstream services (e.g., Shogun Concierge).

---

## 1. Core Design Principle

**Telegram is infrastructure, not the product.**

The Telegram layer exists to:
- Receive messages reliably
- Enforce access control
- Normalize events
- Route them to the correct project handler

It must remain:
- Boring
- Predictable
- Reusable

All domain logic (travel, ops, health checks, budgets, AI reasoning) lives **outside** the Telegram layer.

---

## 2. High-Level Architecture

```
Telegram Servers
      ↓
Telegram Gateway (shared image)
      ↓
Project Upstream Service (e.g. Shogun Core)
      ↓
Telegram Gateway
      ↓
Telegram User
```

### Layer Responsibilities

#### Telegram Gateway (shared platform)
- Polls Telegram (default for MVP1)
- Applies access rules
- Normalizes updates into envelopes
- Forwards envelopes to upstream via HTTP
- Sends replies back to Telegram
- Implements minimal routing / safety rules

#### Project Upstream (per project)
- Implements domain logic
- Handles budgets, rate limits, queues
- Returns `reply_text` or structured actions

---

## 3. Bot Model

### Token Strategy
- **One Telegram bot token per project**
- Each token runs its own instance of the gateway
- All instances share the same gateway image

Examples:
- `shogun-concierge`
- `shogun-ops` (later)
- `future-project-x`

This avoids:
- Cross-project coupling
- Secret sprawl inside a single runtime
- Large blast radius on failure

---

## 4. Access Control Model

### Primary: Telegram User ID Allowlist
- Gateway maintains an allowlist of Telegram **user IDs**
- Default behavior: ignore or reject messages from non-allowed users

### Optional: Group Chat Allowlist
- Specific Telegram **group chat IDs** may be allowed
- Group support is secondary and opt-in

### Default UX Policy
- **1:1 Direct Messages are primary**
- Group chats add noise and are discouraged by default

### Recommended Group Rule (if enabled)
- Only respond in groups if:
  - chat ID is explicitly allowed
  - AND message is a command or bot is mentioned

---

## 5. Message Flow & Envelope Contract

### Inbound Normalization
All Telegram updates are normalized into a consistent envelope before routing.

Example envelope (conceptual):
```json
{
  "receipt_id": "abc123",
  "received_at": "2026-01-25T20:00:00Z",
  "kind": "text | location | photo | voice | document | video_note",
  "from": {
    "user_id": 123456789,
    "username": "ibby"
  },
  "chat": {
    "id": 987654321,
    "type": "private | group"
  },
  "payload": { /* message-specific data */ }
}
```

### Upstream Contract
- Gateway sends envelope via HTTP POST
- Upstream responds with:

```json
{
  "reply_text": "optional text to send back"
}
```

If `reply_text` is absent, gateway applies fallback rules.

---

## 6. Failure & Fallback Rules (MVP1)

The gateway applies **hybrid behavior** when upstream is unavailable.

### Default Rules

| Message Type | Behavior if Upstream Down |
|-------------|---------------------------|
| Location updates | ACK receipt ("Received") |
| Media uploads | ACK receipt |
| Commands (/help, /status) | Reply "Service temporarily unavailable" |
| Free-form text | ACK + brief delay notice |

This prevents:
- User confusion
- Message storms
- Silent failures

---

## 7. Polling vs Webhook Strategy

### MVP1 Default: Polling
- Gateway uses Telegram long polling
- Works without inbound internet connectivity
- Simple and reliable for LAN-only hosts

### Future Option: Webhooks
- Can be enabled per gateway instance
- Requires public ingress or tunnel
- No change required to upstream services

---

## 8. Rules Engine Scope (Intentionally Small)

Gateway rules are **policy**, not business logic.

### Allowed in Gateway
- Allowlist enforcement
- Message normalization
- Rate limiting Telegram replies
- Retry/backoff when upstream fails
- Command routing for gateway-level commands (e.g. /status)

### Not Allowed in Gateway
- Travel logic
- Places API calls
- Budget tracking
- AI reasoning

---

## 9. Cross-Platform Canonical Folder Standard (Windows ↔ Linux)

This project uses a **single canonical repo tree** that exists on both the Windows development laptop and the Linux deployment host.

### Canonical Roots
- **Windows (dev):** `C:\git\`
- **Linux (deploy):** `/opt/git/`

### Canonical Project Location (relative)
- Project work root: `work/shogun/`

So the same files live at:
- Windows: `C:\git\work\shogun\...`
- Linux: `/opt/git/work/shogun/...`

### Automation Rule: No Guessing
Any automation/agent that reads or writes Shogun artifacts must:
- Treat the above as the only valid roots
- Never write outside `work/shogun/`
- Use **relative paths** inside the repo tree whenever possible

### Repository Structure (authoritative)
```
work/shogun/
  ├─ docs/                      # specifications, decisions, checklists
  ├─ infra/                     # deployment, ops, environment wiring
  │   ├─ compose/               # optional: top-level compositions (future)
  │   └─ SHOGUN_PATHS.md        # canonical path contract for automation
  ├─ platform-services/         # shared services (each independently deployable)
  │   ├─ telegram-ingress-service/
  │   ├─ google-places-service/
  │   └─ web-scrape-service/
  └─ repo/                      # application code repos
      ├─ shogun-core/
      └─ shogun-web/
```

> **Note:** If `telegram-ingess-service` exists today, rename to `telegram-ingress-service` to prevent drift.

### Deployment Flow Options (MVP1 Guidance)
You will choose one primary mechanism; both are compatible with this folder standard.

**Option A — Git-based deploy (recommended for simplicity)**
- Dev happens in `C:\git\work\shogun\...`
- Changes are committed/pushed to a Git remote
- Linux host pulls to `/opt/git/work/shogun/...`
- Compose is run from the Linux working copy

**Option B — Container registry deploy (recommended for predictable runtime)**
- Build container images from the same tree (dev or CI)
- Push images to a registry (private)
- Linux host pulls images and runs compose using pinned image tags/digests
- Source tree still exists on Linux for compose files, configs, and docs

For MVP1, start with **Option A (Git)** unless you specifically need image immutability early.

---

## 10. Secrets & Configuration Strategy (MVP1)

### Directory Layout
```
/opt/git/work/shogun/
  ├─ platform-services/
  │   ├─ telegram-ingress-service/
  │   │   ├─ .env
  │   │   └─ docker-compose.yml
  │   ├─ google-places-service/
  │   └─ web-scrape-service/
  └─ repo/
      ├─ shogun-core/
      └─ shogun-web/
```

### Environment Variables (Per Bot / Service)
- `TELEGRAM_BOT_TOKEN`
- `ALLOWED_USER_IDS`
- `ALLOWED_GROUP_IDS` (optional)
- `UPSTREAM_URL`

Secrets are:
- Per service
- Centralized under the canonical tree
- Permission-restricted at OS level

---

## 11. Naming & Identity

To avoid future confusion:

- Platform: **telegram-gateway**
- Instance: **<project>-gateway**
- Upstream: **<project>-core**

Avoid naming anything `*-bot` unless it is strictly Telegram-facing.

---

## 11. MVP1 Scope Summary

**In Scope:**
- Reusable Telegram gateway image
- Per-project bot instances
- User allowlist
- Polling transport
- Envelope forwarding
- Hybrid fallback behavior

**Out of Scope (Future):**
- Central bot registry
- Dynamic bot provisioning
- Webhook-only operation
- Advanced policy engines

---

## 12. Cross‑Platform Development & Deployment Model (MVP1)

Shogun uses a **two‑phase model**:

1. **Development phase (Windows laptop)** — AI agents and humans build code, compose files, and docs.
2. **Deployment phase (Linux servers)** — services run continuously and predictably.

To avoid automation guesswork, **directory structure and relative paths are identical across platforms**.

---

### 12.1 Canonical Roots (Absolute Paths)

| Platform | Canonical Root |
|--------|----------------|
| Windows (dev) | `C:\git\` |
| Linux (deploy) | `/opt/git/` |

All automation, agents, and scripts **must treat these as immutable roots**.

No service, script, or agent may write outside these roots.

---

### 12.2 Canonical Relative Structure

The following tree exists **identically** on Windows and Linux:

```
<root>/git/
├─ archive/           # frozen, historical repos
├─ vendor/            # third‑party reference repos (read‑only)
└─ work/
   ├─ ai-agent-buildout/
   └─ shogun/
      ├─ docs/        # specs, ADRs, platform docs
      ├─ infra/       # deployment assembly, environment wiring
      ├─ platform-services/
      │  ├─ telegram-gateway/
      │  ├─ google-places-service/
      │  └─ web-scrape-service/
      └─ repo/
         ├─ shogun-core/
         └─ shogun-web/
```

Only **relative paths** inside this tree may be used in documentation or automation.

---

### 12.3 Platform Services Rule

Each directory under `platform-services/` is:
- A **standalone service**
- Owns its **own Dockerfile and docker-compose.yml**
- Deployable independently

Example:
```
platform-services/telegram-gateway/
├─ docker-compose.yml
├─ Dockerfile
└─ README.md
```

No platform service may depend on absolute host paths.

---

### 12.4 Application Repos Rule

Directories under `repo/` represent **project logic**, not infrastructure.

Examples:
- `repo/shogun-core/` — concierge logic, APIs, AI
- `repo/shogun-web/` — UI or external interfaces

Application repos **never talk directly to Telegram**.

---

### 12.5 Source of Truth: Git

**Git is the authoritative synchronization mechanism** between Windows and Linux.

Flow:
1. Development happens under `C:\git\work\...`
2. Changes are committed and pushed
3. Linux hosts pull into `/opt/git/work/...`

This ensures:
- deterministic state
- reproducibility
- no hidden drift

---

### 12.6 Container Registry (Phase 1.5)

After Git‑based deployment is stable:
- Images may be built on Windows
- Published to a container registry
- Pulled on Linux servers

This is optional and **not required for MVP1**, but paths and naming are designed to support it later.

---

### 12.7 SHOGUN_PATHS.md (Mandatory File)

At `work/shogun/SHOGUN_PATHS.md`, define:

- Canonical Windows root
- Canonical Linux root
- Allowed subdirectories
- Forbidden write locations

All automation and AI agents must reference this file before creating or moving files.

---

## 13. Updated Next Steps

1. Create `SHOGUN_PATHS.md`
2. Rename `telegram-ingess-service` → `telegram-gateway`
3. Create platform-service skeletons (no logic yet)
4. Create Shogun Core upstream stub

---

**This section formalizes the cross‑platform contract and eliminates path ambiguity for humans and AI agents alike.**

