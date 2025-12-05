/**
 * Composable for handling public folder assets with absolute URLs
 * 
 * This composable provides utilities for generating absolute URLs for public assets,
 * which is required for social media sharing (WhatsApp, Facebook, etc.)
 * 
 * IMPORTANT: This composable must be called within a Vue setup function or Nuxt context.
 * 
 * The site origin is automatically determined using multiple fallback methods:
 * 1. `useRequestEvent()` + `getRequestURL()` - Most reliable for SSR
 * 2. `useRequestURL()` - Nuxt 4 best practice
 * 3. `useRequestHeaders()` - Extract from headers (host, x-forwarded-host, etc.)
 * 4. `useNuxtApp().ssrContext` - Alternative event access
 * 5. Runtime config (`NUXT_PUBLIC_SITE_URL`) - For edge cases
 * 6. Environment variables - Common deployment platform variables
 * 
 * This ensures the origin is ALWAYS determined, even in edge cases.
 * 
 * @example
 * ```ts
 * const { getPublicAssetUrl, siteOrigin } = usePublicAsset()
 * const iconUrl = getPublicAssetUrl('/icon.svg')
 * const ogImageUrl = getPublicAssetUrl('/og-image.svg')
 * ```
 */
export const usePublicAsset = () => {
  /**
   * Get the current site origin (computed for reactivity)
   * All Nuxt composables are called within the computed to ensure proper context
   */
  const siteOrigin = computed((): string => {
    // Client-side: use window.location (always available)
    if (process.client) {
      return window.location.origin
    }
    
    // Server-side: try multiple methods to get origin from request context
    
    // Method 1: useRequestEvent() -> getRequestURL() - Most reliable for SSR
    try {
      const event = useRequestEvent()
      if (event) {
        const url = getRequestURL(event)
        if (url?.origin) {
          return url.origin
        }
      }
    } catch {
      // Fall through to next method
    }
    
    // Method 2: useRequestURL() - Nuxt 4 best practice
    try {
      const requestUrl = useRequestURL()
      if (requestUrl?.origin) {
        return requestUrl.origin
      }
    } catch {
      // Fall through to next method
    }
    
    // Method 3: Extract from request headers (always works in SSR)
    try {
      const headers = useRequestHeaders()
      if (headers && Object.keys(headers).length > 0) {
        // Try multiple header names that might contain the host
        const host = headers.host || 
                     headers['x-forwarded-host'] || 
                     headers[':authority'] ||
                     headers['host']
        
        if (host && typeof host === 'string' && host.length > 0) {
          // Clean host - remove port for canonical origin (social media prefers no port)
          const cleanHost = host.split(':')[0]?.trim()
          if (cleanHost && cleanHost.length > 0) {
            // Determine protocol from headers or environment
            const forwardedProto = headers['x-forwarded-proto']
            const scheme = headers[':scheme']
            const forwardedProtocol = headers['x-forwarded-protocol']
            
            const protocol = (typeof forwardedProto === 'string' ? forwardedProto.split(',')[0]?.trim() : null) ||
                            (typeof scheme === 'string' ? scheme : null) ||
                            (typeof forwardedProtocol === 'string' ? forwardedProtocol : null) ||
                            (process.env.NODE_ENV === 'production' ? 'https' : 'http')
            return `${protocol}://${cleanHost}`
          }
        }
      }
    } catch {
      // Fall through to next method
    }
    
    // Method 4: Try useNuxtApp() -> ssrContext
    try {
      const nuxtApp = useNuxtApp()
      if (nuxtApp?.ssrContext?.event) {
        const url = getRequestURL(nuxtApp.ssrContext.event)
        if (url?.origin) {
          return url.origin
        }
      }
    } catch {
      // Fall through to next method
    }
    
    // Method 5: Runtime config (for edge cases like build-time)
    try {
      const config = useRuntimeConfig()
      const siteUrl = config.public.siteUrl
      if (typeof siteUrl === 'string' && siteUrl) {
        return siteUrl
      }
    } catch {
      // Runtime config not available
    }
    
    // Method 6: Environment variable as last resort
    const envSiteUrl = process.env.NUXT_PUBLIC_SITE_URL
    if (typeof envSiteUrl === 'string' && envSiteUrl) {
      return envSiteUrl
    }
    
    // Development fallback
    if (process.env.NODE_ENV === 'development') {
      return 'http://localhost:3000'
    }
    
    // Production: This should never happen, but if it does, we need a fallback
    // Try to construct from common production patterns
    const hostname = process.env.HOSTNAME || process.env.VERCEL_URL || process.env.RAILWAY_PUBLIC_DOMAIN
    if (hostname) {
      return `https://${hostname}`
    }
    
    // Ultimate fallback - log error but return something
    console.error('[usePublicAsset] CRITICAL: Could not determine site origin. Please set NUXT_PUBLIC_SITE_URL.')
    return ''
  })

  /**
   * Get absolute URL for a public folder asset
   * 
   * @param path - Path to the asset in the public folder (e.g., '/icon.svg', '/og-image.svg')
   * @returns ComputedRef with absolute URL to the asset
   * 
   * @example
   * ```ts
   * const iconUrl = getPublicAssetUrl('/icon.svg')
   * // Returns: ComputedRef<string> with value like 'https://example.com/icon.svg'
   * // Use: iconUrl.value to get the string value
   * ```
   */
  const getPublicAssetUrl = (path: string) => {
    const normalizedPath = path.startsWith('/') ? path : `/${path}`
    return computed(() => {
      const origin = siteOrigin.value
      if (!origin) {
        console.error(`[usePublicAsset] Cannot generate URL for ${normalizedPath}: site origin is not available`)
        return normalizedPath // Return relative path as fallback
      }
      return `${origin}${normalizedPath}`
    })
  }

  return {
    getPublicAssetUrl,
    siteOrigin,
  }
}

