/**
 * Videos Store (Pinia)
 */
import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'
import { useAuthStore } from './auth'
import type { Video, FeedResponse, PendingVote } from '~/types/video'

const PENDING_VOTES_KEY = 'pending_votes'

export const useVideosStore = defineStore('videos', {
  state: () => ({
    feed: [] as Video[],
    likedVideos: [] as Video[],
    currentCursor: null as string | null,
    hasMore: true,
  }),

  actions: {
    async fetchFeed(cursor?: string): Promise<FeedResponse> {
      const api = useApi()
      try {
        const response = await api.get<FeedResponse>(`/feed${cursor ? `?cursor=${cursor}` : ''}`)
        
        this.currentCursor = response.next_cursor
        this.hasMore = response.has_more
        
        if (cursor) {
          this.feed.push(...response.videos)
        } else {
          this.feed = response.videos
        }
        
        return response
      } catch (error) {
        console.error('Failed to fetch feed:', error)
        throw error
      }
    },

    async voteOnVideo(videoId: string, direction: 'like' | 'not_like') {
      const authStore = useAuthStore()
      
      // If user is authenticated, vote directly
      if (authStore.isAuthenticated) {
        const api = useApi()
        try {
          await api.post(`/videos/${videoId}/vote`, {
            direction,
          })
          return
        } catch (error) {
          console.error('Failed to vote on video:', error)
          throw error
        }
      }
      
      // If not authenticated, store vote in localStorage
      if (process.client) {
        const pendingVotes = this.getPendingVotes()
        // Check if already voted on this video
        const existingIndex = pendingVotes.findIndex(v => v.videoId === videoId)
        if (existingIndex >= 0) {
          // Update existing vote
          pendingVotes[existingIndex] = {
            videoId,
            direction,
            timestamp: Date.now(),
          }
        } else {
          // Add new vote
          pendingVotes.push({
            videoId,
            direction,
            timestamp: Date.now(),
          })
        }
        localStorage.setItem(PENDING_VOTES_KEY, JSON.stringify(pendingVotes))
        console.log('Vote stored locally, will sync when logged in')
      }
    },

    getPendingVotes(): PendingVote[] {
      if (!process.client) return []
      try {
        const stored = localStorage.getItem(PENDING_VOTES_KEY)
        return stored ? JSON.parse(stored) : []
      } catch {
        return []
      }
    },

    clearPendingVotes() {
      if (process.client) {
        localStorage.removeItem(PENDING_VOTES_KEY)
      }
    },

    async syncPendingVotes() {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        return
      }

      const pendingVotes = this.getPendingVotes()
      if (pendingVotes.length === 0) {
        return
      }

      const api = useApi()
      const synced: string[] = []
      const failed: PendingVote[] = []

      for (const vote of pendingVotes) {
        try {
          await api.post(`/videos/${vote.videoId}/vote`, {
            direction: vote.direction,
          })
          synced.push(vote.videoId)
        } catch (error: any) {
          console.error(`Failed to sync vote for video ${vote.videoId}:`, error)
          // If it's a conflict (already voted), that's fine - remove it
          // Check if error message contains "already voted" or "409"
          const errorMessage = error?.message || String(error) || ''
          if (errorMessage.includes('already voted') || errorMessage.includes('409') || errorMessage.includes('conflict')) {
            synced.push(vote.videoId)
          } else {
            failed.push(vote)
          }
        }
      }

      // Remove synced votes, keep failed ones for retry
      if (synced.length > 0) {
        const remaining = pendingVotes.filter(v => !synced.includes(v.videoId))
        if (process.client) {
          if (remaining.length > 0) {
            localStorage.setItem(PENDING_VOTES_KEY, JSON.stringify(remaining))
          } else {
            localStorage.removeItem(PENDING_VOTES_KEY)
          }
        }
      }

      if (synced.length > 0) {
        console.log(`Synced ${synced.length} pending vote(s)`)
      }
      if (failed.length > 0) {
        console.warn(`${failed.length} vote(s) failed to sync, will retry later`)
      }
    },

    async uploadVideo(file: File, title?: string, description?: string) {
      const authStore = useAuthStore()
      
      // Ensure auth store is initialized
      if (process.client && !authStore.token) {
        authStore.initFromStorage()
      }
      
      // Verify authentication before upload
      if (!authStore.isAuthenticated) {
        const token = process.client ? localStorage.getItem('token') : null
        if (!token) {
          throw new Error('You must be logged in to upload videos. Please log in and try again.')
        }
        // Update store with token from localStorage
        authStore.token = token
      }
      
      const api = useApi()
      try {
        const formData = new FormData()
        formData.append('file', file)
        if (title) formData.append('title', title)
        if (description) formData.append('description', description)
        
        const response = await api.post('/videos/upload', formData)
        return response
      } catch (error) {
        console.error('Failed to upload video:', error)
        throw error
      }
    },

    async fetchLikedVideos(cursor?: string): Promise<FeedResponse> {
      const authStore = useAuthStore()
      
      // If authenticated, fetch from API
      if (authStore.isAuthenticated) {
        const api = useApi()
        try {
          const response = await api.get<FeedResponse>(`/users/me/liked${cursor ? `?cursor=${cursor}` : ''}`)
          
          if (cursor) {
            this.likedVideos.push(...response.videos)
          } else {
            this.likedVideos = response.videos
          }
          
          return response
        } catch (error) {
          console.error('Failed to fetch liked videos:', error)
          throw error
        }
      }
      
      // If not authenticated, get liked videos from localStorage
      if (!process.client) {
        return { videos: [], next_cursor: null, has_more: false }
      }
      
      const pendingVotes = this.getPendingVotes()
      const likedVideoIds = pendingVotes
        .filter(vote => vote.direction === 'like')
        .map(vote => vote.videoId)
      
      if (likedVideoIds.length === 0) {
        return { videos: [], next_cursor: null, has_more: false }
      }
      
      // Fetch video details for liked video IDs
      // We'll fetch from the feed and filter, or create a batch endpoint
      // For now, let's fetch individual videos
      const api = useApi()
      const videos: Video[] = []
      const errors: string[] = []
      
      // Fetch videos in batches to avoid too many requests
      const batchSize = 10
      for (let i = 0; i < likedVideoIds.length; i += batchSize) {
        const batch = likedVideoIds.slice(i, i + batchSize)
        await Promise.all(
          batch.map(async (videoId) => {
            try {
              const video = await api.get<Video>(`/videos/${videoId}`)
              videos.push(video)
            } catch (error) {
              console.warn(`Failed to fetch video ${videoId}:`, error)
              errors.push(videoId)
            }
          })
        )
      }
      
      // Sort by timestamp (most recently liked first)
      const voteMap = new Map(pendingVotes.map(v => [v.videoId, v]))
      videos.sort((a, b) => {
        const voteA = voteMap.get(a.id)
        const voteB = voteMap.get(b.id)
        if (!voteA || !voteB) return 0
        return voteB.timestamp - voteA.timestamp // Most recent first
      })
      
      // Apply pagination (simple client-side pagination)
      const pageSize = 20
      const startIndex = cursor ? parseInt(cursor) || 0 : 0
      const endIndex = startIndex + pageSize
      const paginatedVideos = videos.slice(startIndex, endIndex)
      const hasMore = endIndex < videos.length
      const nextCursor = hasMore ? endIndex.toString() : null
      
      if (!cursor) {
        this.likedVideos = paginatedVideos
      } else {
        this.likedVideos.push(...paginatedVideos)
      }
      
      return {
        videos: paginatedVideos,
        next_cursor: nextCursor,
        has_more: hasMore,
      }
    },

    async getVideoStatus(videoId: string): Promise<Video> {
      const api = useApi()
      try {
        const response = await api.get<Video>(`/videos/${videoId}`)
        return response
      } catch (error) {
        console.error('Failed to get video status:', error)
        throw error
      }
    },
  },
})

