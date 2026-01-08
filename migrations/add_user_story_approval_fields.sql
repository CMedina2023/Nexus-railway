-- Add approval workflow fields to user_stories table
-- Created at: 2026-01-08

-- Note: Execute these statements one by one if your DB client doesn't support multiple statements.

-- 1. Add approval_status (default 'pending')
ALTER TABLE user_stories ADD COLUMN approval_status VARCHAR(20) DEFAULT 'pending';

-- 2. Add approved_by (User ID)
ALTER TABLE user_stories ADD COLUMN approved_by INTEGER;

-- 3. Add approved_at (Timestamp)
ALTER TABLE user_stories ADD COLUMN approved_at TIMESTAMP; 
