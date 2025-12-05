/**
 * Authentication Store (Pinia)
 */
import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as any | null,
    token: null as string | null,
    refreshToken: null as string | null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
  },

  actions: {
    async login(email: string, password: string) {
      const api = useApi()
      try {
        const response = await api.post<{
          user: any
          access_token: string
          refresh_token: string
        }>('/auth/login', { email, password })
        
        this.user = response.user
        this.token = response.access_token
        this.refreshToken = response.refresh_token
        
        // Store in localStorage
        if (process.client) {
          localStorage.setItem('token', response.access_token)
          localStorage.setItem('refreshToken', response.refresh_token)
          localStorage.setItem('user', JSON.stringify(response.user))
        }
        
        // Sync pending votes after login
        const { useVideosStore } = await import('./videos')
        const videosStore = useVideosStore()
        await videosStore.syncPendingVotes()
        
        return response
      } catch (error) {
        console.error('Login failed:', error)
        throw error
      }
    },

    async register(username: string, email: string, password: string) {
      const api = useApi()
      try {
        const response = await api.post<{
          user: any
          access_token: string
          refresh_token: string
        }>('/auth/register', { username, email, password })
        
        this.user = response.user
        this.token = response.access_token
        this.refreshToken = response.refresh_token
        
        // Store in localStorage
        if (process.client) {
          localStorage.setItem('token', response.access_token)
          localStorage.setItem('refreshToken', response.refresh_token)
          localStorage.setItem('user', JSON.stringify(response.user))
        }
        
        // Sync pending votes after registration
        const { useVideosStore } = await import('./videos')
        const videosStore = useVideosStore()
        await videosStore.syncPendingVotes()
        
        return response
      } catch (error) {
        console.error('Registration failed:', error)
        throw error
      }
    },

    async logout() {
      const api = useApi()
      try {
        if (this.refreshToken) {
          await api.post('/auth/logout', { refresh_token: this.refreshToken })
        }
      } catch (error) {
        console.error('Logout failed:', error)
      } finally {
        this.user = null
        this.token = null
        this.refreshToken = null
        
        if (process.client) {
          localStorage.removeItem('token')
          localStorage.removeItem('refreshToken')
          localStorage.removeItem('user')
        }
      }
    },

    async refreshAccessToken() {
      if (!this.refreshToken) {
        throw new Error('No refresh token available')
      }
      
      const api = useApi()
      try {
        const response = await api.post<{
          access_token: string
          refresh_token: string
        }>('/auth/refresh', { refresh_token: this.refreshToken })
        
        this.token = response.access_token
        this.refreshToken = response.refresh_token
        
        if (process.client) {
          localStorage.setItem('token', response.access_token)
          localStorage.setItem('refreshToken', response.refresh_token)
        }
        
        return response
      } catch (error) {
        // Refresh failed, logout user
        await this.logout()
        throw error
      }
    },

    // Initialize from localStorage
    initFromStorage() {
      if (process.client) {
        const token = localStorage.getItem('token')
        const refreshToken = localStorage.getItem('refreshToken')
        const userStr = localStorage.getItem('user')
        
        if (token && refreshToken && userStr) {
          this.token = token
          this.refreshToken = refreshToken
          this.user = JSON.parse(userStr)
        }
      }
    },

    async fetchProfile() {
      const api = useApi()
      try {
        const response = await api.get<{
          id: string
          username: string
          email: string
          is_admin: boolean
          created_at: string
          stats: {
            videos_uploaded: number
            total_likes_received: number
            total_views: number
          }
        }>('/users/me')
        
        // Update user in store
        this.user = response
        
        // Update localStorage
        if (process.client) {
          localStorage.setItem('user', JSON.stringify(response))
        }
        
        return response
      } catch (error) {
        console.error('Failed to fetch profile:', error)
        throw error
      }
    },
  },
})

