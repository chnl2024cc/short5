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
   */
  const checkActionHint = (): boolean => {
    if (!process.client) return false
    const dismissed = localStorage.getItem(ACTION_HINT_DISMISSED_KEY)
    return !dismissed
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
   * The hint will stay visible until the user interacts (calls dismissActionHint)
   */
  const showHint = (delay: number = 0) => {
    if (!checkActionHint() || showActionHint.value) return

    const show = () => {
      showActionHint.value = true
      // Hint stays visible until user interacts (no auto-dismiss)
    }

    if (delay > 0) {
      setTimeout(show, delay)
    } else {
      show()
    }
  }

  return {
    showActionHint,
    dismissActionHint,
    showHint,
    checkActionHint,
  }
}
