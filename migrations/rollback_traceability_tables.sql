-- Rollback: Drop Traceability Tables
-- Description: Removes tables created by add_traceability_tables.sql

DROP TABLE IF EXISTS requirement_coverages;
DROP TABLE IF EXISTS traceability_links;
DROP TABLE IF EXISTS requirements;
