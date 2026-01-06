-- Migration: Add Traceability Tables
-- Description: Adds tables for Requirements, Traceability Links, and Coverage Stats
-- Created: 2026-01-06

-- 1. Table: requirements
-- Stores functional and non-functional requirements
CREATE TABLE IF NOT EXISTS requirements (
    id VARCHAR(36) PRIMARY KEY, -- UUID
    project_id VARCHAR(50) NOT NULL, -- Logical ID/Key of the project
    code VARCHAR(50) NOT NULL, -- e.g. REQ-001
    title VARCHAR(200) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL, -- FUNCTIONAL, NON_FUNCTIONAL, etc.
    priority VARCHAR(20) NOT NULL, -- CRITICAL, HIGH, etc.
    status VARCHAR(20) DEFAULT 'DRAFT',
    source_document_id VARCHAR(36), -- Link to source file if extracted
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for requirements
CREATE INDEX IF NOT EXISTS idx_requirements_project ON requirements(project_id);
CREATE INDEX IF NOT EXISTS idx_requirements_code ON requirements(code);

-- 2. Table: traceability_links
-- Stores polymorphic links between artifacts (Req <-> Story, Req <-> Test)
CREATE TABLE IF NOT EXISTS traceability_links (
    id VARCHAR(36) PRIMARY KEY, -- UUID
    source_id VARCHAR(36) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- REQUIREMENT, USER_STORY, TEST_CASE
    target_id VARCHAR(36) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    link_type VARCHAR(50) NOT NULL, -- VERIFIES, IMPLEMENTS, etc.
    created_by INTEGER, -- User ID
    meta TEXT, -- JSON metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for traceability links (bidirectional lookup)
CREATE INDEX IF NOT EXISTS idx_traceability_source ON traceability_links(source_id, source_type);
CREATE INDEX IF NOT EXISTS idx_traceability_target ON traceability_links(target_id, target_type);

-- 3. Table: requirement_coverages
-- Stores cached coverage statistics for requirements
CREATE TABLE IF NOT EXISTS requirement_coverages (
    id VARCHAR(36) PRIMARY KEY, -- UUID
    requirement_id VARCHAR(36) NOT NULL,
    test_count INTEGER DEFAULT 0,
    story_count INTEGER DEFAULT 0,
    coverage_score FLOAT DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'UNCOVERED',
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_req_coverage FOREIGN KEY (requirement_id) REFERENCES requirements(id) ON DELETE CASCADE
);

-- Index for coverage
CREATE INDEX IF NOT EXISTS idx_coverage_req_id ON requirement_coverages(requirement_id);
