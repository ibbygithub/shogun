# Project Shogun — Clean Handoff

**Audience:** Primary = Future Me. Secondary = Next ChatGPT / AI Assistant  
**Intent:** Reset context cleanly after a long build/debug session. This document is the *authoritative memory* for Project Shogun at the end of MVP1.

---

## 1. What Shogun Is (One‑Paragraph Truth)

Shogun is a **location‑aware AI concierge platform**. Its core job is to ingest real‑time user signals (starting with Telegram live location), normalize them, route them to an upstream decision engine, and proactively message users when conditions are met.

The architectural risk was never AI — it was **transport, normalization, and proactive feedback**. MVP1 focused exclusively on proving that loop.

---

## 2. Environments

### 2.1 Windows (Primary Development)
- Used for:
  - Editing code (VS Code)
  - Git commits and branch management
  - Controlled file edits (never inline shell overwrites)

**Repo root (Windows):**
```
C:\git\work\shogun
```

Rules learned the hard way:
- Always edit files in Windows
- Always verify with `git diff --name-only` before committing
- Never use shell redirection or partial overwrite commands for code

---

### 2.2 Linux (Runtime / Validation)
- Headless Linux server
- Docker + docker‑compose
- Used only for:
  - Pulling from GitHub
  - Building containers
  - Running services
  - Observing logs (with `--tail=N`, never streaming blindly)

**Repo root (Linux):**
```
/opt/git/work/shogun
```

---

## 3. GitHub & Repo Reality

- **Main branch** is authoritative
- MVP1 was stabilized and validated directly on `main`
- Feature branches were used temporarily but merged back

**Golden rule:**
> If `git diff` is empty on both Windows and Linux, you are testing exactly what is committed.

---

## 4. Deployed Services (MVP1)

### 4.1 Telegram Gateway (Ingress)
**Path:**
```
platform-services/telegram-ingress-service/gateway/
```

**Responsibilities:**
- Poll Telegram Bot API
- Receive all update types
- Normalize events into a stable envelope
- Forward events upstream over HTTP
- Send proactive Telegram messages when upstream requests it

Key discovery:
- Telegram **live location updates arrive as `edited_message`**, not new messages
- Gateway explicitly normalizes edited updates → `kind=location`

---

### 4.2 Upstream Stub (Harness)
**Path:**
```
platform-services/telegram-ingress-service/upstream-stub/
```

**What it is:**
- A **test harness**, not production logic
- Exists to validate:
  - event receipt
  - stateful evaluation
  - decision → reply feedback

**What it is NOT:**
- Not AI
- Not recommendation logic
- Not durable

The stub proved:
- movement‑based triggers
- cooldown logic
- proactive messaging loop

---

## 5. MVP1 — What Was Successfully Accomplished (Frozen)

### 5.1 Core Loop Proven

```
Telegram
  → Gateway (polling)
    → Normalized Event
      → Upstream Decision
        → Proactive Telegram Message
```

This loop works in real‑world conditions.

---

### 5.2 Features Delivered
- Telegram polling ingress
- Text, photo (+ caption), voice, document handling
- Live location handling (including edited updates)
- Normalized event envelope
- Capability flags for future intelligence layers
- Proactive, out‑of‑band Telegram messaging
- Dockerized, headless deployment

---

### 5.3 Major Bug Fixes / Learnings
- Fixed missing edited live‑location handling
- Fixed photo caption loss
- Fixed upstream route mismatch (`/telegram/events` vs `/`)
- Replaced step‑based movement logic with anchor‑based logic (conceptual)
- Established safe log inspection practices

---

## 6. MVP1 Explicit Success Criteria (All Met)

- [x] Live location works reliably
- [x] Edited updates normalized
- [x] Upstream can trigger proactive user messages
- [x] Architecture is ingress‑agnostic
- [x] Hardest technical uncertainty retired

**MVP1 is complete and should not be reopened.**

---

## 7. MVP2 — Clearly Defined Next Phase

Everything below was intentionally *not* MVP1. It is now MVP2.

### MVP2 Scope

1. **HTTP Webhooks & Edge Hardening**
   - Telegram webhooks (replace polling)
   - HTTPS termination (Cloudflare)
   - Secret validation / replay protection

2. **Persistence Layer**
   - Redis or database‑backed state
   - Restart‑safe sessions
   - Durable movement history

3. **Real Shogun Core (Replace Stub)**
   - FastAPI or equivalent service
   - Clean API contract
   - Business logic separated from ingress

4. **Search & LLM Intelligence**
   - Activate `can_search`, `can_scrape`, `can_fetch_files`
   - LLM reasoning
   - Location‑aware recommendations

5. **Multi‑User Support**
   - Per‑user isolation
   - Policy & rate limits

6. **Multi‑Ingress Readiness**
   - Matrix adapter
   - Future WhatsApp/SMS adapters

---

## 8. MVP3 (Placeholder Only)

Anything not completed in MVP2 rolls cleanly into MVP3.

No design work should be done for MVP3 until MVP2 is underway.

---

## 9. Rules for the Next AI Assistant (Important)

If you are ChatGPT reading this in the future:

- **Do not re‑debug MVP1 transport** — it works
- **Do not modify gateway or stub casually**
- **Assume polling mode is intentional for MVP1**
- **Ask before touching Docker or Git commands**
- **Prefer documents and contracts before code**

---

## 10. Closeout Statement

MVP1 retired the hardest unknowns in Shogun.

What remains is productization, not feasibility.

This document is the clean restart point.

---

*End of MVP1 handoff.*

