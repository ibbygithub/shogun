-- Migration: wishlist_items table for shogun-web
-- Run on dbnode-01 as dba-agent
-- psql -U dba-agent -d shogun_v1 -f 20260313_wishlist_items.sql

CREATE TABLE IF NOT EXISTS wishlist_items (
    id              SERIAL PRIMARY KEY,
    requested_by    INTEGER NOT NULL REFERENCES users(id),
    city            TEXT,
    description     TEXT NOT NULL,
    ai_research     TEXT,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by     INTEGER REFERENCES users(id),
    reviewed_at     TIMESTAMPTZ,
    itinerary_note  TEXT,
    created_utc     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_wishlist_status       ON wishlist_items(status);
CREATE INDEX IF NOT EXISTS idx_wishlist_requested_by ON wishlist_items(requested_by);
