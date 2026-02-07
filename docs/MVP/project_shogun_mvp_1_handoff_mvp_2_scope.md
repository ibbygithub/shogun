<!-- FILE: docs/DB/Project-Shogun-MVP1-Handoff-v1.md -->

# Project Shogun – Database & Ingestion Phase
## Formal Turnover / Handoff Report (v1)

**Scope covered:** Database schema, storage provisioning, ICS ingestion, lodging normalization  
**Cutoff state:** Verified and stable as of latest validation queries  
**Audience:** Human engineer + future AI agents  
**Confidence level:** Production-ready for MVP-1 ingestion layer

---

## 1. Original Goals at Handoff

At the start of this phase, the explicit goals were:

- Stand up a PostgreSQL schema capable of supporting:
  - Trips
  - Events (flights, lodging, activities)
  - Future document ingestion (emails, Reddit, APIs, LLM outputs)

- Design for expansion, not final UX:
  - No privacy enforcement yet
  - No web UI yet
  - No Telegram triggers yet

- Ingest real-world data (ICS calendars) to validate schema design:
  - Flights calendar
  - Lodging calendar

- Normalize lodging data to support:
  - Check-in / check-out logic
  - Contact details (phones, WhatsApp, email)
  - Future enrichment

- Provision dedicated storage for raw ingestion artifacts

- Avoid premature complexity (SCP, resync, UI upload, etc.)

---

## 2. Goals Successfully Met

### 2.1 Database Schema (Core)

The following tables were created, validated, and populated:

- `trips`
- `trip_events`
- `lodging_details`
- `sources`
- `ingestion_runs`
- `documents`
- `document_embeddings`

**Key design decisions:**

- `trip_events` is the canonical timeline table
- Specialized data (e.g., lodging) lives in extension tables
- Raw ingestion metadata preserved as JSON (non-lossy)
- All relational anchoring flows through `trip_id`

---

### 2.2 Storage Provisioning (Option A – Completed)

Dedicated disk provisioned and mounted:

- **Size:** 128 GB
- **Mount:** `/srv/shogun`
- **Ownership:** `postgres:postgres`
- **Permissions:** `750`

Subdirectories created and writable by Postgres:

- `/srv/shogun/raw/ics`
- `/srv/shogun/raw/email`
- `/srv/shogun/raw/web`
- `/srv/shogun/raw/receipts`

Verified via mount checks, write tests, and reboot persistence.

---

### 2.3 ICS Ingestion (Flights + Lodging)

Successfully ingested:

- `Japan-2026-Flights-Detailed-v4.ics`
- `Japan-2026-Lodging-v2.ics`

**Results:**

- 7 total events
  - 3 flights
  - 3 lodging stays
  - 1 layover activity

- Correct population of `sources` and `ingestion_runs`
- All events tied to `trip_id = 1`

Validated:

- Ingestion pipeline
- Idempotent behavior
- Source attribution
- Event typing

---

### 2.4 Lodging Normalization

Defaults applied (explicit by design):

- **Check-in:** 16:00 local
- **Check-out:** 11:00 local
- **Timezone:** `Asia/Tokyo`

Lodging data model includes:

- `lodging_name`
- `phone_primary`
- `phone_after_hours`
- `phone_tollfree`
- `phone_fax`
- `whatsapp`
- `email`
- `checkin_local_time`
- `checkout_local_time`
- `checkin_tz`
- `checkout_tz`

**Behavioral guarantees:**

- Lodging is not modeled as all-day
- `starts_at` / `ends_at` represent real occupancy windows in UTC
- Correct across DST and multi-day spans

---

### 2.5 City Derivation

Derived from `location_text` where possible:

| Event | City |
|------|------|
| Osaka Airbnb | Osaka |
| Kanazawa Hotel | Kanazawa |
| Tokyo Airbnb | *(blank – expected)* |

Blank city values are correct when address data is incomplete.

---

## 3. Coding & Operational Preferences

### Safety & Editing

- Never edit large files inline unless unavoidable
- Preferred workflow:
  1. Create new file
  2. Syntax check
  3. Backup original
  4. Atomically replace

This workflow was used for `import_ics_to_shogun_new.py`.

### Design Philosophy

- Schema first
- Preserve raw data
- Normalize later
- Avoid premature UI or transport layers
- Copy/paste acceptable for MVP-1

### Git Discipline

All scripts and SQL must be:

- Committed
- Versioned
- Tagged at logical milestones

**Pre-MVP-2 Commit Checklist:**

- [ ] `import_ics_to_shogun.py`
- [ ] SQL migration scripts executed in MVP-1
- [ ] This document

---

## 4. Explicitly Deferred (By Design)

- Privacy / redaction
- RBAC
- Web UI
- Telegram ingestion
- Automated email ingestion
- Large-scale crawling
- LLM embedding pipelines (beyond schema)

---

## 5. Issues Encountered & Resolved

| Issue | Resolution |
|-----|-----------|
| sudo permission confusion | Clarified root vs agent roles |
| lost+found chown error | Scoped fix to `/raw` |
| nano paste risk | Safe file replacement workflow |
| mangled SQL paste | Detected and corrected |
| missing lodging times | Defaults applied + recompute |

All issues closed.

---

## 6. Nice-to-Have Items Identified

- Manual calendar entry UI
- City enrichment service
- Human-readable itinerary view
- Source confidence scoring

These are future MVP items, not blockers.

---

## 7. Final State Summary

- Schema: stable
- Storage: provisioned
- Real data ingested: yes
- Lodging modeling: correct
- Timezones: correct

**MVP-1 ingestion layer complete.**

---

<!-- FILE: docs/MVP/MVP-2-Knowledge-and-Signal-Ingestion.md -->

# Project Shogun – MVP-2: Knowledge & Signal Ingestion

## Objective

Extend the stable MVP-1 ingestion foundation to support **external knowledge, enrichment, and signal sources** while preserving raw data, provenance, and auditability.

This phase focuses on *what the system knows*, not *how it is presented*.

---

## In-Scope Capabilities

### 1. External Knowledge Sources

- Reddit (travel, local, niche communities)
- Web articles (manual or API-based)
- Booking confirmations (email ingestion – semi-automated)
- LLM-generated summaries and notes

All content stored first as raw documents.

---

### 2. Document Ingestion Pipeline

- Raw document storage under `/srv/shogun/raw/*`
- Metadata recorded in `documents`
- Source attribution via `sources`
- Ingestion traceability via `ingestion_runs`

No deduplication heuristics required yet.

---

### 3. Embedding & Semantic Indexing

- Populate `document_embeddings`
- Support multiple embedding providers
- Preserve embedding model metadata

Embedding is additive, not destructive.

---

### 4. Enrichment Pipelines

- City inference when address missing
- Tagging (food, transit, culture, shopping, etc.)
- Confidence scoring by source type

Enrichment must be replayable and versioned.

---

## Explicitly Out of Scope (MVP-2)

- User-facing UI
- Real-time Telegram triggers
- Automated decision-making
- Privacy redaction
- Access control policies

---

## Guardrails

- Raw data is never overwritten
- All derived data must reference source IDs
- LLM outputs treated as documents, not truth
- No schema-breaking changes without migration

---

## MVP-2 Exit Criteria

- At least one non-ICS external source ingested
- Documents embedded and queryable
- Enrichment demonstrated on existing trip data
- Full provenance preserved

---

## Naming & Versioning

- Phase name: **MVP-2: Knowledge & Signal Ingestion**
- Tag upon completion: `shogun-mvp2-ingestion`

---

*This document intentionally defines capability boundaries to prevent premature UI or automation coupling.*

