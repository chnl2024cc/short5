<template>
  <div
    ref="swipeContainer"
    class="video-container"
    @touchstart="onTouchStart"
    @touchmove="onTouchMove"
    @touchend="onTouchEnd"
    @mousedown="onMouseDown"
    @mousemove="onMouseMove"
    @mouseup="onMouseEnd"
    @mouseleave="onMouseEnd"
    @click="handleContainerClick"
  >
    <!-- Loading State -->
    <div
      v-if="isLoading"
      class="absolute inset-0 flex items-center justify-center bg-black/80 z-10"
    >
      <div class="text-center text-white">
        <div class="loading-spinner mb-4"></div>
        <p class="text-sm">{{ t('videoSwiper.loadingVideo') }}</p>
      </div>
    </div>

    <!-- Error State -->
    <div
      v-if="hasError && !isRetrying"
      class="absolute inset-0 flex items-center justify-center bg-black/80 z-10"
    >
      <div class="text-center text-white px-4">
        <p class="text-lg mb-2">{{ t('videoSwiper.failedToLoad') }}</p>
        <p class="text-sm text-gray-400 mb-4">{{ errorMessage }}</p>
        <button
          @click="retryVideoLoad"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          {{ t('videoSwiper.retry') }}
        </button>
      </div>
    </div>

    <!-- Video Thumbnail Placeholder -->
    <div
      v-if="isLoading || hasError"
      class="absolute inset-0 bg-cover bg-center"
      :style="video.thumbnail ? { backgroundImage: `url(${getAbsoluteUrl(video.thumbnail)})` } : {}"
    >
      <div class="absolute inset-0 bg-black/40"></div>
    </div>

    <video
      ref="videoElement"
      class="h-full object-cover cursor-pointer"
      :class="{ 
        'opacity-0': isLoading || hasError,
        'swipe-animation-like': buttonSwipeAnimation === 'like',
        'swipe-animation-not-like': buttonSwipeAnimation === 'not_like',
        'swipe-animation-share': buttonSwipeAnimation === 'share'
      }"
      :autoplay="isActive && !isLoading && !hasError"
      :loop="true"
      playsinline
      preload="auto"
      @loadedmetadata="onVideoLoaded"
      @timeupdate="onTimeUpdate"
      @waiting="onVideoWaiting"
      @playing="onVideoPlaying"
      @pause="onVideoPause"
      @play="onVideoPlay"
      @canplay="onVideoCanPlay"
      @error="onVideoError"
      @loadstart="onVideoLoadStart"
    />
    
    <!-- Buffering Indicator -->
    <div
      v-if="isBuffering && !isLoading"
      class="absolute inset-0 flex items-center justify-center bg-black/40 z-20 pointer-events-none"
    >
      <div class="loading-spinner"></div>
    </div>
    
    <!-- Swipe Overlay -->
    <div
      v-if="showOverlay"
      :class="['swipe-overlay', overlayClass, {
        'swipe-overlay-animate-like': buttonSwipeAnimation === 'like',
        'swipe-overlay-animate-not-like': buttonSwipeAnimation === 'not_like',
        'swipe-overlay-animate-share': buttonSwipeAnimation === 'share'
      }]"
      :style="{ opacity: overlayOpacity }"
      @click.stop
    >
      <div class="swipe-overlay-text">
        {{ overlayText }}
      </div>
    </div>
    
    <!-- Play/Pause Overlay - Shows when video is paused -->
    <div
      v-if="!isLoading && !hasError && isVideoPaused"
      class="absolute inset-0 flex items-center justify-center z-35 pointer-events-none"
    >
      <button
        @click.stop="togglePlayPause"
        class="p-6 bg-black/60 hover:bg-black/80 rounded-full transition-all backdrop-blur-sm shadow-lg pointer-events-auto"
        aria-label="Play video"
      >
        <svg
          class="w-16 h-16 text-white"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path d="M8 5v14l11-7z" />
        </svg>
      </button>
    </div>
    
    <!-- Action Buttons - Always visible for easy access -->
    <div 
      class="absolute bottom-0 left-0 right-0 flex items-center justify-center gap-16 z-35 action-buttons-container"
    >
      <!-- Not Like Button (Left) -->
      <button
        @click.stop="handleActionButtonClick('not_like')"
        class="action-button action-button-not-like"
        :aria-label="t('videoSwiper.nope')"
        :title="t('videoSwiper.nope')"
      >
        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="3">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <!-- Share Button (Center/Up) -->
      <button
        @click.stop="handleActionButtonClick('share')"
        class="action-button action-button-share"
        :aria-label="t('videoSwiper.share')"
        :title="t('videoSwiper.share')"
      >
        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
        </svg>
      </button>

      <!-- Like Button (Right) -->
      <button
        @click.stop="handleActionButtonClick('like')"
        class="action-button action-button-like"
        :aria-label="t('videoSwiper.like')"
        :title="t('videoSwiper.like')"
      >
        <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
        </svg>
      </button>
    </div>

    <!-- Video Info Overlay -->
    <div 
      class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent text-white z-30 video-info-overlay"
    >
      <h3 v-if="video.title && video.title.trim() !== '' && video.title.toLowerCase() !== 'untitled'" class="font-bold text-lg">
        {{ video.title }}
      </h3>
      <p class="text-sm">{{ video.user?.username }}</p>
      <div class="flex gap-4 mt-2 text-sm items-center">
        <span>❤️ {{ video.stats?.likes || 0 }}</span>
        <span>👁️ {{ video.stats?.views || 0 }}</span>
        <button
          @click.stop="handleShare"
          class="flex items-center gap-1 px-3 py-1.5 bg-black/60 hover:bg-black/80 active:bg-black/90 rounded-lg transition-colors touch-manipulation"
          :title="t('videoSwiper.shareButton')"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
          </svg>
          <span class="font-medium">{{ t('videoSwiper.shareButton') }}</span>
        </button>
        <button
          v-if="authStore.isAuthenticated"
          @click.stop="showReportDialog = true"
          class="flex items-center gap-1 px-3 py-1.5 bg-red-600/60 hover:bg-red-600/80 active:bg-red-600/90 rounded-lg transition-colors touch-manipulation"
          title="Report"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span class="font-medium">Report</span>
        </button>
      </div>
      <!-- Share notification -->
      <div
        v-if="showShareNotification"
        class="absolute left-1/2 transform -translate-x-1/2 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg z-40 animate-fade-in"
        style="bottom: max(calc(4rem + env(safe-area-inset-bottom)), 4rem);"
      >
        {{ t('videoSwiper.linkCopied') }}
      </div>
    </div>

    <!-- Action Hint Overlay - Shows when video repeats second time -->
    <ActionHintOverlay
      :show="showActionHint"
      @dismiss="dismissActionHint"
    />

    <!-- Prominent Share Button - Appears after second playback -->
    <Transition name="share-button">
      <button
        v-if="showShareButton"
        @click.stop="handleShareButtonClick"
        class="prominent-share-button"
        :aria-label="t('videoSwiper.shareVideo')"
      >
        <div class="share-button-content">
          <div class="share-button-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
          </div>
          <div class="share-button-text">
            <span class="share-button-label">{{ t('videoSwiper.shareWithFriends') }}</span>
            <span class="share-button-subtitle">{{ t('videoSwiper.theyWillLoveIt') }}</span>
          </div>
        </div>
        <div class="share-button-glow"></div>
      </button>
    </Transition>

    <!-- Report Dialog -->
    <div
      v-if="showReportDialog"
      class="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      @click.self="showReportDialog = false"
    >
      <div class="bg-gray-900 rounded-lg p-6 max-w-md w-full">
        <h3 class="text-xl font-bold mb-4">Report Video</h3>
        <p class="text-gray-400 mb-4">
          Help us keep the community safe. Why are you reporting this video?
        </p>
        <div class="mb-4">
          <label class="block text-sm font-semibold mb-2">
            Reason (optional)
          </label>
          <textarea
            v-model="reportReason"
            class="w-full bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500"
            rows="3"
            placeholder="Please describe the issue..."
          />
        </div>
        <div v-if="reportSuccess" class="mb-4 p-3 bg-green-900/50 border border-green-700 rounded-lg">
          <p class="text-green-300 text-sm">Report submitted successfully. Thank you!</p>
        </div>
        <div class="flex gap-3">
          <button
            @click="showReportDialog = false; reportReason = ''; reportSuccess = false"
            class="flex-1 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
          >
            Cancel
          </button>
          <button
            @click="submitReport"
            :disabled="reportSubmitting || reportSuccess"
            class="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-semibold transition-colors"
          >
            {{ reportSubmitting ? 'Submitting...' : reportSuccess ? 'Submitted' : 'Submit Report' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useVideosStore } from '~/stores/videos'
import { useAuthStore } from '~/stores/auth'
import { useActionHint } from '~/composables/useActionHint'
import { useI18n } from '~/composables/useI18n'
import { useShareVideo } from '~/composables/useShareVideo'
import { useApi } from '~/composables/useApi'
import ActionHintOverlay from './ActionHintOverlay.vue'
import type { Video } from '~/types/video'

const config = useRuntimeConfig()
const backendBaseUrl = config.public.backendBaseUrl

// Helper to convert relative URLs to absolute URLs
const getAbsoluteUrl = (url: string | null | undefined): string => {
  // Handle missing URLs gracefully - return empty string instead of throwing
  if (!url) {
    return ''
  }
  // If already absolute (starts with http:// or https://), return as-is
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  // If relative (starts with /), prepend backend base URL
  if (url.startsWith('/')) {
    return `${backendBaseUrl}${url}`
  }
  // Otherwise, assume it's relative to backend
  return `${backendBaseUrl}/${url}`
}


interface Props {
  video: Video
  isActive?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isActive: true,
})

