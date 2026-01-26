# Shogun MVP — Next Steps Checklist (v1)

**Purpose:** A short, operational checklist to track progress after finalizing the AI Services Rails design.

This document intentionally contains **only execution steps**, not design rationale.

---

## Step 1 — Create Empty Containers (Rails Validation)
**Goal:** Verify Docker, networking, and ports without worrying about API correctness yet.

**Actions:**
- [ ] Create shared Docker network (`ai_net`)
- [ ] Bring up containers:
  - [ ] OpenAI MCP server
  - [ ] Gemini MCP server
  - [ ] Google Places FastAPI service
  - [ ] Unstructured parsing service
- [ ] Confirm containers stay running (`docker ps`)
- [ ] Confirm ports are listening on the Docker host

**Success Criteria:**
- Containers are up and stable
- No crash loops
- Ports are reachable from the host

---

## Step 2 — Laptop → Lab Smoke Tests (No Real Data Yet)
**Goal:** Prove connectivity from the laptop dev environment to lab services.

**Actions:**
- [ ] From laptop, call Places API `/health`
- [ ] From laptop, attempt MCP connection to:
  - [ ] OpenAI MCP endpoint
  - [ ] Gemini MCP endpoint
- [ ] Confirm responses are reachable (even if auth errors occur)

**Success Criteria:**
- Network path is validated
- No firewall or routing surprises
- Errors (if any) are predictable and auth-related

---

## Step 3 — Enable One Real API at a Time
**Goal:** Turn on real functionality in a controlled order.

**Order (do not skip):**
1. [ ] OpenAI MCP (chat + embeddings)
2. [ ] Gemini MCP (chat + embeddings)
3. [ ] Google Places API wrapper
4. [ ] Firecrawl scraper
5. [ ] Unstructured parsing

**Rules:**
- If one service fails, **stop and fix it before proceeding**
- Do not debug multiple services simultaneously

**Success Criteria:**
- Each service returns valid real data before moving on

---

## Step 4 — Create Shogun Service Index
**Goal:** Centralize service discovery for Shogun and future agents.

**Actions:**
- [ ] Create `SERVICE_INDEX.md` (or JSON)
- [ ] For each service, record:
  - Name
  - Host/IP
  - Port
  - Purpose
  - Status (up/down/experimental)

**Success Criteria:**
- One authoritative reference for all running services
- Shogun code references this index, not hardcoded assumptions

---

## Completion Rule
Once Steps 1–4 are complete:
- MVP infrastructure is considered **stable**
- No refactoring allowed until Shogun has real end-to-end usage
- Tag the repo (e.g. `shogun-mvp-infra-v1`)

---

**Status:** ⬜ Not Started

**Last Updated:** 2026-01-25
