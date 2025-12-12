/**
 * Composable for managing action hint overlay state (like/not_like/share)
 * Shows hints when video repeats for the second time
 */
import { ref } from 'vue'

const ACTION_HINT_DISMISSED_KEY = 'action_hint_dismissed'

export const useActionHint = () => {
  const showActionHint = ref(false)

  /**
   * Check if the hint has been dismissed (stored in localStorage)
   * DISABLED: Always returns false to prevent hints from showing
   */
  const checkActionHint = (): boolean => {
    // Hint is disabled - always return false
    return false
  }

  /**
   * Dismiss the hint and store in localStorage
   */
  const dismissActionHint = () => {
    showActionHint.value = false
    if (process.client) {
      localStorage.setItem(ACTION_HINT_DISMISSED_KEY, 'true')
    }
  }

  /**
   * Show the hint if it hasn't been dismissed
   * DISABLED: Does nothing to prevent hints from showing
   */
  const showHint = (delay: number = 0) => {
    // Hint is disabled - do nothing
    return
  }

  return {
    showActionHint,
    dismissActionHint,
    showHint,
    checkActionHint,
  }
}
