-- ============================================================
-- Migration: 002_grants.sql
-- Database:  shogun_v1 (dbnode-01)
-- Schema:    public
-- Persona:   dba-agent
--
-- Grants for the shogun application user on brainnode-01.
-- NOTE: Run AFTER 001_initial_schema.sql.
--
-- App user is TBD — must be confirmed before running.
-- Check existing roles with:
--   sudo -u postgres psql -d shogun_v1 -c "\du"
--
-- Candidate: create 'shogun_app' if no suitable role exists.
-- See 002a_create_app_user.sql for user creation if needed.
-- ============================================================

-- Replace :shogun_app_user with the confirmed role name before running.
-- e.g. if role is 'shogun_app': \set shogun_app_user shogun_app

\set shogun_app_user shogun_app

GRANT CONNECT ON DATABASE shogun_v1 TO :shogun_app_user;
GRANT USAGE   ON SCHEMA   public    TO :shogun_app_user;

-- Application needs full CRUD on all shogun tables
GRANT SELECT, INSERT, UPDATE, DELETE
    ON users, user_preferences, trip_itinerary, trip_pois
    TO :shogun_app_user;

-- Grant access to sequences (needed for SERIAL columns on INSERT)
GRANT USAGE, SELECT
    ON SEQUENCE users_id_seq,
               user_preferences_id_seq,
               trip_itinerary_id_seq,
               trip_pois_id_seq
    TO :shogun_app_user;
