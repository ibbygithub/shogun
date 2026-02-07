# Shogun MVP1 – Telegram Live Location & Gateway Validation

**Date:** 2026-01-27  
**Status:** ✅ MVP1 SUCCESSFULLY VALIDATED  
**Scope:** Telegram ingress → Gateway → Upstream decision → Proactive response

---

## 1. Executive Summary

Today validated the *core architectural promise* of Shogun MVP1:

> **Telegram events (including live location) can be normalized, routed upstream, evaluated, and used to proactively message users.**

This is the hardest part of the system. Everything beyond this (LLMs, search, recommendations) is additive.

The work today confirmed that the transport layer, event model, and proactive messaging loop are sound.

---

## 2. Completed MVP1 Objectives

### ✅ Telegram Ingress
- Telegram Bot operational in **polling mode** (no Cloudflare/webhooks required)
- Bot reliably receives:
  - text messages
  - photos (with captions)
  - voice messages
  - documents
  - **live location**

### ✅ Critical Telegram Reality Discovered
- Live location updates arrive primarily as **`edited_message`** events, not new messages
- This required explicit handling and normalization

---

## 3. Gateway (telegram-ingress-service) – Completed Work

### Features Implemented
- Normalized all Telegram update types into a **stable event envelope**:
  - `kind=text`
  - `kind=photo`
  - `kind=voice`
  - `kind=document`
  - `kind=location`

- Unified handling of:
  - initial location shares
  - **edited live-location updates** → normalized as `kind=location`

- Added **capability flags** to every event:
  - `can_search`
  - `can_scrape`
  - `can_fetch_files`

- Implemented **proactive Telegram messaging**:
  - Gateway can send messages without a direct user prompt
  - Triggered only when upstream explicitly returns `reply_text`

### Bug Fixes
- Fixed missing propagation of edited live-location updates
- Fixed photo + caption handling (captions now preserved)
- Fixed upstream route mismatch (`/telegram/events` vs `/`)
- Added safe logging patterns to avoid SSH lock-ups

---

## 4. Upstream Stub – Purpose & Results

### What the Stub Is (and Is Not)
- ✅ A **test harness** and contract validator
- ❌ Not production logic
- ❌ Not AI or recommendation engine

### Validated Capabilities
- Receives normalized events from gateway
- Maintains per-chat state
- Evaluates movement thresholds
- Returns `reply_text` to trigger proactive messaging

### Key Insight
Movement logic must be **anchor-based**, not step-based, to match human expectations:
- Trigger when moving *far enough from a reference point*
- Not based on incremental GPS jitter

This insight directly informs future geofence and proximity features.

---

## 5. Confirmed End-to-End Flow (MVP1 Core)

```
Telegram App
  ↓ (polling)
Telegram Gateway
  ↓ (normalized event)
Upstream Service
  ↓ (decision)
Telegram Gateway
  ↓ (proactive send)
User
```

This loop is now **proven in real-world conditions**.

---

## 6. Operational Lessons Learned

### Transport & Infra
- Polling mode is sufficient for MVP1
- Webhooks / Cloudflare can be added later without refactor
- Docker rebuilds must follow Git pulls deterministically

### Developer Ergonomics
- Always prefer full-file edits over inline snippets
- Always verify with `git diff --name-only` before commit
- Use `docker compose logs --tail=N` to avoid SSH lock

### Product Reality
- Telegram GPS updates are irregular and device-dependent
- Thresholds must be testable (20m for dev, 100m+ for prod)

---

## 7. What MVP1 Now Enables

With this foundation, Shogun can now:
- Recompute recommendations as a user moves
- Trigger contextual nudges (food, coffee, water, safety)
- Support multi-step, long-lived conversations
- Swap Telegram for other ingress platforms (Matrix, WhatsApp later)
- Introduce LLMs *without touching transport code*

---

## 8. Explicit MVP1 Success Criteria (All Met)

- [x] Live location works reliably
- [x] Edited updates normalized
- [x] Upstream decisions flow back to user
- [x] Proactive messaging proven
- [x] Architecture is swappable and clean

---

## 9. MVP Status Update & Roadmap

### MVP1 — **Complete** ✅
MVP1 is officially complete and validated in real-world conditions.

**MVP1 Scope (Delivered):**
- Telegram ingress (polling mode)
- Normalized event gateway
- Live location handling (including edited updates)
- Upstream decision loop (via stub harness)
- Proactive Telegram messaging
- Dockerized, headless Linux deployment

This milestone proves the *transport, normalization, and decision-feedback loop* — the hardest architectural risk.

---

### MVP2 — **Next Phase (Promoted from Yellow Items)** 🚧
All previously "yellow" items are now explicitly designated as **MVP2**.

**MVP2 Scope:**
1. **HTTP Webhooks & Edge Hardening**
   - Telegram webhooks (replace polling)
   - HTTPS termination (Cloudflare)
   - Secret validation & replay protection

2. **Persistence Layer**
   - Redis or database-backed state
   - Durable location/session tracking
   - Restart-safe behavior

3. **Real Shogun Core (Replace Stub)**
   - FastAPI or equivalent service
   - Business logic separated from ingress
   - Clean API boundary for intelligence layer

4. **Search & Intelligence Integration**
   - Activate `can_search`, `can_scrape`, `can_fetch_files`
   - LLM-backed reasoning and summarization
   - Location-aware recommendations

5. **Multi-User & Policy Expansion**
   - Broader user allowlists
   - Per-user state isolation
   - Rate limits and safety policies

6. **Multi-Ingress Readiness**
   - Matrix-compatible ingress adapter
   - Future WhatsApp / SMS compatibility

---

### Why This Is **MVP2**, Not MVP1.5
This next phase:
- Introduces **new capabilities**, not refinements
- Adds **scale, durability, and intelligence**, not fixes
- Changes the *operational posture* of the system

That makes it a clean **MVP2**, not a 1.5.

---

### 10. Closeout Statement

MVP1 successfully retired the primary technical unknowns.

MVP2 is now about **productization**, not feasibility.

Freezing MVP1 here is the correct engineering decision.

---

*Document updated to reflect MVP1 completion and MVP2 scope definition.*

