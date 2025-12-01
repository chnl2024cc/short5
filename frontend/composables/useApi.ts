/**
 * API Client Composable
 */
export const useApi = () => {
  const config = useRuntimeConfig()
  const apiBaseUrl = config.public.apiBaseUrl

  const request = async <T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> => {
    // Get auth store fresh on each request to ensure we have the latest token
    const authStore = useAuthStore()
    
    // Ensure auth store is initialized from localStorage (client-side only)
    // Always initialize from storage to ensure we have the latest token
    if (import.meta.client) {
      authStore.initFromStorage()
    }
    
    // Get token - try store first, then localStorage as fallback
    // Always read fresh from localStorage as fallback to ensure we have the latest token
    let token = authStore.token
    if (!token && import.meta.client) {
      token = localStorage.getItem('token')
      // If we got token from localStorage, update the store
      if (token) {
        authStore.token = token
        // Also get refresh token if available
        const refreshToken = localStorage.getItem('refreshToken')
        if (refreshToken) {
          authStore.refreshToken = refreshToken
        }
        // Also get user if available
        const userStr = localStorage.getItem('user')
        if (userStr) {
          try {
            authStore.user = JSON.parse(userStr)
          } catch (e) {
            console.warn('Failed to parse user from localStorage:', e)
          }
        }
      }
    }

    // Build headers object
    const headers: Record<string, string> = {}
    
    // Copy existing headers first
    if (options.headers) {
      if (options.headers instanceof Headers) {
        options.headers.forEach((value, key) => {
          headers[key] = value
        })
      } else if (Array.isArray(options.headers)) {
        options.headers.forEach(([key, value]) => {
          headers[key] = String(value)
        })
      } else {
        Object.entries(options.headers).forEach(([key, value]) => {
          headers[key] = String(value)
        })
      }
    }

    // Only set Content-Type for JSON, not for FormData
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json'
    }

    // Always set Authorization header if we have a token
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    } else {
      // Log warning if no token for authenticated endpoints
      console.warn('No authentication token found for request:', endpoint)
    }

    // Debug logging (always in development)
    if (import.meta.client) {
      console.log('API Request:', {
        endpoint: `${apiBaseUrl}${endpoint}`,
        method: options.method || 'GET',
        hasToken: !!token,
        tokenPreview: token ? `${token.substring(0, 20)}...` : 'none',
        tokenLength: token?.length || 0,
        headers: { ...headers },
        authStoreToken: authStore.token ? 'exists' : 'missing',
        localStorageToken: import.meta.client ? (localStorage.getItem('token') ? 'exists' : 'missing') : 'N/A',
        authorizationHeader: headers['Authorization'] ? 'present' : 'missing',
      })
    }

    // Create fetch options, ensuring headers are properly merged
    // Important: Don't spread options.headers here as it would overwrite our headers
    const { headers: _, ...restOptions } = options
    const fetchOptions: RequestInit = {
      ...restOptions,
      headers,
    }

    const response = await fetch(`${apiBaseUrl}${endpoint}`, fetchOptions)

    // Handle 401 Unauthorized - token might be expired, try to refresh
    if (response.status === 401 && import.meta.client) {
      const authStore = useAuthStore()
      const refreshToken = authStore.refreshToken || (import.meta.client ? localStorage.getItem('refreshToken') : null)
      
      // Try to refresh the token (use direct fetch to avoid circular dependency)
      if (refreshToken) {
        try {
          // Make refresh request directly (don't use useApi to avoid circular dependency)
          const refreshResponse = await fetch(`${apiBaseUrl}/auth/refresh`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: refreshToken }),
          })
          
          if (refreshResponse.ok) {
            const refreshData = await refreshResponse.json()
            const newAccessToken = refreshData.access_token
            const newRefreshToken = refreshData.refresh_token
            
            // Update store and localStorage
            authStore.token = newAccessToken
            authStore.refreshToken = newRefreshToken
            if (import.meta.client) {
              localStorage.setItem('token', newAccessToken)
              localStorage.setItem('refreshToken', newRefreshToken)
            }
            
            // Retry the original request with the new token
            headers['Authorization'] = `Bearer ${newAccessToken}`
            
            const retryOptions: RequestInit = {
              ...restOptions,
              headers,
            }
            
            const retryResponse = await fetch(`${apiBaseUrl}${endpoint}`, retryOptions)
            
            if (!retryResponse.ok) {
              const errorData = await retryResponse.json().catch(() => ({ detail: 'Unknown error' }))
              const errorMessage = errorData.detail || errorData.error?.message || errorData.message || 'Request failed'
              
              // If still 401 after refresh, redirect to login
              if (retryResponse.status === 401) {
                authStore.logout()
                navigateTo('/login')
              }
              
              throw new Error(errorMessage)
            }
            
            return retryResponse.json()
          } else {
            // Refresh failed
            throw new Error('Token refresh failed')
          }
        } catch (refreshError) {
          // Refresh failed, logout and redirect to login
          console.error('Token refresh failed:', refreshError)
          authStore.logout()
          navigateTo('/login')
          throw new Error('Session expired. Please log in again.')
        }
      } else {
        // No refresh token, logout and redirect
        authStore.logout()
        navigateTo('/login')
        throw new Error('Session expired. Please log in again.')
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      // FastAPI returns errors in 'detail' field
      const errorMessage = errorData.detail || errorData.error?.message || errorData.message || 'Request failed'
      throw new Error(errorMessage)
    }

    return response.json()
  }

  return {
    get: <T>(endpoint: string) => request<T>(endpoint, { method: 'GET' }),
    post: <T>(endpoint: string, data?: any) => {
      const isFormData = data instanceof FormData
      return request<T>(endpoint, {
        method: 'POST',
        body: isFormData ? data : data ? JSON.stringify(data) : undefined,
      })
    },
    put: <T>(endpoint: string, data?: any) =>
      request<T>(endpoint, {
        method: 'PUT',
        body: data ? JSON.stringify(data) : undefined,
      }),
    delete: <T>(endpoint: string) => request<T>(endpoint, { method: 'DELETE' }),
  }
}

