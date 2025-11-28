/**
 * Videos Store (Pinia)
 */
import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'

export const useVideosStore = defineStore('videos', {
  state: () => ({
    feed: [] as any[],
    likedVideos: [] as any[],
    currentCursor: null as string | null,
    hasMore: true,
  }),

  actions: {
    async fetchFeed(cursor?: string) {
      const api = useApi()
      try {
        const response = await api.get<{
          videos: any[]
          next_cursor: string | null
          has_more: boolean
        }>(`/feed${cursor ? `?cursor=${cursor}` : ''}`)
        
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
      const api = useApi()
      try {
        await api.post(`/videos/${videoId}/vote`, {
          direction,
        })
      } catch (error) {
        console.error('Failed to vote on video:', error)
        throw error
      }
    },

    async uploadVideo(file: File, title?: string, description?: string) {
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

    async fetchLikedVideos(cursor?: string) {
      const api = useApi()
      try {
        const response = await api.get<{
          videos: any[]
          next_cursor: string | null
          has_more: boolean
        }>(`/users/me/liked${cursor ? `?cursor=${cursor}` : ''}`)
        
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
  },
})

