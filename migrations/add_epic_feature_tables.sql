-- Migration: Add Epics and Features Tables
-- Description: Adds tables for Epics and Features hierarchy
-- Created: 2026-01-07

-- 1. Table: epics
CREATE TABLE IF NOT EXISTS epics (
    id VARCHAR(36) PRIMARY KEY,
    project_key VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'DRAFT',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for epics
CREATE INDEX IF NOT EXISTS idx_epics_project ON epics(project_key);

-- 2. Table: features
CREATE TABLE IF NOT EXISTS features (
    id VARCHAR(36) PRIMARY KEY,
    project_key VARCHAR(50) NOT NULL,
    epic_id VARCHAR(36),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'DRAFT',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (epic_id) REFERENCES epics(id) ON DELETE SET NULL
);

-- Indexes for features
CREATE INDEX IF NOT EXISTS idx_features_project ON features(project_key);
CREATE INDEX IF NOT EXISTS idx_features_epic ON features(epic_id);
