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
      :class="{ 'opacity-0': isLoading || hasError }"
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
      :class="['swipe-overlay', overlayClass]"
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useVideosStore } from '~/stores/videos'
import { useActionHint } from '~/composables/useActionHint'
import { useI18n } from '~/composables/useI18n'
import { useShareVideo } from '~/composables/useShareVideo'
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

// Overlay state
const showOverlay = computed(() => isDragging.value && swipeDirection.value !== null)
const overlayClass = computed(() => {
  if (swipeDirection.value === 'like') return 'like'
  if (swipeDirection.value === 'not_like') return 'not-like'
  if (swipeDirection.value === 'share') return 'share'
  return ''
})
const overlayText = computed(() => {
  if (swipeDirection.value === 'like') return t('videoSwiper.like')
  if (swipeDirection.value === 'not_like') return t('videoSwiper.nope')
  if (swipeDirection.value === 'share') return t('videoSwiper.share')
  return ''
})
const overlayOpacity = computed(() => {
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
 * Update gesture during movement
 * Calculates direction and prevents default scrolling for swipes
 */
const updateGesture = (e: TouchEvent | MouseEvent) => {
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
  
  // Prevent default scrolling for swipes (critical for iOS Safari)
  if (e instanceof TouchEvent && e.touches.length === 1) {
    if (absDeltaX > 10 || absDeltaY > 10) {
      e.preventDefault()
    }
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
    const seconds = Math.floor(videoElement.value.currentTime)
    emit('viewUpdate', seconds)
    
    // Detect video loop by checking if currentTime resets to near 0
    const currentTime = videoElement.value.currentTime
    const duration = videoElement.value.duration
    
    // If we were near the end and now we're near the start, video looped
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
  bottom: 6rem;
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

/* Mobile optimizations */
@media (max-width: 640px) {
  .prominent-share-button {
    bottom: 5rem;
    padding: 1rem 1.5rem;
    /* min-width: 280px; */
    border-radius: 1.25rem;
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
    bottom: 4.5rem;
    padding: 0.875rem 1.25rem;
    /* min-width: 280px; */
    max-width: 85%;
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
