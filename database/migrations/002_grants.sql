-- ============================================================
-- Migration: 002_grants.sql
-- Database:  shogun_v1 (dbnode-01)
-- Schema:    public
-- Persona:   dba-agent
--
-- Grants for shogun_app on brainnode-01.
-- NOTE: Run AFTER 002a_create_app_user.sql and 001_initial_schema.sql.
-- ============================================================

GRANT CONNECT ON DATABASE shogun_v1 TO shogun_app;
GRANT USAGE   ON SCHEMA   public    TO shogun_app;

-- Full CRUD on the four new Shogun MVP tables
GRANT SELECT, INSERT, UPDATE, DELETE
    ON users, user_preferences, trip_itinerary, trip_pois
    TO shogun_app;

-- Sequence access (required for SERIAL inserts)
GRANT USAGE, SELECT
    ON SEQUENCE users_id_seq,
               user_preferences_id_seq,
               trip_itinerary_id_seq,
               trip_pois_id_seq
    TO shogun_app;
