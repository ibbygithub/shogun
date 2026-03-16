-- ============================================================
-- Migration: 001_initial_schema.sql
-- Database:  shogun_v1 (dbnode-01, 192.168.71.221)
-- Schema:    public
-- Persona:   dba-agent
--
-- Creates 4 tables for the Shogun Japan trip concierge:
--   users             — Telegram users with notification state
--   user_preferences  — Dietary, shopping, entertainment preferences (trip-long)
--   trip_itinerary    — Flights, accommodation, activities, transit
--   trip_pois         — Points of interest by city with crowd intelligence
--
-- Rollback: See section at end of file.
-- ============================================================

BEGIN;

-- ── users ────────────────────────────────────────────────────────────────────
-- One row per Telegram user. Identified by telegram_user_id (Telegram's stable
-- numeric ID, not display name which can change).
-- notification_active controls whether Shogun sends unsolicited location-based
-- messages to this user. Toggleable per user via /quiet and /active commands.

CREATE TABLE users (
    id                  SERIAL          PRIMARY KEY,
    telegram_user_id    BIGINT          NOT NULL UNIQUE,
    display_name        TEXT            NOT NULL,           -- short name Shogun uses in responses
    full_name           TEXT,                               -- optional formal name
    notification_active BOOLEAN         NOT NULL DEFAULT true,
    language_preference TEXT            NOT NULL DEFAULT 'en',
    created_utc         TIMESTAMPTZ     NOT NULL DEFAULT now()
);

COMMENT ON TABLE  users                     IS 'Telegram users registered with Shogun';
COMMENT ON COLUMN users.telegram_user_id    IS 'Stable Telegram numeric user ID (from bot update payload)';
COMMENT ON COLUMN users.notification_active IS 'If false, user receives no unsolicited location-triggered messages';


-- ── user_preferences ─────────────────────────────────────────────────────────
-- Key-value preference store per user and category. Trip-long constants.
-- Not stored in Valkey (would expire); lives here permanently across the trip.
--
-- category values:
--   dietary      — what they eat and restrictions (must-not-eat items)
--   likes        — positive preferences (cuisines, activities)
--   dislikes     — negative preferences (not hard restrictions)
--   shopping     — shopping interests by type
--   entertainment — activities, attractions, interests

CREATE TABLE user_preferences (
    id               SERIAL      PRIMARY KEY,
    user_id          INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category         TEXT        NOT NULL
                                 CHECK (category IN ('dietary', 'likes', 'dislikes', 'shopping', 'entertainment')),
    preference_key   TEXT        NOT NULL,  -- e.g. 'eats', 'avoids', 'interest_type'
    preference_value TEXT        NOT NULL,  -- e.g. 'fish', 'red_meat_as_protein', 'vintage_cameras'
    notes            TEXT,                  -- freeform context from questionnaire
    created_utc      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_user_pref_user_id  ON user_preferences(user_id);
CREATE INDEX idx_user_pref_category ON user_preferences(user_id, category);

COMMENT ON TABLE  user_preferences                IS 'Trip-long user preferences: dietary, shopping, entertainment';
COMMENT ON COLUMN user_preferences.preference_key IS 'Preference dimension (e.g. eats, avoids, interest_type)';
COMMENT ON COLUMN user_preferences.notes          IS 'Freeform context from user questionnaire';


-- ── trip_itinerary ────────────────────────────────────────────────────────────
-- Full trip schedule: flights, accommodation check-in/check-out,
-- planned activities, and transit legs.
--
-- leg_type values:
--   flight        — JL7555, JL69, JL2
--   accommodation — airbnb/hotel check-in and check-out legs
--   activity      — USJ, Ghibli Museum, day trips
--   transit       — Osaka→Kanazawa→Tokyo transfers

CREATE TABLE trip_itinerary (
    id                  SERIAL      PRIMARY KEY,
    leg_sequence        INTEGER     NOT NULL,   -- ordering key; gaps allowed for inserts
    leg_type            TEXT        NOT NULL
                                    CHECK (leg_type IN ('flight', 'accommodation', 'activity', 'transit')),
    date_local          DATE        NOT NULL,   -- local date at the destination
    city                TEXT        NOT NULL,   -- Osaka, Nara, Kyoto, Kanazawa, Tokyo, Sakai, etc.
    title               TEXT        NOT NULL,   -- human-readable leg description
    address_en          TEXT,
    address_ja          TEXT,
    contact_phone       TEXT,
    confirmation_number TEXT,
    notes_en            TEXT,
    notes_ja            TEXT,
    start_time          TIME,                   -- local time; null if all-day
    end_time            TIME,
    created_utc         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_itinerary_date ON trip_itinerary(date_local);
CREATE INDEX idx_itinerary_city ON trip_itinerary(city);

COMMENT ON TABLE  trip_itinerary             IS 'Full trip schedule: flights, accommodation, activities, transit';
COMMENT ON COLUMN trip_itinerary.leg_sequence IS 'Explicit ordering; not auto-derived from date (flights cross midnight)';
COMMENT ON COLUMN trip_itinerary.date_local  IS 'Local date at destination, not UTC';


-- ── trip_pois ─────────────────────────────────────────────────────────────────
-- Points of interest by city. Pre-loaded before departure with Shogun-curated
-- context: crowd timing, Madeline-layer tags, shopping intelligence.
--
-- tags array examples:
--   ghibli, anime, knife, food, vintage-camera, shopping, crowd-warning,
--   madeline, brenda, todd, early-morning-only, retro-gaming

CREATE TABLE trip_pois (
    id              SERIAL          PRIMARY KEY,
    city            TEXT            NOT NULL,
    name_en         TEXT            NOT NULL,
    name_ja         TEXT,
    category        TEXT            NOT NULL,   -- restaurant, shrine, shopping, market, museum, park, etc.
    lat             NUMERIC(10, 7),
    lng             NUMERIC(10, 7),
    address_en      TEXT,
    address_ja      TEXT,
    tags            TEXT[]          NOT NULL DEFAULT '{}',
    crowd_notes     TEXT,                       -- e.g. "arrive before 9am, tour buses after 9:30"
    best_time_notes TEXT,                       -- e.g. "dawn only — gates never close"
    source          TEXT,                       -- 'manual', 'tavily', 'google_places', etc.
    created_utc     TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE INDEX idx_pois_city     ON trip_pois(city);
CREATE INDEX idx_pois_category ON trip_pois(category);
CREATE INDEX idx_pois_tags     ON trip_pois USING GIN(tags);

COMMENT ON TABLE  trip_pois            IS 'Points of interest by city with crowd intelligence and user-layer tags';
COMMENT ON COLUMN trip_pois.tags       IS 'Array of searchable tags: ghibli, anime, knife, madeline, early-morning-only, etc.';
COMMENT ON COLUMN trip_pois.source     IS 'How this POI was ingested: manual, tavily, google_places';

COMMIT;


-- ============================================================
-- ROLLBACK (execute as dba-agent if migration must be reversed)
-- Run each statement individually — do NOT wrap in a transaction
-- if data may already exist.
-- ============================================================
--
-- DROP TABLE IF EXISTS trip_pois         CASCADE;
-- DROP TABLE IF EXISTS trip_itinerary    CASCADE;
-- DROP TABLE IF EXISTS user_preferences  CASCADE;
-- DROP TABLE IF EXISTS users             CASCADE;
--
-- ============================================================
