/**
 * Composable for managing swipe hint overlay state
 */
import { ref } from 'vue'

const SWIPE_HINT_DISMISSED_KEY = 'swipe_hint_dismissed'

export const useSwipeHint = () => {
  const showSwipeHint = ref(false)

  /**
   * Check if the hint has been dismissed (stored in localStorage)
   */
  const checkSwipeHint = (): boolean => {
    if (!process.client) return false
    const dismissed = localStorage.getItem(SWIPE_HINT_DISMISSED_KEY)
    return !dismissed
  }

  /**
   * Dismiss the hint and store in localStorage
   */
  const dismissSwipeHint = () => {
    showSwipeHint.value = false
    if (process.client) {
      localStorage.setItem(SWIPE_HINT_DISMISSED_KEY, 'true')
    }
  }

  /**
   * Show the hint if it hasn't been dismissed
   * Auto-dismisses after 5 seconds if user doesn't interact
   */
  const showHint = (delay: number = 0, autoDismissDelay: number = 5000) => {
    if (!checkSwipeHint() || showSwipeHint.value) return

    const show = () => {
      showSwipeHint.value = true
      // Auto-dismiss after specified delay if user doesn't interact
      if (autoDismissDelay > 0) {
        setTimeout(() => {
          if (showSwipeHint.value) {
            dismissSwipeHint()
          }
        }, autoDismissDelay)
      }
    }

    if (delay > 0) {
      setTimeout(show, delay)
    } else {
      show()
    }
  }

  return {
    showSwipeHint,
    dismissSwipeHint,
    showHint,
    checkSwipeHint,
  }
}