const emit = defineEmits<{
  swiped: [direction: 'like' | 'not_like' | 'share']
  viewUpdate: [seconds: number]
  error: [error: Error]
  videoStarted: []
}>()

const videosStore = useVideosStore()
const authStore = useAuthStore()
const api = useApi()
const swipeContainer = ref<HTMLElement | null>(null)
const videoElement = ref<HTMLVideoElement | null>(null)
const { t } = useI18n()

// Action hint management
const { showActionHint, dismissActionHint, showHint: showActionHintHint } = useActionHint()

// Prominent share button state - appears after second playback
const showShareButton = ref(false)
const shareButtonDismissed = ref(false)

// Share notification state
const showShareNotification = ref(false)

// Report dialog state
const showReportDialog = ref(false)
const reportReason = ref('')
const reportSubmitting = ref(false)
const reportSuccess = ref(false)

// Share video functionality with notification UI
const { shareVideo } = useShareVideo({
  onCopied: () => {
    showShareNotification.value = true
    setTimeout(() => {
      showShareNotification.value = false
    }, 2000)
  },
  translationPrefix: 'videoSwiper',
})

const handleShare = async () => {
  // Simply call share - video should continue playing naturally
  // The share dialog (if it opens) might pause the video, but that's expected browser behavior
  // We don't need to interfere with video playback during the gesture
  await shareVideo(props.video)
  // Note: If the share dialog pauses the video, it will resume automatically when dialog closes
  // This matches the behavior when clicking the share button
  
  // Dismiss prominent share button after sharing
  if (showShareButton.value) {
    showShareButton.value = false
    shareButtonDismissed.value = true
  }
}

// Handle prominent share button click
const handleShareButtonClick = async () => {
  await handleShare()
}

// Trigger swipe animation for button clicks
const triggerButtonSwipeAnimation = (direction: 'like' | 'not_like' | 'share') => {
  // Set the animation direction
  buttonSwipeAnimation.value = direction
  
  // Animate: fade in, hold, fade out
  // The overlay will show immediately with opacity 0.9 (from computed)
  // After a delay, clear it to trigger fade out
  setTimeout(() => {
    buttonSwipeAnimation.value = null
  }, 500) // Show for 500ms, then fade out (fade out handled by CSS transition)
}

