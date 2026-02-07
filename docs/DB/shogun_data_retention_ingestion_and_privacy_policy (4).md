# Shogun Data Retention, Ingestion, and Privacy Policy

**Status:** Authoritative (MVP2 Baseline)

**Audience:** Human operators, future AI assistants, and contributors to Project Shogun

**Purpose:**
This document defines the canonical rules for how Shogun ingests data, stores it, retains it, embeds it, and governs privacy. These policies are intended to prevent schema churn, uncontrolled storage growth, and privacy regressions as Shogun evolves.

---

## 1. Core Principles

1. **Persist raw first, normalize second**
   Raw artifacts are always retained (temporarily) before normalization. Normalized data can be regenerated if logic improves.

2. **Trips are the primary container**
   All user activity, events, surveys, expenses, and knowledge are scoped to a `trip`.

3. **Disk for bulk, database for truth**
   Large or unstructured content lives on disk. PostgreSQL stores metadata, pointers, normalized facts, and embeddings.

4. **Private by default**
   User-specific data is private unless explicitly shared.

---

## 2. Data Categories & Storage Locations

### 2.1 Raw Artifacts (Disk)
Stored under:
```
/srv/shogun/raw/
  ├── ics/
  ├── email/
  ├── web/
  ├── receipts/
```

Examples:
- ICS calendar files
- Email bodies and attachments
- Scraped HTML pages
- Screenshots, PDFs, receipts

Tracked in DB via:
- `sources` table (hash, metadata, content_uri)

---

### 2.2 Normalized Facts (PostgreSQL)
Examples:
- `trip_events` (flights, lodging, activities)
- `lodging_details` (contacts, WhatsApp, phones, email)
- `surveys`, `survey_votes`
- `expenses`

These tables represent *interpreted facts*, not raw input.

---

### 2.3 Knowledge Text (PostgreSQL)
Stored in:
- `documents`

Contents:
- Cleaned text
- Translations
- Extracted summaries
- Structured JSON representations

This layer exists so embeddings can be regenerated without re-fetching raw content.

---

### 2.4 Embeddings (PostgreSQL + pgvector)
Stored in:
- `document_embeddings`

Current standard:
- Model: **OpenAI `text-embedding-3-small`**
- Dimensions: **1536**
- Index: **HNSW cosine similarity**

Embeddings are derived data and may be re-generated at any time.

---

## 3. Retention Policy

### 3.1 Default Retention
- **Raw artifacts:** 120 days
- **Normalized facts:** retained indefinitely
- **Documents + embeddings:** retained indefinitely

### 3.2 Exceptions
- **Receipts / financial records:** retained indefinitely
- **Pinned sources:** retained indefinitely
- **Sources referenced by itinerary decisions:** retained beyond 120 days

### 3.3 Cleanup Strategy
- Cleanup jobs should remove raw artifacts **only if**:
  - They exceed 120 days
  - They are not pinned
  - They are not referenced by active documents or events

Only hashes + metadata may remain after cleanup.

---

## 4. Ingestion Contract (Transport-Agnostic)

Shogun defines *what happens when data arrives*, not *how it arrives*.

### 4.1 Ingestion Steps
1. Write raw artifact to disk
2. Insert or update `sources`
3. Create an `ingestion_runs` record
4. Normalize into domain tables (`trip_events`, `documents`, etc.)
5. Optionally embed content asynchronously

### 4.2 Ingestion Sources (Examples)
- Calendar (ICS)
- Email
- Telegram messages
- Web URLs
- Manual uploads

### 4.3 Manual Entry Is First-Class
Shogun supports creating trip facts without any external artifact (early itinerary planning).

**Policy:** Manual entry should still create an `ingestion_runs` row for auditability.
- `ingestion_runs.kind`: `manual_entry` (or `manual_upload`)
- `ingestion_runs.source_id`: may be NULL if no artifact exists

Manual-created facts should be stored in the same domain tables as imported facts (especially `trip_events`).

**Recommendation:** Use `trip_events.provider = 'manual'` and track status in `trip_events.metadata`.

Suggested `trip_events.metadata` conventions:
- `status`: `tentative` | `confirmed` | `cancelled`
- `confidence`: numeric 0–1 (optional)
- `source`: `manual` | `ics` | `email` | `telegram` | `web`

Transport mechanisms (web UI, email forwarding, bots) are out of scope for this policy.

---

## 5. Privacy Model

### 5.1 Defaults
- All user-specific data is **private by default**
- Shared trip data is explicitly marked non-private

### 5.2 Enforcement
- `documents.is_private = true` → visible only to `owner_user_id`
- `documents.is_private = false` → visible to trip members

### 5.3 Organizer Override (Family Mode)
- Trips may designate one or more **Organizers** (trip-scoped admins)
- Organizers can manage shared trip data and trip membership
- Users may opt-in to share private data with Organizers
- Default for family trips: sharing enabled

Recommended trip role semantics (stored in `trip_members.role`):
- `organizer` — trip admin (multiple allowed)
- `member` — standard trip participant

MVP3+ enforcement targets:
- Trip creator becomes an `organizer` automatically.
- A trip must always have at least 1 organizer (prevent lockout).

This avoids friction while preserving intent and auditability.

---

## 6. Chunking & Embedding Strategy

### 6.1 Canonical Rule
- **Chunk-level embeddings** for retrieval quality
- **Document-level text retained** for audit and reprocessing

### 6.2 Implications
- Chunk boundaries may change over time
- Re-embedding should not require re-scraping
- Embeddings are never treated as source-of-truth

---

