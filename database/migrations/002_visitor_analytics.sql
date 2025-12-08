-- Migration: 002_visitor_analytics.sql
-- Description: Visitor analytics tracking table (MVP)
-- Run after initial schema (001_initial_schema.sql)
-- 
-- This migration is idempotent - safe to run multiple times

BEGIN;

-- Ensure UUID extension exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Visitor Logs Table (MVP - Minimal Implementation)
CREATE TABLE IF NOT EXISTS visitor_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Session/User Identification
    session_id UUID NOT NULL, -- Anonymous session or user session
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- NULL for anonymous users
    
    -- Request Information (Core)
    url TEXT NOT NULL, -- The URL/page visited
    ip_address INET, -- IP address (used for GeoIP lookup)
    user_agent TEXT, -- User agent string
    
    -- Geographic Information (Core)
    country VARCHAR(2), -- ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB')
    country_name VARCHAR(100), -- Full country name
    city VARCHAR(100), -- City name
    latitude DECIMAL(10, 8), -- Latitude coordinate
    longitude DECIMAL(11, 8), -- Longitude coordinate
    
    -- Timestamps
    visited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Essential indexes only (MVP)
CREATE INDEX IF NOT EXISTS idx_visitor_logs_visited_at ON visitor_logs(visited_at DESC);
CREATE INDEX IF NOT EXISTS idx_visitor_logs_url ON visitor_logs(url);
CREATE INDEX IF NOT EXISTS idx_visitor_logs_country ON visitor_logs(country);
CREATE INDEX IF NOT EXISTS idx_visitor_logs_coordinates ON visitor_logs(latitude, longitude) WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

COMMIT;

