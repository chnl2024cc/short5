/**
 * API Client Composable
 */
export const useApi = () => {
  const config = useRuntimeConfig()
  const apiBaseUrl = config.public.apiBaseUrl
  const authStore = useAuthStore()

  const request = async <T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> => {
    const token = authStore?.token
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    }

    // Only set Content-Type for JSON, not for FormData
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json'
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${apiBaseUrl}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: 'Unknown error' } }))
      throw new Error(error.error?.message || 'Request failed')
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

