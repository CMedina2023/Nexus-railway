-- Rollback: Drop Epics and Features Tables
-- Description: Removes tables created by add_epic_feature_tables.sql

DROP TABLE IF EXISTS features;
DROP TABLE IF EXISTS epics;
