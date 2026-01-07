-- Migration: Add Traceability Columns to TestCase
-- Description: Adds requirement_id, requirement_version, and coverage_status to test_cases table
-- Created: 2026-01-06

ALTER TABLE test_cases ADD COLUMN requirement_id VARCHAR(36);
ALTER TABLE test_cases ADD COLUMN requirement_version VARCHAR(20);
ALTER TABLE test_cases ADD COLUMN coverage_status VARCHAR(20);

-- Index for traceability lookups
CREATE INDEX IF NOT EXISTS idx_test_cases_requirement ON test_cases(requirement_id);
