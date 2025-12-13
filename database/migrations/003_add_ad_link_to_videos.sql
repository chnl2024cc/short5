-- Migration: 003_add_ad_link_to_videos.sql
-- Description: Add ad_link field to videos table for affiliate/sponsored content

BEGIN;

ALTER TABLE videos 
ADD COLUMN IF NOT EXISTS ad_link TEXT;

-- Add index for querying videos with ad links (optional, for analytics)
CREATE INDEX IF NOT EXISTS idx_videos_ad_link ON videos(ad_link) WHERE ad_link IS NOT NULL;

COMMIT;

