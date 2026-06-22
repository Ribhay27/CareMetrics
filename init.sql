-- =============================================================
-- Hospital Analytics Pipeline — Database Initialization
-- Runs automatically on first PostgreSQL container start
-- =============================================================

-- ─────────────────────────────────────────────────────────────
-- 1. Schema creation
-- ─────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS marts;

-- ─────────────────────────────────────────────────────────────
-- 2. Privileges
--    The POSTGRES_USER set in .env owns the DB, so we grant
--    that same user full rights on every schema explicitly.
-- ─────────────────────────────────────────────────────────────

DO $$
DECLARE
    db_owner TEXT;
BEGIN
    SELECT current_user INTO db_owner;

    EXECUTE format('GRANT ALL PRIVILEGES ON SCHEMA raw          TO %I', db_owner);
    EXECUTE format('GRANT ALL PRIVILEGES ON SCHEMA staging       TO %I', db_owner);
    EXECUTE format('GRANT ALL PRIVILEGES ON SCHEMA intermediate  TO %I', db_owner);
    EXECUTE format('GRANT ALL PRIVILEGES ON SCHEMA marts         TO %I', db_owner);

    EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA raw          GRANT ALL ON TABLES TO %I', db_owner);
    EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA staging       GRANT ALL ON TABLES TO %I', db_owner);
    EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA intermediate  GRANT ALL ON TABLES TO %I', db_owner);
    EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA marts         GRANT ALL ON TABLES TO %I', db_owner);
END $$;

-- ─────────────────────────────────────────────────────────────
-- 3. Pipeline run log table
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS raw.hospital_pipeline_runs (
    run_id          SERIAL          PRIMARY KEY,
    pipeline_name   VARCHAR(255)    NOT NULL,
    dag_id          VARCHAR(255),
    run_type        VARCHAR(50)     NOT NULL DEFAULT 'manual',
    status          VARCHAR(50)     NOT NULL DEFAULT 'running',
                                    -- running | success | failed | skipped
    started_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    duration_secs   NUMERIC(10, 2)  GENERATED ALWAYS AS (
                        EXTRACT(EPOCH FROM (completed_at - started_at))
                    ) STORED,
    rows_processed  BIGINT,
    error_message   TEXT,
    metadata        JSONB           DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status
    ON raw.hospital_pipeline_runs (status);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_pipeline_name
    ON raw.hospital_pipeline_runs (pipeline_name);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started_at
    ON raw.hospital_pipeline_runs (started_at DESC);

-- ─────────────────────────────────────────────────────────────
-- 4. Confirmation notice
-- ─────────────────────────────────────────────────────────────

DO $$
BEGIN
    RAISE NOTICE '======================================================';
    RAISE NOTICE 'Hospital Analytics Pipeline DB initialized successfully';
    RAISE NOTICE 'Schemas created: raw, staging, intermediate, marts';
    RAISE NOTICE 'Log table: raw.hospital_pipeline_runs';
    RAISE NOTICE '======================================================';
END $$;
