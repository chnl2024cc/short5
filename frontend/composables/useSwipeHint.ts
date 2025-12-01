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
   * The hint will stay visible until the user swipes (calls dismissSwipeHint)
   */
  const showHint = (delay: number = 0) => {
    if (!checkSwipeHint() || showSwipeHint.value) return

    const show = () => {
      showSwipeHint.value = true
      // Hint stays visible until user swipes (no auto-dismiss)
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
