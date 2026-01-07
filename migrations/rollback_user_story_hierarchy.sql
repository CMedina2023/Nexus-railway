-- Rollback: Update User Story Hierarchy
-- Description: Drops hierarchy fields from user_stories table
-- Created: 2026-01-07

ALTER TABLE user_stories DROP COLUMN requirement_id;
ALTER TABLE user_stories DROP COLUMN epic_id;
ALTER TABLE user_stories DROP COLUMN feature_id;
ALTER TABLE user_stories DROP COLUMN parent_story_id;
ALTER TABLE user_stories DROP COLUMN dependencies;
