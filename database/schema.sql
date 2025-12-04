-- Short5 Platform Database Schema
-- PostgreSQL 14+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(30) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Videos Table
CREATE TYPE video_status AS ENUM ('uploading', 'processing', 'ready', 'failed', 'rejected');

CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    description TEXT,
    status video_status DEFAULT 'uploading',
    url_mp4 TEXT,
    thumbnail TEXT,
    duration_seconds INTEGER,
    file_size_bytes BIGINT,
    original_filename VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_videos_user_id ON videos(user_id);
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_created_at ON videos(created_at DESC);

-- Votes/Swipes Table (Likes and Not-Likes)
CREATE TYPE vote_direction AS ENUM ('like', 'not_like');

CREATE TABLE votes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    direction vote_direction NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, video_id)
);

CREATE INDEX idx_votes_user_id ON votes(user_id);
CREATE INDEX idx_votes_video_id ON votes(video_id);
CREATE INDEX idx_votes_direction ON votes(direction);
CREATE INDEX idx_votes_user_direction ON votes(user_id, direction);

-- User Liked Videos (Saved List)
CREATE TABLE user_liked_videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, video_id)
);

CREATE INDEX idx_user_liked_videos_user_id ON user_liked_videos(user_id);
CREATE INDEX idx_user_liked_videos_video_id ON user_liked_videos(video_id);

-- Views Table
CREATE TABLE views (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    watched_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_views_video_id ON views(video_id);
CREATE INDEX idx_views_user_id ON views(user_id);
CREATE INDEX idx_views_created_at ON views(created_at);

-- Reports Table (for moderation)
CREATE TYPE report_type AS ENUM ('video', 'user');
CREATE TYPE report_status AS ENUM ('pending', 'resolved', 'dismissed');

CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reporter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    report_type report_type NOT NULL,
    target_id UUID NOT NULL, -- video_id or user_id
    reason TEXT,
    status report_status DEFAULT 'pending',
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_type_target ON reports(report_type, target_id);
CREATE INDEX idx_reports_reporter_id ON reports(reporter_id);

-- Refresh Tokens (for JWT auth)
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_videos_updated_at BEFORE UPDATE ON videos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_views_updated_at BEFORE UPDATE ON views
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Materialized View for Video Stats (for performance)
CREATE MATERIALIZED VIEW video_stats AS
SELECT 
    v.id as video_id,
    COUNT(DISTINCT CASE WHEN vo.direction = 'like' THEN vo.id END) as likes_count,
    COUNT(DISTINCT CASE WHEN vo.direction = 'not_like' THEN vo.id END) as not_likes_count,
    COUNT(DISTINCT vi.id) as views_count,
    COALESCE(SUM(vi.watched_seconds), 0) as total_watched_seconds,
    COALESCE(AVG(vi.watched_seconds), 0) as avg_watched_seconds
FROM videos v
LEFT JOIN votes vo ON v.id = vo.video_id
LEFT JOIN views vi ON v.id = vi.video_id
WHERE v.status = 'ready'
GROUP BY v.id;

CREATE UNIQUE INDEX idx_video_stats_video_id ON video_stats(video_id);

-- Refresh stats view periodically (run via cron or application)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY video_stats;

