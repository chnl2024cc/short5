-- Migration: 000_migration_tracking.sql
-- Description: Create migration tracking table
-- Run this FIRST before any other migrations
-- 
-- This table tracks which migrations have been applied to prevent duplicate runs

BEGIN;

-- Migration tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    checksum VARCHAR(64), -- Optional: SHA256 hash of migration file for verification
    execution_time_ms INTEGER -- Optional: track how long migration took
);

CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at ON schema_migrations(applied_at DESC);

COMMIT;

