/**
 * Session ID Composable
 * Generates and manages a persistent session ID for anonymous users
 */
const SESSION_ID_KEY = 'session_id'

export const useSession = () => {
  const getOrCreateSessionId = (): string => {
    if (!process.client) {
      // Server-side: generate a temporary ID (won't persist, but that's okay)
      return crypto.randomUUID()
    }
    
    // Check if session ID already exists
    let sessionId = localStorage.getItem(SESSION_ID_KEY)
    
    if (!sessionId) {
      // Generate new session ID
      sessionId = crypto.randomUUID()
      localStorage.setItem(SESSION_ID_KEY, sessionId)
    }
    
    return sessionId
  }
  
  const getSessionId = (): string | null => {
    if (!process.client) return null
    return localStorage.getItem(SESSION_ID_KEY)
  }
  
  const clearSessionId = (): void => {
    if (process.client) {
      localStorage.removeItem(SESSION_ID_KEY)
    }
  }
  
  return {
    getOrCreateSessionId,
    getSessionId,
    clearSessionId,
  }
}

