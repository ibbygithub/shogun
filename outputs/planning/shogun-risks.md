# Risk Register — Shogun Reboot / MVP 3
Last updated: 2026-03-10

---

## Active Risks

### R-01: LLM response latency exceeds Telegram timeout
**Risk:** Inline processing means the LLM call must complete before shogun-core
returns a response to the Telegram gateway. If the LLM takes >25 seconds,
the gateway may timeout and the user gets no reply.
**Likelihood:** Medium (Gemini 2.0 Flash is fast, but place lookup + LLM is two
sequential network calls)
**Impact:** High — user receives no response, appears broken
**Category:** Architecture
**Mitigation:**
- Use Gemini 2.0 Flash (lowest latency model on LLM gateway) for all MVP calls
- Set aggressive timeouts on places and LLM calls (5s places, 15s LLM)
- Return a "thinking" ack immediately if Telegram supports it (it does not for
  webhook mode — this mitigation is not available)
- If this triggers in testing, revisit with Valkey pub/sub queue (already in backlog)
**Status:** Open

---

### R-02: GPS drift causes false movement triggers
**Risk:** Live location updates can drift 10-50m without the user actually moving.
A 100m threshold may fire recommendations repeatedly while the user is stationary.
**Likelihood:** High — GPS drift in urban environments (Japan, dense buildings) is significant
**Impact:** Medium — spammy recommendations, poor UX
**Category:** Architecture
**Mitigation:**
- Set threshold to 150m (not 100m as originally suggested in canonical index)
- Add cooldown: do not trigger again within N minutes of last trigger (suggest: 5 min)
- Both threshold AND cooldown must be satisfied to trigger
**Status:** Open — threshold value is an open decision

---

### R-03: Valkey data loss on container restart without persistence configured
**Risk:** If Valkey is deployed without AOF persistence, a container restart wipes
all session state. User loses conversation context and location history.
**Likelihood:** High (if not configured) / Low (if configured correctly)
**Impact:** Medium — annoying but not catastrophic for single-user MVP
**Category:** Operational
**Mitigation:** Configure AOF (appendonly yes) in Valkey before first use.
Document in service README. Verify with a restart test during Phase 1.
**Status:** Open — mitigated by correct deployment config

---

### R-04: Telegram gateway UPSTREAM_URL misconfiguration
**Risk:** Telegram gateway currently has no UPSTREAM_URL set that points to
shogun-core (shogun-core doesn't exist yet). If the gateway is live and
receiving events, those events go nowhere.
**Likelihood:** High — this is a known gap
**Impact:** Low for now (no users actively using it), High once shogun-core is live
**Category:** Operational
**Mitigation:** Phase 2 explicitly includes updating UPSTREAM_URL as an exit
criterion. Do not mark Phase 2 complete without verifying the gateway forwards
events to shogun-core.
**Status:** Open — resolved in Phase 2

---

### R-05: places data not seeded when shogun-core goes live
**Risk:** shogun-core Phase 4 depends on place data in Postgres. If
shogun-places-ingester has not been run against the target DB, place lookup
returns empty results and the LLM has nothing to format.
**Likelihood:** Medium — ingester exists but may not have run on current DB state
**Impact:** High — Phase 4 exit criteria fail; no recommendations delivered
**Category:** Dependency
**Mitigation:** Make ingestion a Phase 4 entry criterion. Run ingester, verify
row count in places.google_places before starting Phase 4 work.
**Status:** Open

---

## Closed Risks

*(None yet)*
