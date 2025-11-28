/**
 * Authentication Store (Pinia)
 */
import { defineStore } from 'pinia'

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
      // TODO: Implement login
    },

    async register(username: string, email: string, password: string) {
      // TODO: Implement registration
    },

    async logout() {
      // TODO: Implement logout
    },

    async refreshAccessToken() {
      // TODO: Implement token refresh
    },
  },
})

