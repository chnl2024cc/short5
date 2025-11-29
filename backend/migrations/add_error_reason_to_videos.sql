-- Migration: Add error_reason column to videos table
-- Run this migration to add error_reason field for storing failure messages

ALTER TABLE videos ADD COLUMN IF NOT EXISTS error_reason TEXT;

-- Add comment to document the field
COMMENT ON COLUMN videos.error_reason IS 'Stores user-friendly error message when video processing fails';
