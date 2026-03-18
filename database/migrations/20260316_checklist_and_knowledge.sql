-- Migration: checklist_items and knowledge_items tables
-- Database:  shogun_v1 (Docker Desktop: platform-postgres)
-- Schema:    public
-- Run:       docker exec platform-postgres bash -c "psql -U postgres -d shogun_v1 -f /tmp/migration.sql"
--
-- Purpose:
--   checklist_items — packing checklist with packed/unpacked state
--   knowledge_items — trip knowledge base for AI RAG search (local tips, restaurants, shops)
--
-- Note: knowledge_items was created by the seed script (tools/seed_tokyo_knowledge.py)
--   with a richer schema (anchor, source_url, tavily_score, raw_content, ingested_utc).
--   This migration creates checklist_items and ensures the knowledge_items indexes exist.
--   The CREATE TABLE IF NOT EXISTS for knowledge_items is a no-op when the table exists.
--
-- Rollback:
--   DROP TABLE IF EXISTS checklist_items CASCADE;

BEGIN;

-- ── checklist_items ───────────────────────────────────────────────────────────
-- Packing checklist for the Japan trip. Items can be toggled packed/unpacked.
-- category examples: documents, clothing, electronics, toiletries, misc

CREATE TABLE IF NOT EXISTS checklist_items (
    id          SERIAL      PRIMARY KEY,
    category    TEXT        NOT NULL DEFAULT 'misc',
    item_name   TEXT        NOT NULL,
    packed      BOOLEAN     NOT NULL DEFAULT false,
    notes       TEXT,
    created_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_checklist_category ON checklist_items(category);
CREATE INDEX IF NOT EXISTS idx_checklist_packed   ON checklist_items(packed);

COMMENT ON TABLE  checklist_items          IS 'Trip packing checklist — items with packed/unpacked state';
COMMENT ON COLUMN checklist_items.category IS 'Item category: documents, clothing, electronics, toiletries, misc';
COMMENT ON COLUMN checklist_items.packed   IS 'True when item has been packed';

-- Seed with common trip items (idempotent — skipped if rows already exist)
INSERT INTO checklist_items (category, item_name, packed) VALUES
    ('documents', 'Passport',              false),
    ('documents', 'Travel insurance docs', false),
    ('documents', 'JR Pass',               false),
    ('documents', 'Hotel confirmations',   false),
    ('documents', 'Yen cash',              false),
    ('electronics', 'Phone charger',       false),
    ('electronics', 'Power adapter (Type A)', false),
    ('electronics', 'Portable battery pack', false),
    ('electronics', 'Camera',              false),
    ('clothing', 'Walking shoes',          false),
    ('clothing', 'Rain jacket',            false),
    ('toiletries', 'Medications',          false),
    ('toiletries', 'Sunscreen',            false),
    ('misc', 'Luggage locks',              false),
    ('misc', 'Reusable bag',               false)
ON CONFLICT DO NOTHING;


-- ── knowledge_items ───────────────────────────────────────────────────────────
-- Trip knowledge base for AI-powered search.
-- Covers local tips, restaurants, vintage shops, temples, transit, etc.
-- Used by search_trip_knowledge tool in the chat AI.
--
-- Actual schema (created by tools/seed_tokyo_knowledge.py):
--   anchor, city, category, topic, source_url, content_summary,
--   raw_content, tavily_score, ingested_utc
--
-- This block is intentionally a no-op if table already exists — the seed script
-- owns the schema. Only add the standard search indexes if missing.

CREATE TABLE IF NOT EXISTS knowledge_items (
    id              SERIAL      PRIMARY KEY,
    anchor          TEXT,
    city            TEXT,
    category        TEXT,
    topic           TEXT,
    source_url      TEXT,
    content_summary TEXT,
    raw_content     TEXT,
    tavily_score    FLOAT,
    ingested_utc    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_city     ON knowledge_items(city);
CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_items(category);

COMMENT ON TABLE  knowledge_items                IS 'Trip knowledge base for AI RAG search — local tips, places, food';
COMMENT ON COLUMN knowledge_items.topic          IS 'Short searchable title for this knowledge item';
COMMENT ON COLUMN knowledge_items.content_summary IS 'AI-readable summary: 1-3 sentences of actionable knowledge';

COMMIT;
