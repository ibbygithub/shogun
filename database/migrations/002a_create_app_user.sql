-- ============================================================
-- Migration: 002a_create_app_user.sql
-- Database:  shogun_v1 (dbnode-01)
-- Persona:   dba-agent
--
-- Creates the shogun_app role if it does not already exist.
-- Run BEFORE 002_grants.sql if 'shogun_app' does not exist.
--
-- Check first: sudo -u postgres psql -c "\du" | grep shogun
-- If shogun_app already exists — skip this file.
-- ============================================================

-- No password set here — shogun_app connects from brainnode-01
-- via peer auth or local trust. Password needed only if TCP auth required.
-- Confirm connection method before deploying shogun-core.

CREATE ROLE shogun_app
    WITH LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    CONNECTION LIMIT 10;

COMMENT ON ROLE shogun_app IS 'shogun-core application user on brainnode-01';