// Handle action button clicks (Like, Not Like, Share)
const handleActionButtonClick = async (direction: 'like' | 'not_like' | 'share') => {
  // Dismiss hints on any action
  if (showActionHint.value) {
    dismissActionHint()
  }
  
  // Trigger swipe animation to show users they can also swipe
  triggerButtonSwipeAnimation(direction)
  
  // Wait for animation to complete (500ms) before executing action and switching to next video
  // This ensures users see the full animation before the video disappears
  await new Promise(resolve => setTimeout(resolve, 500))
  
  if (direction === 'share') {
    // Share doesn't remove video from feed
    await handleShare()
    emit('swiped', 'share')
  } else {
    // Like/Not Like - trigger vote and emit swipe event (this removes video and shows next)
    videosStore.voteOnVideo(props.video.id, direction)
    emit('swiped', direction)
  }
}

// Report functionality
const submitReport = async () => {
  if (reportSubmitting.value || reportSuccess.value) return
  
  reportSubmitting.value = true
  try {
    await api.post('/reports', {
      report_type: 'video',
      target_id: props.video.id,
      reason: reportReason.value || undefined,
    })
    reportSuccess.value = true
    setTimeout(() => {
      showReportDialog.value = false
      reportReason.value = ''
      reportSuccess.value = false
    }, 2000)
  } catch (err: any) {
    console.error('Failed to submit report:', err)
    alert(err.message || 'Failed to submit report. Please try again.')
  } finally {
    reportSubmitting.value = false
  }
}

// Expose play method for external control (needed for iOS Safari autoplay)
const playVideo = async () => {
  if (!videoElement.value || isLoading.value || hasError.value) return false
  try {
    await videoElement.value.play()
    return true
  } catch (err) {
    console.warn('Play failed:', err)
    return false
  }
}

// Expose methods for parent component
defineExpose({
  playVideo,
})

// Video state
const isLoading = ref(true)
const hasError = ref(false)
const errorMessage = ref('')
const isRetrying = ref(false)
const isBuffering = ref(false)
const isVideoPaused = ref(false) // Track video paused state for play button overlay
const videoLoopCount = ref(0) // Track how many times video has looped
const lastVideoTime = ref(0) // Track last video time to detect loops

const retryCount = ref(0)
const maxRetries = 3
const retryDelay = 2000 // 2 seconds
let retryTimeout: NodeJS.Timeout | null = null
let bufferingTimeout: NodeJS.Timeout | null = null

// Performance optimization: Throttle timeupdate emissions
let lastViewUpdateTime = 0
const VIEW_UPDATE_THROTTLE = 1000 // Emit viewUpdate once per second
let rafGestureId: number | null = null // RequestAnimationFrame ID for gesture throttling
let pendingGestureUpdate: (() => void) | null = null // Closure that captures the event

// Swipe state
const startX = ref(0)
const startY = ref(0)
const currentX = ref(0)
const currentY = ref(0)
const isDragging = ref(false)
const swipeDirection = ref<'like' | 'not_like' | 'share' | null>(null)
const touchStartTime = ref(0)
// Track if a swipe occurred to prevent click events from firing
const hasSwiped = ref(false)

// Button-triggered swipe animation state
const buttonSwipeAnimation = ref<'like' | 'not_like' | 'share' | null>(null)

// Overlay state
const showOverlay = computed(() => {
  // Show overlay during drag OR button animation
  return (isDragging.value && swipeDirection.value !== null) || buttonSwipeAnimation.value !== null
})
const overlayClass = computed(() => {
  // Use button animation direction if active, otherwise use drag direction
  const direction = buttonSwipeAnimation.value || swipeDirection.value
  if (direction === 'like') return 'like'
  if (direction === 'not_like') return 'not-like'
  if (direction === 'share') return 'share'
  return ''
})
const overlayText = computed(() => {
  // Use button animation direction if active, otherwise use drag direction
  const direction = buttonSwipeAnimation.value || swipeDirection.value
  if (direction === 'like') return t('videoSwiper.like')
  if (direction === 'not_like') return t('videoSwiper.nope')
  if (direction === 'share') return t('videoSwiper.share')
  return ''
})
const overlayOpacity = computed(() => {
  // If button animation is active, show full opacity
  if (buttonSwipeAnimation.value !== null) {
    return 0.9
  }
  // Otherwise, use drag-based opacity
  if (!isDragging.value) return 0
  if (swipeDirection.value === 'share') {
    const distance = Math.abs(currentY.value - startY.value)
    return Math.min(distance / 150, 1)
  }
  const distance = Math.abs(currentX.value - startX.value)
  return Math.min(distance / 150, 1)
})

// ============================================================================
// SWIPE GESTURE DETECTION - Clean Implementation Following Vue Best Practices
// ============================================================================

/**
 * Check if target is an interactive element (button, link, input)
 * Prevents swipe detection from interfering with button clicks
 */
const isInteractiveElement = (target: HTMLElement | null): boolean => {
  if (!target) return false
  return (
    target.tagName === 'BUTTON' ||
    target.tagName === 'A' ||
    target.tagName === 'INPUT' ||
    !!target.closest('button') ||
    !!target.closest('a') ||
    !!target.closest('input')
  )
}

/**
 * Extract coordinates from touch or mouse event
 * Handles iOS Safari quirks with changedTouches
 */
const getEventCoordinates = (e: TouchEvent | MouseEvent): { x: number; y: number } => {
  if (e instanceof TouchEvent) {
    const touch = e.touches?.[0] || e.changedTouches?.[0]
    if (touch) {
      return { x: touch.clientX, y: touch.clientY }
    }
    return { x: 0, y: 0 }
  }
  return { x: e.clientX, y: e.clientY }
}

/**
 * Start gesture tracking
 * Only starts if not clicking on interactive elements
 */
const startGesture = (e: TouchEvent | MouseEvent) => {
  const target = e.target as HTMLElement
  if (isInteractiveElement(target)) return
  
  const coords = getEventCoordinates(e)
  startX.value = coords.x
  startY.value = coords.y
  isDragging.value = true
  hasSwiped.value = false // Reset swipe flag
  touchStartTime.value = Date.now()
  swipeDirection.value = null
}

