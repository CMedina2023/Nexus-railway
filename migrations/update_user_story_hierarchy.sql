-- Migration: Update User Story Hierarchy
-- Description: Adds hierarchy fields to user_stories table
-- Created: 2026-01-07

-- Note: Checks for column existence are not standard in standard SQL for ADD COLUMN,
-- so we rely on the application keying track of migrations or manual execution.

ALTER TABLE user_stories ADD COLUMN requirement_id TEXT;
ALTER TABLE user_stories ADD COLUMN epic_id TEXT;
ALTER TABLE user_stories ADD COLUMN feature_id TEXT;
ALTER TABLE user_stories ADD COLUMN parent_story_id INTEGER REFERENCES user_stories(id);
ALTER TABLE user_stories ADD COLUMN dependencies TEXT;
