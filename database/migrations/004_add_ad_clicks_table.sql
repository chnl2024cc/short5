-- Migration: 004_add_ad_clicks_table.sql
-- Description: Create ad_clicks table for tracking ad video link clicks

BEGIN;

CREATE TABLE IF NOT EXISTS ad_clicks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    clicker_session_id UUID,  -- Nullable for anonymous users
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- Nullable for anonymous clicks
    clicked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ad_clicks_video_id ON ad_clicks(video_id);
CREATE INDEX IF NOT EXISTS idx_ad_clicks_clicker_session_id ON ad_clicks(clicker_session_id) WHERE clicker_session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ad_clicks_user_id ON ad_clicks(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ad_clicks_clicked_at ON ad_clicks(clicked_at);

COMMIT;

