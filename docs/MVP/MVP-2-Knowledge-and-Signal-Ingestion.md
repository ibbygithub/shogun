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
