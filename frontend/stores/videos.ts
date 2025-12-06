/**
 * Videos Store (Pinia)
 */
import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'
import { useAuthStore } from './auth'
import type { Video, FeedResponse } from '~/types/video'

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
      const api = useApi()
      
      // Always send vote to backend immediately (for analytics)
      const votePayload: { direction: string; session_id?: string } = {
        direction,
      }
      
      // If not authenticated, include session_id
      if (!authStore.isAuthenticated) {
        const { useSession } = await import('~/composables/useSession')
        const { getOrCreateSessionId } = useSession()
        votePayload.session_id = getOrCreateSessionId()
      }
      
      await api.post(`/videos/${videoId}/vote`, votePayload)
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
      const api = useApi()
      
      // Build query parameters
      const params = new URLSearchParams()
      if (cursor) {
        params.append('cursor', cursor)
      }
      
      // If not authenticated, include session_id
      if (!authStore.isAuthenticated && process.client) {
        const { useSession } = await import('~/composables/useSession')
        const { getSessionId } = useSession()
        const sessionId = getSessionId()
        if (sessionId) {
          params.append('session_id', sessionId)
        }
      }
      
      const queryString = params.toString()
      const endpoint = `/users/me/liked${queryString ? `?${queryString}` : ''}`
      
      try {
        const response = await api.get<FeedResponse>(endpoint)
        
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

