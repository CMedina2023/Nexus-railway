-- Rollback: Remove Traceability Columns from TestCase
-- Description: Removes requirement_id, requirement_version, and coverage_status from test_cases table
-- Note: SQLite does not support DROP COLUMN in older versions. 
-- For modern SQLite (3.35.0+): ALTER TABLE test_cases DROP COLUMN requirement_id; etc.

-- If using an older version, a table recreation would be needed. 
-- For now, providing the modern syntax.

ALTER TABLE test_cases DROP COLUMN requirement_id;
ALTER TABLE test_cases DROP COLUMN requirement_version;
ALTER TABLE test_cases DROP COLUMN coverage_status;
