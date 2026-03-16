# MVP 2.1 HANDOFF – SHOGUN PLATFORM (PLACES SERVICE)

**Status:** CLOSED (MVP 2.1)

**Priority Declaration:**
> *Google Places ingestion is an **operational test harness only**. Geographic logic is **incomplete by design** and intentionally left unresolved for MVP 2.1.*

**Sources of Truth:**
- **Code:** Git repository (`main` branch)
- **Data:** PostgreSQL schema (`shogun_v1`, `places` schema)

---

## 1. Executive Summary (Non‑Technical)

MVP 2.1 successfully established the **foundational platform infrastructure** for Shogun’s location-aware services. Core system components—networking, reverse proxy, database schema, credentials, containerization, and service health—are now operational and reproducible.

The Google Places service is running end-to-end, authenticated, and capable of ingesting seed data, persisting records, and exposing APIs. However, **geographic correctness (country / region accuracy)** is *not* solved in this milestone. This is intentional.

MVP 2.1’s goal was **platform validation**, not business correctness. The Places service is explicitly treated as a **test harness** to validate:
- API wiring
- Schema durability
- Ingestion mechanics
- Observability and rollback

Correct geospatial logic is deferred to MVP 2.2.

---

## 2. MVP 2.1 Goals (Original Intent)

### Primary Goals
- Stand up a production‑grade platform skeleton
- Validate Google API authentication and quotas
- Establish durable DB schema for places ingestion
- Prove reverse‑proxy routing and service isolation
- Enable repeatable ingest cycles with auditability

### Explicit Non‑Goals (Deferred)
- Correct geographic scoping
- User‑trustworthy recommendations
- Multi‑region production logic
- Cost optimization

---

## 3. What Is **DONE** (Logically Closed)

> DONE means *operationally complete*, even if logic is imperfect.

### Infrastructure
- Reverse proxy routing to `places.platform.ibbytech.com`
- Per‑service Docker Compose model
- Container build & restart lifecycle validated
- Health endpoint operational

### Database
- `shogun_v1` database created
- `places` schema defined and stable
- `google_places` table populated
- `google_place_snapshots` audit table populated
- Indexing in place (geo, city, PK)

### Security & Access
- Google API keys injected and verified
- DB role `places_app` created
- Schema‑scoped privileges granted
- Least‑privilege model established (DBA override only)

### Application
- `app.py` runs cleanly
- Modular ingestion pipeline exists
- Seed ingestion endpoint functional
- Error handling + stats returned
- Country mismatch detection present (flagging only)

### Dev Workflow
- Windows = authoritative dev environment
- GitHub = single source of truth
- Linux nodes = deployment targets only
- Push / pull sync verified

---

## 4. What Is **NOT DONE** (Intentionally Open)

> NOT DONE means *logic incomplete or intentionally deferred*.

### Geographic Correctness
- Address → lat/lng resolution is **not trusted yet**
- Country correctness is not enforced at query time
- IP / region bias behavior is unverified

### Business Semantics
- Results are not user‑safe
- Data may be globally incorrect
- No deduplication strategy finalized

### Cost & Scale
- No request throttling strategy
- No caching strategy
- No per‑city quotas

---

## 5. Known Failures (Documented, Accepted)

- Places results returned from incorrect countries
- Google API behaves correctly *given provided inputs*
- Misinterpretation initially framed as “bug” — corrected to **design gap**

This is **not** a regression. It is an expected outcome of MVP 2.1 scope.

---

## 6. Rollback & Hygiene

### Rollback
- Drop/recreate `places` schema
- Re‑ingest from seeds
- No upstream dependencies

### Audit
- Raw Google responses preserved
- Snapshot timestamps retained
- Country mismatch flag retained for tuning

---

## 7. MVP 2.2 – Required Next Work

### Priority 1: Anchor Resolution (Hard Requirement)
- Resolve address → lat/lng using **Google Geocoding API**
- Enforce `components=country:XX`
- Persist resolved anchors in DB
- Never re‑guess anchors after resolution

### Priority 2: Query Discipline
- Nearby search must use lat/lng only
- Text search must be region‑constrained
- Explicit country mismatch rejection

### Priority 3: Data Trust Model
- Mark data as `trusted_geo = true/false`
- Prevent untrusted data from surfacing to users

### Priority 4: Multi‑Region Readiness
- Japan strict mode
- California soft mode
- Config‑driven, not hard‑coded

---

## 8. Guidance for Humans & AI Agents

### For Humans
- Treat MVP 2.1 as **plumbing validation**
- Do not trust output data
- Do not “patch around” logic gaps

### For AI Agents
- Do not optimize
- Do not infer geography
- Follow DB as ground truth
- Assume Places service is sandboxed

---

## 9. Final Statement

MVP 2.1 is **successfully closed**.

The system works.
The logic does not.
And that is **by design**.

---

**Document:** `MVP_2.1_HANDOFF.md`
**Owner:** IbbyTech
**Next Milestone:** MVP 2.2 – Geo‑Correctness

