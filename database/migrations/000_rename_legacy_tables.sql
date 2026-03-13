-- ============================================================
-- Migration: 000_rename_legacy_tables.sql
-- Database:  shogun_v1 (dbnode-01, 192.168.71.221)
-- Schema:    public
-- Persona:   dba-agent
-- Run BEFORE: 001_initial_schema.sql
--
-- Option B — Preserve old schema alongside new Shogun MVP schema.
--
-- Context: shogun_v1 contains 17 tables from a prior web-based
-- version of the project (email/password auth, surveys, expenses,
-- trip planning). These are not part of the current MVP design.
--
-- Only ONE table has a naming conflict: "users".
-- The old users table has 0 rows and a web-app schema.
-- Renaming it to users_v1_legacy clears the way for the new
-- Telegram-first users table without touching any other tables.
--
-- Existing FK constraints from other old tables (activities,
-- documents, expenses, survey_votes, surveys, trip_members) that
-- reference users will continue to work after the rename — Postgres
-- FK constraints resolve by OID internally, not by table name.
--
-- Rollback: ALTER TABLE users_v1_legacy RENAME TO users;
-- ============================================================

ALTER TABLE users RENAME TO users_v1_legacy;

COMMENT ON TABLE users_v1_legacy IS
  'Legacy shogun v1 web-app users table — preserved 2026-03-12, superseded by new users table (Telegram-first schema)';