## 7. Roles & Responsibilities

### Root / Infra
- Disk provisioning
- Mount points
- OS packages

### Postgres / Data Plane
- Owns `/srv/shogun`
- Writes raw artifacts
- Performs normalization

### DBA / Agent Roles
- No filesystem mutation
- Controlled DB access only

---

## 8. Non-Goals (Explicitly Out of Scope)

- User-facing upload UI
- Authentication mechanisms
- Telegram or web ingestion logic
- Scheduling or automation

These belong to later MVPs.

---

## 9. Change Control

Any changes to:
- retention duration
- embedding model/dimensions
- privacy defaults

**must update this document**.

---

**This document is the canonical policy reference for Shogun data handling.**


---

## Storage & Permissions (Authoritative)

### Purpose
Provide a durable, low-risk home for Shogun raw artifacts (ICS, email, web snapshots, receipts) without bloating Postgres or risking root filesystem exhaustion.

### Mount
- **Path:** `/srv/shogun`
- **Backing:** Dedicated Proxmox LXC mount point
- **Size:** 128 GB
- **Filesystem:** ext4
- **Persistence:** Managed by Proxmox (no fstab inside container)

### Ownership & Permissions
- `/srv/shogun` — owned by `postgres:postgres`, mode `755`
- `/srv/shogun/raw` and all subdirectories — owned by `postgres:postgres`, mode `750`

```text
/srv/shogun/raw/
├── ics/        # calendar imports (ICS)
├── email/      # raw email bodies / attachments
├── web/        # fetched web pages / snapshots
└── receipts/   # images / PDFs of receipts
```

Postgres must be able to write directly to all subdirectories **without sudo**. This has been validated via write tests.

### Data Placement Policy
- **Disk:** Raw artifacts only (files, images, PDFs, HTML, ICS)
- **Postgres:** Metadata, hashes, pointers (content_uri), normalized records, embeddings
- Large blobs must never be stored directly in Postgres tables.

### Retention Policy (MVP2 Baseline)
- Default raw artifact retention: **120 days**
- Receipts may be retained longer if explicitly pinned
- Retention enforcement handled by scheduled cleanup (future work)

### Operational Notes
- Do **not** recursively `chown` filesystem roots containing `lost+found`
- Do **not** mount raw storage on `/` or `/var`
- All ingestion services must target `/srv/shogun/raw/*`

This storage layout is considered **final for MVP2** and should not be modified without updating this document.

---

## Knowledge Ingestion Lifecycle (Policy)

This section defines **what happens when knowledge enters Shogun**, independent of transport (web, email, Telegram, manual entry).

### Goals
- Preserve provenance and auditability
- Avoid duplicate or stale knowledge
- Support both human planning and AI retrieval
- Keep Postgres lean; store large blobs on disk

---

### 1. Raw Artifact Capture
**Definition:** Any unprocessed external or user-provided data.

- Stored on disk under `/srv/shogun/raw/{ics,email,web,receipts}`
- Examples:
  - ICS calendar files
  - Email bodies / attachments
  - HTML snapshots
  - Images / PDFs

**Rules:**
- Raw artifacts are immutable once written
- Filenames may be content-hash based or timestamped
- Postgres stores only pointers (`content_uri`) and hashes

---

### 2. Source Registration (`sources`)
Each unique external origin is represented once.

**When to create/update:**
- First time a source is seen
- When fetched content hash changes

**Key fields:**
- `source_type` (web, reddit, google_places, calendar, email, manual)
- `source_key` (URL, provider ID, message ID, etc.)
- `raw_hash` (used for change detection)
- `content_uri` (points to raw artifact on disk)

**Policy:**
- If `raw_hash` unchanged → do not reprocess
- If `raw_hash` changed → create new ingestion run

---

### 3. Ingestion Run (`ingestion_runs`)
Tracks *how and when* processing occurred.

**Created for:**
- Every import attempt (including manual entry)

**Fields of note:**
- `kind`: `ics`, `email`, `web`, `manual_entry`
- `status`: `ok` or `error`
- `notes`: parser or validation details

**Policy:**
- Never update ingestion runs after creation
- Errors are recorded, not hidden

---

### 4. Normalization (`documents`, `trip_events`, etc.)
Raw content is converted into structured domain data.

Examples:
- ICS → `trip_events`
- Email confirmation → `trip_events` + `lodging_details`
- Web review → `documents`

**Rules:**
- All normalized records reference the originating `ingestion_runs`
- Manual entries are treated the same as imported data

---

### 5. Document Canonicalization (`documents`)
Documents represent **semantic knowledge units**.

**Characteristics:**
- Trip-scoped
- May be shared or private
- Store cleaned text and structured JSON

**Policy:**
- Documents may be updated if source content changes
- Updates should preserve prior versions when feasible (future work)

---

### 6. Embedding (`document_embeddings`)
Documents may be embedded for semantic search.

**Current standard:**
- Model: `text-embedding-3-small`
- Dimensions: `1536`

**Rules:**
- Embeddings are regenerated only when document content changes
- Multiple models per document may coexist

---

### 7. Retention & Cleanup

**Baseline (MVP2):**
- Raw artifacts retained **120 days** by default
- Receipts may be pinned for longer retention
- Sources and documents persist beyond raw retention

**Future work:**
- Scheduled cleanup jobs
- Pinning / archival flags

---

### Design Principles (Non-Negotiable)
- Transport-agnostic ingestion
- Disk for blobs, DB for meaning
- Auditability over convenience
- Manual data is first-class

This lifecycle is considered **authoritative** for Shogun MVP2+.
