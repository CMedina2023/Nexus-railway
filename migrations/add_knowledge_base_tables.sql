-- Migration: Add Knowledge Base Tables
-- Description: Adds tables for ProjectContext (Project Brain) and ProjectDocument (Files)
-- Created: 2026-01-06

-- 1. Table: project_contexts
-- Stores the high-level understanding of the project (The Brain)
CREATE TABLE IF NOT EXISTS project_contexts (
    id VARCHAR(36) PRIMARY KEY, -- UUID
    project_key VARCHAR(50) NOT NULL,
    summary TEXT,
    glossary TEXT, -- Stored as JSON string (SQLite) or JSONB (Postgres)
    business_rules TEXT, -- Stored as JSON string (SQLite) or JSONB (Postgres)
    tech_constraints TEXT, -- Stored as JSON string (SQLite) or JSONB (Postgres)
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookup by project
CREATE INDEX IF NOT EXISTS idx_project_contexts_key ON project_contexts(project_key);

-- 2. Table: project_documents
-- Stores metadata of files uploaded to the Knowledge Base
CREATE TABLE IF NOT EXISTS project_documents (
    id VARCHAR(36) PRIMARY KEY, -- UUID
    project_key VARCHAR(50) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_type VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending', -- pending, processed, error, archived
    content_hash VARCHAR(64), -- SHA256 for deduplication
    extracted_summary TEXT,
    error_message TEXT,
    upload_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_project_documents_key ON project_documents(project_key);
CREATE INDEX IF NOT EXISTS idx_project_documents_hash ON project_documents(content_hash);