/**
 * Update gesture during movement (internal - processes gesture)
 * Calculates direction and prevents default scrolling for swipes
 */
const processGestureUpdate = (e: TouchEvent | MouseEvent) => {
  if (!isDragging.value) return
  
  const coords = getEventCoordinates(e)
  currentX.value = coords.x
  currentY.value = coords.y
  
  const deltaX = currentX.value - startX.value
  const deltaY = currentY.value - startY.value
  const absDeltaX = Math.abs(deltaX)
  const absDeltaY = Math.abs(deltaY)
  
  // Determine swipe direction based on dominant axis
  const minMovement = 30 // Minimum pixels to detect direction
  if (absDeltaY > absDeltaX && absDeltaY > minMovement) {
    // Vertical swipe
    swipeDirection.value = deltaY < 0 ? 'share' : null // Up = share, Down = ignore
  } else if (absDeltaX > absDeltaY && absDeltaX > minMovement) {
    // Horizontal swipe
    swipeDirection.value = deltaX > 0 ? 'like' : 'not_like'
  }
  
  // Clear RAF ID after processing
  rafGestureId = null
  pendingGestureUpdate = null
}

/**
 * Update gesture during movement (throttled with RAF)
 * Uses requestAnimationFrame to throttle updates to ~60fps max
 */
const updateGesture = (e: TouchEvent | MouseEvent) => {
  if (!isDragging.value) return
  
  // Always prevent default immediately for touch events (required for iOS Safari)
  // This must happen synchronously, not in RAF
  if (e instanceof TouchEvent && e.touches.length === 1) {
    const coords = getEventCoordinates(e)
    const deltaX = Math.abs(coords.x - startX.value)
    const deltaY = Math.abs(coords.y - startY.value)
    if (deltaX > 10 || deltaY > 10) {
      e.preventDefault()
    }
  }
  
  // Store the event for processing in RAF
  pendingGestureUpdate = () => processGestureUpdate(e)
  
  // Schedule update via RAF if not already scheduled
  if (rafGestureId === null) {
    rafGestureId = requestAnimationFrame(() => {
      if (pendingGestureUpdate) {
        pendingGestureUpdate()
      }
    })
  }
}

/**
 * End gesture and process result
 * Handles share, like/not_like, and tap gestures
 */
const endGesture = (e?: TouchEvent) => {
  if (!isDragging.value) return
  
  // Update final coordinates from touch end event (iOS Safari)
  if (e?.changedTouches?.[0]) {
    const touch = e.changedTouches[0]
    currentX.value = touch.clientX
    currentY.value = touch.clientY
  }
  
  const deltaX = currentX.value - startX.value
  const deltaY = currentY.value - startY.value
  const absDeltaX = Math.abs(deltaX)
  const absDeltaY = Math.abs(deltaY)
  const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY)
  const duration = Date.now() - touchStartTime.value
  
  // Process gesture result BEFORE resetting state
  const SWIPE_THRESHOLD = 100 // Minimum distance for swipe
  const TAP_THRESHOLD = 10 // Maximum distance for tap
  const TAP_DURATION = 300 // Maximum duration for tap (ms)
  
  const isTap = distance < TAP_THRESHOLD && duration < TAP_DURATION
  const isUpwardSwipe = swipeDirection.value === 'share' && absDeltaY > absDeltaX && absDeltaY > SWIPE_THRESHOLD && deltaY < 0
  const isHorizontalSwipe = (swipeDirection.value === 'like' || swipeDirection.value === 'not_like') && absDeltaX > absDeltaY && absDeltaX > SWIPE_THRESHOLD
  
  // Mark if a swipe occurred (prevents click event from firing)
  if (isUpwardSwipe || isHorizontalSwipe) {
    hasSwiped.value = true
  }
  
  // Dismiss hints on any interaction
  if (showActionHint.value) {
    dismissActionHint()
  }
  
  // Handle gestures
  if (isUpwardSwipe) {
    // Upward swipe = Share (preserves user gesture context for iOS Safari)
    handleShare()
    emit('swiped', 'share')
  } else if (isHorizontalSwipe && swipeDirection.value) {
    // Horizontal swipe = Like/Not Like
    const swipeDir = swipeDirection.value as 'like' | 'not_like'
    emit('swiped', swipeDir)
    videosStore.voteOnVideo(props.video.id, swipeDir)
  } else if (isTap) {
    // Tap = Toggle play/pause (only if no swipe occurred)
    togglePlayPause()
  }
  
  // Reset state AFTER processing
  isDragging.value = false
  swipeDirection.value = null
  currentX.value = 0
  currentY.value = 0
  touchStartTime.value = 0
  
  // Clear swipe flag after a short delay to allow click prevention
  // This prevents click events that fire after touch events
  if (hasSwiped.value) {
    setTimeout(() => {
      hasSwiped.value = false
    }, 300) // Click events typically fire within 300ms
  }
}

// Event handlers - Clean and simple
const onTouchStart = (e: TouchEvent) => startGesture(e)
const onMouseDown = (e: MouseEvent) => startGesture(e)
const onTouchMove = (e: TouchEvent) => updateGesture(e)
const onMouseMove = (e: MouseEvent) => updateGesture(e)

const onTouchEnd = (e: TouchEvent) => {
  endGesture(e)
  // CRITICAL: Prevent click event from firing after swipe
  // This completely separates swipe gestures from click events
  if (hasSwiped.value) {
    e.preventDefault()
    e.stopPropagation()
  }
}

const onMouseEnd = () => endGesture()

// Handle container clicks for play/pause (fallback)
// IMPORTANT: Only handles actual clicks, NOT swipes
let clickTimeout: NodeJS.Timeout | null = null

