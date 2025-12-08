-- Short5 Platform Database Schema
-- PostgreSQL 14+
--
-- PURPOSE:
-- This file is a CONVENIENCE WRAPPER for fresh database initialization.
-- It references the migration files which are the SINGLE SOURCE OF TRUTH.
--
-- USAGE:
-- - For fresh database setup: This file can be used (if migrations are accessible)
-- - For existing databases: Use individual migration files in database/migrations/
-- - For production: Use the migration runner (database/migrations/run_migrations.py)
--
-- NOTE: The actual schema definitions are in database/migrations/ directory.
--       This file should be kept in sync with migrations, or better yet,
--       use the migration runner for all database setup.
--
-- IMPORTANT: If running this file directly, ensure the migrations/ directory
--            is accessible relative to this file's location.

-- Run migrations in order
-- Note: For Docker init, migrations are mounted at /docker-entrypoint-initdb.d/migrations/
\i /docker-entrypoint-initdb.d/migrations/000_migration_tracking.sql
\i /docker-entrypoint-initdb.d/migrations/001_initial_schema.sql
\i /docker-entrypoint-initdb.d/migrations/002_visitor_analytics.sql
