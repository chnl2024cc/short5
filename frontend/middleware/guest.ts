/**
 * Guest Middleware
 * Only allows non-authenticated users (for login/register pages)
 */
export default defineNuxtRouteMiddleware((to, from) => {
  const authStore = useAuthStore()
  
  // Initialize auth from localStorage if not already loaded
  if (process.client && !authStore.token) {
    authStore.initFromStorage()
  }
  
  // If authenticated, redirect to home
  if (authStore.isAuthenticated) {
    return navigateTo('/')
  }
})