const handleContainerClick = (e: MouseEvent) => {
  // CRITICAL: Ignore clicks that occurred after a swipe
  // This completely separates tap/click from swipe gestures
  if (hasSwiped.value || isDragging.value) {
    e.preventDefault()
    e.stopPropagation()
    return
  }
  
  const target = e.target as HTMLElement
  if (target === swipeContainer.value || target === videoElement.value || target.closest('.video-container')) {
    // Only process if it's a genuine mouse click (not from touch event)
    // Check if this is a mouse click by checking pointerType if available, or if touch is not supported
    const isMouseClick = (e instanceof PointerEvent && e.pointerType === 'mouse') || 
                         (!('ontouchstart' in window) && e.type === 'click')
    
    if (isMouseClick) {
      if (clickTimeout) clearTimeout(clickTimeout)
      clickTimeout = setTimeout(() => {
        // Double-check we didn't swipe during the timeout
        if (!isDragging.value && !hasSwiped.value) {
          togglePlayPause()
        }
        clickTimeout = null
      }, 100)
    }
  }
}

// Initialize HLS video playback with proper error handling
const initializeVideo = async (retry = false) => {
  if (!videoElement.value) return
  if (!process.client) return // Only run on client side
  
  // Reset error state on new initialization
  if (!retry) {
    hasError.value = false
    errorMessage.value = ''
    retryCount.value = 0
    videoLoopCount.value = 0 // Reset loop count for new video
    lastVideoTime.value = 0
    // Reset share button state for new video
    showShareButton.value = false
    shareButtonDismissed.value = false
  }
  
  isLoading.value = true
  isRetrying.value = retry
  
  const video = videoElement.value
  
  // Clear any existing retry timeout
  if (retryTimeout) {
    clearTimeout(retryTimeout)
    retryTimeout = null
  }
  
  try {
    // Skip videos without url_mp4 instead of throwing
    if (!props.video.url_mp4) {
      console.warn(`Video ${props.video.id} is missing url_mp4 - skipping`)
      handleVideoError(new Error('Video is not ready for playback'))
      return
    }
    
    // Simple MP4 playback - works in all modern browsers
    const mp4Src = getAbsoluteUrl(props.video.url_mp4)
    if (!mp4Src) {
      handleVideoError(new Error('MP4 URL is invalid or could not be resolved'))
      return
    }
    // Log only in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[VideoSwiper] Loading MP4: ${mp4Src}`)
    }
    video.src = mp4Src
    video.load()
    video.addEventListener('error', handleNativeVideoError, { once: true })
  } catch (error: any) {
    console.error('Error initializing video:', error)
    handleVideoError(error)
  }
}


// Handle native video element errors
const handleNativeVideoError = (event: Event) => {
  const video = event.target as HTMLVideoElement
  const error = video.error
  
  if (error) {
    let message = 'Unknown video error'
    switch (error.code) {
      case MediaError.MEDIA_ERR_ABORTED:
        message = 'Video loading aborted'
        break
      case MediaError.MEDIA_ERR_NETWORK:
        message = 'Network error while loading video'
        if (retryCount.value < maxRetries) {
          retryCount.value++
          retryTimeout = setTimeout(() => {
            video.load()
          }, retryDelay)
          return
        }
        break
      case MediaError.MEDIA_ERR_DECODE:
        message = 'Video decoding error'
        break
      case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
        message = 'Video format not supported'
        break
    }
    handleVideoError(new Error(message))
  }
}

// General video error handler
const handleVideoError = (error: Error) => {
  console.error('Video error:', error)
  hasError.value = true
  errorMessage.value = error.message || 'Failed to load video'
  isLoading.value = false
  isRetrying.value = false
  emit('error', error)
}

// Retry video load
const retryVideoLoad = () => {
  retryCount.value = 0
  initializeVideo(true)
}

// Watch for video changes (when video prop changes)
watch(
  () => props.video.id,
  (newId, oldId) => {
    if (newId !== oldId && process.client) {
      // Clean up previous video
      cleanupVideo()
      // Small delay to ensure DOM is updated
      nextTick(() => {
        initializeVideo()
      })
    }
  }
)

// Watch for active state changes
watch(
  () => props.isActive,
  async (isActive) => {
    if (!videoElement.value) return
    
    if (isActive && !isLoading.value && !hasError.value) {
      // Try to play immediately
      try {
        await videoElement.value.play()
      } catch (err: any) {
        // If autoplay is blocked (iOS Safari), we'll need user interaction
        // The play will be triggered by the swipe handler in VideoFeed
        console.warn('Autoplay blocked, will need user interaction:', err)
      }
    } else if (!isActive) {
      videoElement.value.pause()
    }
  },
  { immediate: true }
)

// Cleanup function
const cleanupVideo = () => {
  // Reset loop tracking
  videoLoopCount.value = 0
  lastVideoTime.value = 0
  lastViewUpdateTime = 0
  // Reset share button state for new video
  showShareButton.value = false
  shareButtonDismissed.value = false
  // Clear timeouts
  if (retryTimeout) {
    clearTimeout(retryTimeout)
    retryTimeout = null
  }
  if (bufferingTimeout) {
    clearTimeout(bufferingTimeout)
    bufferingTimeout = null
  }
  if (clickTimeout) {
    clearTimeout(clickTimeout)
    clickTimeout = null
  }
  
  // Cancel pending RAF gesture update
  if (rafGestureId !== null) {
    cancelAnimationFrame(rafGestureId)
    rafGestureId = null
    pendingGestureUpdate = null
  }
  
  // Clean up video element
  if (videoElement.value) {
    videoElement.value.pause()
    videoElement.value.src = ''
    videoElement.value.load()
  }
  
  // Reset state
  isLoading.value = true
  hasError.value = false
  isBuffering.value = false
  isRetrying.value = false
}

// Video event handlers
const onVideoLoadStart = () => {
  isLoading.value = true
  hasError.value = false
}

const onVideoLoaded = () => {
  isLoading.value = false
  if (videoElement.value && props.isActive) {
    // Try to play immediately when video loads and is active
    videoElement.value.play().catch((err) => {
      console.warn('Autoplay blocked on load:', err)
      // Autoplay blocked, will be handled by swipe handler or user interaction
    })
  }
}

