-- Add approval workflow fields to test_cases table
-- Created at: 2026-01-07

-- Note: Execute these statements one by one if your DB client doesn't support multiple statements.

-- 1. Add approval_status (default 'pending')
ALTER TABLE test_cases ADD COLUMN approval_status VARCHAR(20) DEFAULT 'pending';

-- 2. Add approved_by (User ID)
ALTER TABLE test_cases ADD COLUMN approved_by INTEGER;

-- 3. Add approved_at (Timestamp)
-- SQLite uses TEXT, Postgres uses TIMESTAMP. Adjust type accordingly if running manually.
-- For this file we use generic syntax or multiple versions.
-- Below is a generic attempt, but usually run via app logic.

-- ALTER TABLE test_cases ADD COLUMN approved_at TIMESTAMP; 
