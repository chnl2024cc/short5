import { useI18n } from './useI18n'
import type { Video } from '~/types/video'

export interface ShareVideoOptions {
  /**
   * Callback to show a notification when link is copied.
   * If not provided, will use alert() as fallback.
   */
  onCopied?: () => void
  
  /**
   * Translation key prefix for i18n keys.
   * Default: 'common'
   * Keys used: {prefix}.checkOutVideo, {prefix}.linkCopied, {prefix}.shareLink
   */
  translationPrefix?: string
}

/**
 * Composable for sharing videos
 * Handles Web Share API (mobile) and clipboard fallback (desktop)
 * 
 * @example
 * ```ts
 * const { shareVideo } = useShareVideo({
 *   onCopied: () => showNotification('Link copied!'),
 *   translationPrefix: 'videoSwiper'
 * })
 * 
 * await shareVideo(video)
 * ```
 */
export const useShareVideo = (options: ShareVideoOptions = {}) => {
  const { t } = useI18n()
  const { onCopied, translationPrefix = 'common' } = options

  const shareVideo = async (video: Video | { id: string; title?: string | null; description?: string | null }) => {
    if (!process.client) return

    try {
      const shareUrl = `${window.location.origin}/?video=${video.id}`
      const title = video.title || t(`${translationPrefix}.checkOutVideo`)
      const text = (video as Video).description || ''

      // Try to use Web Share API if available (mobile/iOS Safari)
      // IMPORTANT: This must be called synchronously within the user gesture context
      if (navigator.share) {
        try {
          await navigator.share({
            title,
            text,
            url: shareUrl,
          })
          // If share was successful and callback is provided, show notification
          if (onCopied) {
            onCopied()
          }
          return
        } catch (err: any) {
          // User cancelled - don't show error, just return silently
          if (err.name === 'AbortError') {
            return
          }
          // Other errors - fall back to clipboard
          console.warn('Web Share API failed:', err)
        }
      }

      // Fall back to clipboard
      try {
        await navigator.clipboard.writeText(shareUrl)
        
        // Show success notification
        if (onCopied) {
          onCopied()
        } else {
          // Fallback to alert if no callback provided
          alert(t(`${translationPrefix}.linkCopied`) || 'Link copied to clipboard')
        }
      } catch (clipboardError) {
        // Clipboard API might not be available (some browsers/iOS versions)
        console.error('Clipboard API failed:', clipboardError)
        // Final fallback: show the URL in an alert
        const shareLinkText = t(`${translationPrefix}.shareLink`) || 'Share link'
        alert(`${shareLinkText}: ${shareUrl}`)
      }
    } catch (error) {
      console.error('Failed to share video:', error)
      // Fallback: show the URL in an alert
      const shareLinkText = t(`${translationPrefix}.shareLink`) || 'Share link'
      alert(`${shareLinkText}: ${window.location.origin}/?video=${video.id}`)
    }
  }

  return {
    shareVideo,
  }
}