const onVideoCanPlay = () => {
  isLoading.value = false
  isBuffering.value = false
  // Try to play when video can play and is active (important for iOS Safari)
  if (videoElement.value && props.isActive && videoElement.value.paused) {
    videoElement.value.play().catch((err) => {
      // Silent fail - will be handled by user interaction or swipe handler
      console.warn('Play failed on canplay:', err)
    })
  }
}

const onVideoPlaying = () => {
  isLoading.value = false
  isBuffering.value = false
  isVideoPaused.value = false
  if (bufferingTimeout) {
    clearTimeout(bufferingTimeout)
    bufferingTimeout = null
  }
  // Emit event when video starts playing (only for active video)
  if (props.isActive) {
    emit('videoStarted')
  }
}

const onVideoWaiting = () => {
  // Show buffering indicator after 500ms
  bufferingTimeout = setTimeout(() => {
    if (videoElement.value && !videoElement.value.ended) {
      isBuffering.value = true
    }
  }, 500)
}

const onVideoError = (event: Event) => {
  handleNativeVideoError(event)
}

const onTimeUpdate = () => {
  if (videoElement.value && props.isActive) {
    const currentTime = videoElement.value.currentTime
    const duration = videoElement.value.duration
    const now = Date.now()
    
    // Detect video loop by checking if currentTime resets to near 0
    // This check runs every timeupdate to ensure we catch loops accurately
    if (duration > 0 && lastVideoTime.value > duration * 0.9 && currentTime < duration * 0.1) {
      videoLoopCount.value++
      
      // Show action hint when video has looped once (played twice)
      if (videoLoopCount.value === 1) {
        showActionHintHint(500) // Show after 500ms delay
        
        // Show prominent share button after second playback (when user might want to share)
        // Delay slightly longer than action hint to avoid overwhelming user
        if (!shareButtonDismissed.value) {
          setTimeout(() => {
            if (props.isActive && videoLoopCount.value >= 1) {
              showShareButton.value = true
            }
          }, 2000) // Show 2 seconds after loop (1.5s after action hint)
        }
      }
    }
    
    // Throttle viewUpdate emissions to once per second (reduces parent component updates)
    // Loop detection still runs every frame to ensure accuracy
    if (now - lastViewUpdateTime >= VIEW_UPDATE_THROTTLE) {
      const seconds = Math.floor(currentTime)
      emit('viewUpdate', seconds)
      lastViewUpdateTime = now
    }
    
    lastVideoTime.value = currentTime
  }
}

// Toggle play/pause on video click/tap
const togglePlayPause = () => {
  if (!videoElement.value || isLoading.value || hasError.value) return
  
  if (videoElement.value.paused) {
    videoElement.value.play().catch((err) => {
      console.warn('Play failed:', err)
    })
    isVideoPaused.value = false
  } else {
    videoElement.value.pause()
    isVideoPaused.value = true
  }
}

// Watch video element for pause/play events to update overlay
watch(
  () => videoElement.value?.paused,
  (paused) => {
    if (videoElement.value) {
      isVideoPaused.value = paused ?? false
    }
  },
  { immediate: true }
)

// Also listen to video pause/play events
const onVideoPause = () => {
  isVideoPaused.value = true
}

const onVideoPlay = () => {
  isVideoPaused.value = false
}


onMounted(() => {
  if (process.client) {
    nextTick(() => {
      initializeVideo()
    })
    
    // Add touch event listeners with proper passive options for iOS Safari
    // touchmove MUST be non-passive to allow preventDefault() for scroll prevention
    const container = swipeContainer.value
    if (container) {
      container.addEventListener('touchstart', onTouchStart, { passive: true })
      container.addEventListener('touchmove', onTouchMove, { passive: false })
      container.addEventListener('touchend', onTouchEnd, { passive: true })
    }
  }
})

onUnmounted(() => {
  // Remove touch event listeners
  const container = swipeContainer.value
  if (container && process.client) {
    container.removeEventListener('touchstart', onTouchStart)
    container.removeEventListener('touchmove', onTouchMove)
    container.removeEventListener('touchend', onTouchEnd)
  }
  
  // Complete cleanup
  cleanupVideo()
})
</script>

<style scoped>
@reference "tailwindcss";

.video-container {
  @apply relative w-full flex items-center justify-center bg-black touch-none;
  /* Fill parent container (feed-container) which fills page-container */
  height: 100%;
  min-height: 100%;
  user-select: none;
  -webkit-user-select: none;
  /* Prevent default touch behaviors to allow custom swipe gestures on iOS Safari */
  touch-action: none;
  -webkit-touch-callout: none;
}

.swipe-overlay {
  @apply absolute inset-0 flex items-center justify-center pointer-events-none z-50 transition-opacity duration-200;
}

.swipe-overlay.like {
  @apply bg-green-500;
}

.swipe-overlay.not-like {
  @apply bg-red-500;
}

.swipe-overlay.share {
  @apply bg-blue-500;
}

.swipe-overlay-text {
  @apply text-4xl font-bold text-white;
  text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.8);
  transform: rotate(-5deg);
}

/* Video swipe animations - makes video completely swipe away in swipe direction */
.swipe-animation-like {
  animation: swipeRight 0.5s ease-out forwards;
}

.swipe-animation-not-like {
  animation: swipeLeft 0.5s ease-out forwards;
}

.swipe-animation-share {
  animation: swipeUp 0.5s ease-out forwards;
}

@keyframes swipeRight {
  0% {
    transform: translateX(0) rotate(0deg);
    opacity: 1;
  }
  30% {
    transform: translateX(10%) rotate(5deg);
    opacity: 1;
  }
  60% {
    transform: translateX(30%) rotate(10deg);
    opacity: 1;
  }
  100% {
    transform: translateX(100%) rotate(15deg);
    opacity: 0;
  }
}

@keyframes swipeLeft {
  0% {
    transform: translateX(0) rotate(0deg);
    opacity: 1;
  }
  30% {
    transform: translateX(-10%) rotate(-5deg);
    opacity: 1;
  }
  60% {
    transform: translateX(-30%) rotate(-10deg);
    opacity: 1;
  }
  100% {
    transform: translateX(-100%) rotate(-15deg);
    opacity: 0;
  }
}

