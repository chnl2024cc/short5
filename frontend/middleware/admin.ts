/**
 * Admin Middleware
 * Protects routes that require admin privileges
 * Only runs on client-side since it depends on localStorage
 */
export default defineNuxtRouteMiddleware((to, from) => {
  // Skip middleware on server-side - let client handle it
  if (process.server) {
    return
  }
  
  const authStore = useAuthStore()
  
  // Initialize from localStorage
  authStore.initFromStorage()
  
  // Check if user is authenticated
  if (!authStore.isAuthenticated) {
    return navigateTo('/login')
  }
  
  // Check if user is admin - must be explicitly true (handle both boolean and string)
  const isAdmin = authStore.user?.is_admin === true || authStore.user?.is_admin === 'true'
  if (!isAdmin) {
    // Redirect to home if not admin
    return navigateTo('/')
  }
})
