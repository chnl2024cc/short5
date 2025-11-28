/**
 * Admin Middleware
 * Protects routes that require admin privileges
 */
import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware((to, from) => {
  const authStore = useAuthStore()
  
  // Initialize from localStorage if needed
  if (process.client) {
    authStore.initFromStorage()
  }
  
  // Check if user is authenticated
  if (!authStore.isAuthenticated) {
    return navigateTo('/login')
  }
  
  // Check if user is admin
  if (!authStore.user?.is_admin) {
    // Redirect to home if not admin
    return navigateTo('/')
  }
})