@keyframes swipeUp {
  0% {
    transform: translateY(0) rotate(0deg);
    opacity: 1;
  }
  30% {
    transform: translateY(-10%) rotate(-2deg);
    opacity: 1;
  }
  60% {
    transform: translateY(-30%) rotate(-3deg);
    opacity: 1;
  }
  100% {
    transform: translateY(-100%) rotate(-5deg);
    opacity: 0;
  }
}

/* Overlay animations - slides in then swipes away with video */
.swipe-overlay-animate-like {
  animation: overlaySwipeRight 0.5s ease-out forwards;
}

.swipe-overlay-animate-not-like {
  animation: overlaySwipeLeft 0.5s ease-out forwards;
}

.swipe-overlay-animate-share {
  animation: overlaySwipeUp 0.5s ease-out forwards;
}

.swipe-overlay-animate-like .swipe-overlay-text {
  animation: textSlideInFromRight 0.3s ease-out;
}

.swipe-overlay-animate-not-like .swipe-overlay-text {
  animation: textSlideInFromLeft 0.3s ease-out;
}

.swipe-overlay-animate-share .swipe-overlay-text {
  animation: textSlideInFromTop 0.3s ease-out;
}

@keyframes overlaySwipeRight {
  0% {
    transform: translateX(0) rotate(0deg);
    opacity: 0;
  }
  20% {
    transform: translateX(0) rotate(0deg);
    opacity: 0.9;
  }
  30% {
    transform: translateX(10%) rotate(5deg);
    opacity: 0.9;
  }
  60% {
    transform: translateX(30%) rotate(10deg);
    opacity: 0.9;
  }
  100% {
    transform: translateX(100%) rotate(15deg);
    opacity: 0;
  }
}

@keyframes overlaySwipeLeft {
  0% {
    transform: translateX(0) rotate(0deg);
    opacity: 0;
  }
  20% {
    transform: translateX(0) rotate(0deg);
    opacity: 0.9;
  }
  30% {
    transform: translateX(-10%) rotate(-5deg);
    opacity: 0.9;
  }
  60% {
    transform: translateX(-30%) rotate(-10deg);
    opacity: 0.9;
  }
  100% {
    transform: translateX(-100%) rotate(-15deg);
    opacity: 0;
  }
}

@keyframes overlaySwipeUp {
  0% {
    transform: translateY(0) rotate(0deg);
    opacity: 0;
  }
  20% {
    transform: translateY(0) rotate(0deg);
    opacity: 0.9;
  }
  30% {
    transform: translateY(-10%) rotate(-2deg);
    opacity: 0.9;
  }
  60% {
    transform: translateY(-30%) rotate(-3deg);
    opacity: 0.9;
  }
  100% {
    transform: translateY(-100%) rotate(-5deg);
    opacity: 0;
  }
}

@keyframes textSlideInFromRight {
  0% {
    transform: translateX(50px) rotate(-5deg);
    opacity: 0;
  }
  20% {
    transform: translateX(0) rotate(-5deg);
    opacity: 1;
  }
  100% {
    transform: translateX(0) rotate(-5deg);
    opacity: 1;
  }
}

@keyframes textSlideInFromLeft {
  0% {
    transform: translateX(-50px) rotate(-5deg);
    opacity: 0;
  }
  20% {
    transform: translateX(0) rotate(-5deg);
    opacity: 1;
  }
  100% {
    transform: translateX(0) rotate(-5deg);
    opacity: 1;
  }
}

@keyframes textSlideInFromTop {
  0% {
    transform: translateY(-50px) rotate(-5deg);
    opacity: 0;
  }
  20% {
    transform: translateY(0) rotate(-5deg);
    opacity: 1;
  }
  100% {
    transform: translateY(0) rotate(-5deg);
    opacity: 1;
  }
}

.loading-spinner {
  @apply w-12 h-12 border-4 border-white/20 border-t-white rounded-full;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translate(-50%, -10px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}

.touch-manipulation {
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}

.video-info-overlay {
  padding: 1rem;
  /* Use max() to ensure minimum padding while respecting safe area insets - works better in iOS Safari */
  /* This pattern is required for iOS Safari to properly recognize env() values */
  padding-bottom: max(calc(1rem + env(safe-area-inset-bottom)), 1rem);
}

/* ============================================================================
   PROMINENT SHARE BUTTON - Appears after second playback
   ============================================================================ */

.prominent-share-button {
  position: absolute;
  bottom: 18rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 40;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #1d4ed8 100%);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 1.5rem;
  padding: 1.25rem 2rem;
  box-shadow: 
    0 20px 60px rgba(59, 130, 246, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset,
    0 0 40px rgba(59, 130, 246, 0.3);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  pointer-events: auto;
  overflow: hidden;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  animation: shareButtonPulse 2s ease-in-out infinite, shareButtonFloat 3s ease-in-out infinite;
  min-width: 280px;
  max-width: 90%;
  /* Performance optimization: hint browser to optimize transforms */
  will-change: transform, box-shadow;
}

.prominent-share-button:hover {
  transform: translateX(-50%) translateY(-4px) scale(1.05);
  box-shadow: 
    0 25px 80px rgba(59, 130, 246, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.2) inset,
    0 0 60px rgba(59, 130, 246, 0.4);
  border-color: rgba(255, 255, 255, 0.4);
}

.prominent-share-button:active {
  transform: translateX(-50%) translateY(-2px) scale(1.02);
}

.share-button-content {
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
  z-index: 2;
}

.share-button-icon {
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  backdrop-filter: blur(10px);
  animation: iconRotate 3s ease-in-out infinite;
  /* Performance optimization: hint browser to optimize transforms */
  will-change: transform;
}

.share-button-icon svg {
  width: 1.75rem;
  height: 1.75rem;
  color: white;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.share-button-text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.25rem;
}

.share-button-label {
  color: white;
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  line-height: 1.2;
}

.share-button-subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.875rem;
  font-weight: 500;
  letter-spacing: 0.01em;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.share-button-glow {
  position: absolute;
  inset: -2px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.6), rgba(37, 99, 235, 0.4));
  border-radius: 1.5rem;
  opacity: 0;
  animation: glowPulse 2s ease-in-out infinite;
  z-index: 1;
  filter: blur(8px);
  /* Performance optimization: hint browser to optimize opacity/transform */
  will-change: opacity, transform;
}

