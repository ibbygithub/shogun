# Shogun MVP-1 Hardened Baseline — Clean Handoff

**Filename:** SHOGUN_MVP1_HANDOFF_2026-01-26.md  
**Purpose:** Clean restart context for a new chat / agent with zero baggage  
**Status:** VERIFIED WORKING + HARDENED

---

## 1. Current State (Verified, Working)

**Date:** 2026-01-26  
**Branch:** `main`  
**Tag:** `mvp1-baseline-hardened-20260126`

### Runtime Verification
- Telegram bot is live and responsive
  - `ping` → upstream stub responds
  - `/status` → gateway responds “alive”
- Docker services running:
  - `telegram-gateway`
  - `upstream-stub` (temporary core placeholder)
- Restart tested after merge — system recovers cleanly

---

## 2. Architecture (Current)

```
Telegram
   ↓
telegram-gateway (Node.js)
   ↓ HTTP
upstream-stub (Node.js)
```

- Polling mode only
- No webhooks yet
- No location handling yet
- No shogun-core yet

---

## 3. What Was Accomplished (Fact-Based)

### Security & Stability (Permanent)
- `.env` REMOVED from Git tracking
- `.env` explicitly ignored via `.gitignore`
- `.env.example` added for reproducible setup
- Secrets now survive merges, pulls, branch switches, rebases
- `.env` restored from Git history after deletion
- Token rotation completed and verified

### Repo Integrity
- `main` branch clean
- Hardened baseline tagged
- Known-good rollback point exists
- No uncommitted state

---

## 4. Canonical Paths (Do Not Guess)

**Repo root**
```
/opt/git/work/shogun
```

**ONLY valid Telegram ingress location**
```
platform-services/telegram-ingress-service/
```

Contents:
```
.env                # local-only, ignored, REQUIRED at runtime
.env.example        # tracked template
docker-compose.yml
gateway/
upstream-stub/
```

---

## 5. HARD SAFEGUARDS (MANDATORY)

### Secrets & Debugging Rules
The assistant MUST NOT request or suggest:
- `docker compose config` (unredacted)
- `cat .env`
- `printenv` / `env`
- `docker inspect` env output
- Any command that expands secrets

Allowed:
- Redacted checks
- Yes/No validation
- Runtime behavior tests (`ping`, `/status`)

### Git Rules
- `.env` must NEVER be committed
- `.env` must be recreated from `.env.example`
- Never remove tracked secrets without preserving a local copy

---

## 6. Definition of Progress Going Forward

Progress MUST be:
- A new user-visible feature, OR
- A new architectural capability

Not progress:
- Infra churn
- Re-hardening secrets
- Cleanup without feature movement

---

## 7. Next Feature Options (Choose ONE)

- **Option A:** Webhooks
- **Option B:** Location Handling
- **Option C:** shogun-core Introduction

---

## 8. One-Sentence Context for New Chat

> “We have a hardened, working MVP-1 Telegram ingress with polling mode. Secrets are local-only and safe. Choose one feature path and move forward.”

---
