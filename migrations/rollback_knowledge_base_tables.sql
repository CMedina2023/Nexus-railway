-- Rollback: Drop Knowledge Base Tables
-- Description: Removes tables created by add_knowledge_base_tables.sql

DROP TABLE IF EXISTS project_documents;
DROP TABLE IF EXISTS project_contexts;