@keyframes shareButtonPulse {
  0%, 100% {
    box-shadow: 
      0 20px 60px rgba(59, 130, 246, 0.4),
      0 0 0 1px rgba(255, 255, 255, 0.1) inset,
      0 0 40px rgba(59, 130, 246, 0.3);
  }
  50% {
    box-shadow: 
      0 25px 80px rgba(59, 130, 246, 0.5),
      0 0 0 1px rgba(255, 255, 255, 0.15) inset,
      0 0 60px rgba(59, 130, 246, 0.4);
  }
}

@keyframes shareButtonFloat {
  0%, 100% {
    transform: translateX(-50%) translateY(0);
  }
  50% {
    transform: translateX(-50%) translateY(-8px);
  }
}

@keyframes iconRotate {
  0%, 100% {
    transform: rotate(0deg) scale(1);
  }
  25% {
    transform: rotate(5deg) scale(1.05);
  }
  50% {
    transform: rotate(0deg) scale(1.1);
  }
  75% {
    transform: rotate(-5deg) scale(1.05);
  }
}

@keyframes glowPulse {
  0%, 100% {
    opacity: 0;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}

/* Share button transition */
.share-button-enter-active {
  transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.share-button-leave-active {
  transition: all 0.3s ease-out;
}

.share-button-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(20px) scale(0.8);
}

.share-button-enter-to {
  opacity: 1;
  transform: translateX(-50%) translateY(0) scale(1);
}

.share-button-leave-from {
  opacity: 1;
  transform: translateX(-50%) translateY(0) scale(1);
}

.share-button-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-10px) scale(0.9);
}

/* ============================================================================
   ACTION BUTTONS - Always visible Like/Not Like/Share buttons
   ============================================================================ */

.action-buttons-container {
  pointer-events: none; /* Allow clicks to pass through container, but buttons are clickable */
  padding-bottom: max(calc(10rem + env(safe-area-inset-bottom)), 10rem);
}

.action-button {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
  pointer-events: auto; /* Make buttons clickable */
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
}

/* Active/pressed state - works on touch screens */
.action-button:active {
  transform: scale(0.85);
  transition: transform 0.1s ease-out;
  border-color: rgba(255, 255, 255, 0.5);
}

/* Focus state for keyboard navigation (desktop) */
.action-button:focus-visible {
  outline: 2px solid rgba(255, 255, 255, 0.8);
  outline-offset: 2px;
}

/* Hover only on devices with pointer (desktop with mouse) */
@media (hover: hover) and (pointer: fine) {
  .action-button:hover {
    transform: scale(1.05);
    border-color: rgba(255, 255, 255, 0.5);
    box-shadow: 
      0 6px 16px rgba(0, 0, 0, 0.4),
      0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  }

  .action-button-not-like:hover {
    background: rgba(239, 68, 68, 0.5);
    box-shadow: 
      0 6px 16px rgba(239, 68, 68, 0.4),
      0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  }

  .action-button-share:hover {
    background: rgba(59, 130, 246, 0.5);
    box-shadow: 
      0 6px 16px rgba(59, 130, 246, 0.4),
      0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  }

  .action-button-like:hover {
    background: rgba(34, 197, 94, 0.5);
    box-shadow: 
      0 6px 16px rgba(34, 197, 94, 0.4),
      0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  }
}

/* Not Like Button (Red/X) */
.action-button-not-like {
  background: rgba(239, 68, 68, 0.35); /* red-500 with more transparency */
  color: white;
}

.action-button-not-like:active {
  background: rgba(239, 68, 68, 0.6);
  box-shadow: 
    0 4px 12px rgba(239, 68, 68, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.3) inset;
}

/* Share Button (Blue) */
.action-button-share {
  background: rgba(59, 130, 246, 0.35); /* blue-500 with more transparency */
  color: white;
}

.action-button-share:active {
  background: rgba(59, 130, 246, 0.6);
  box-shadow: 
    0 4px 12px rgba(59, 130, 246, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.3) inset;
}

/* Like Button (Green - Heart) */
.action-button-like {
  background: rgba(34, 197, 94, 0.35); /* green-500 with more transparency */
  color: white;
  width: 64px; /* Bigger than other buttons */
  height: 64px; /* Bigger than other buttons */
}

.action-button-like:active {
  background: rgba(34, 197, 94, 0.55);
  transform: scale(0.9); /* Slightly different scale for visual feedback */
  box-shadow: 
    0 4px 12px rgba(34, 197, 94, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.3) inset;
}

/* Mobile optimizations */
@media (max-width: 640px) {
  .prominent-share-button {
    padding: 1rem 1.5rem;
    border-radius: 1.25rem;
    min-width: 320px; /* Wider on mobile */
  }

  .share-button-icon {
    width: 2.5rem;
    height: 2.5rem;
  }

  .share-button-icon svg {
    width: 1.5rem;
    height: 1.5rem;
  }

  .share-button-label {
    font-size: 1rem;
  }

  .share-button-subtitle {
    font-size: 0.8125rem;
  }
}

@media (max-width: 480px) {
  .prominent-share-button {
    min-width: 300px; /* Wider on small mobile */
    max-width: 90%; /* Increased from 85% to make it wider */
  }

  .share-button-content {
    gap: 0.75rem;
  }

  .share-button-icon {
    width: 2.25rem;
    height: 2.25rem;
  }

  .share-button-icon svg {
    width: 1.25rem;
    height: 1.25rem;
  }

  .share-button-label {
    font-size: 0.9375rem;
  }

  .share-button-subtitle {
    font-size: 0.75rem;
  }
}
</style>
