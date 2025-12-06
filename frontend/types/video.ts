/**
 * Video Types
 * Based on backend schemas
 */

export type VideoStatus = 'uploading' | 'processing' | 'ready' | 'failed' | 'rejected'

export interface VideoUser {
  id: string
  username: string
}

export interface VideoStats {
  likes: number
  not_likes: number
  views: number
}

export interface Video {
  id: string
  title?: string
  description?: string
  status: VideoStatus
  thumbnail: string // Required - fail fast if missing
  url_mp4: string // Required - fail fast if missing
  duration_seconds?: number | null
  error_reason?: string | null
  user: VideoUser
  stats: VideoStats
  created_at: string // ISO datetime string
}

export interface FeedResponse {
  videos: Video[]
  next_cursor: string | null
  has_more: boolean
}

