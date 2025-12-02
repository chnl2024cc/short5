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
        <p class="text-sm">Loading video...</p>
      </div>
    </div>

    <!-- Error State -->
    <div
      v-if="hasError && !isRetrying"
      class="absolute inset-0 flex items-center justify-center bg-black/80 z-10"
    >
      <div class="text-center text-white px-4">
        <p class="text-lg mb-2">Failed to load video</p>
        <p class="text-sm text-gray-400 mb-4">{{ errorMessage }}</p>
        <button
          @click="retryVideoLoad"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          Retry
        </button>
      </div>
    </div>

    <!-- Video Thumbnail Placeholder -->
    <div
      v-if="isLoading || hasError"
      class="absolute inset-0 bg-cover bg-center"
      :style="{ backgroundImage: `url(${getAbsoluteUrl(video.thumbnail)})` }"
    >
      <div class="absolute inset-0 bg-black/40"></div>
    </div>

    <video
      ref="videoElement"
      class="w-full h-full object-contain cursor-pointer"
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
    <div class="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/60 to-transparent text-white z-30">
      <h3 v-if="video.title && video.title.trim() !== '' && video.title.toLowerCase() !== 'untitled'" class="font-bold text-lg">
        {{ video.title }}
      </h3>
      <p class="text-sm">{{ video.user?.username }}</p>
      <div class="flex gap-4 mt-2 text-sm">
        <span>❤️ {{ video.stats?.likes || 0 }}</span>
        <span>👁️ {{ video.stats?.views || 0 }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useVideosStore } from '~/stores/videos'
import type { Video } from '~/types/video'

const config = useRuntimeConfig()
const backendBaseUrl = config.public.backendBaseUrl

// Helper to convert relative URLs to absolute URLs
const getAbsoluteUrl = (url: string): string => {
  // Fail fast if URL is missing (should never happen with required fields)
  if (!url) {
    throw new Error('URL is required but was missing')
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
  swiped: [direction: 'like' | 'not_like']
  viewUpdate: [seconds: number]
  error: [error: Error]
  videoStarted: []
}>()

const videosStore = useVideosStore()
const swipeContainer = ref<HTMLElement | null>(null)
const videoElement = ref<HTMLVideoElement | null>(null)

// Video state
const isLoading = ref(true)
const hasError = ref(false)
const errorMessage = ref('')
const isRetrying = ref(false)
const isBuffering = ref(false)
const isVideoPaused = ref(false) // Track video paused state for play button overlay

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
const swipeDirection = ref<'like' | 'not_like' | null>(null)
const touchStartTime = ref(0)

// Overlay state
const showOverlay = computed(() => isDragging.value && swipeDirection.value !== null)
const overlayClass = computed(() => {
  if (swipeDirection.value === 'like') return 'like'
  if (swipeDirection.value === 'not_like') return 'not-like'
  return ''
})
const overlayText = computed(() => {
  if (swipeDirection.value === 'like') return 'LIKE'
  if (swipeDirection.value === 'not_like') return 'NOPE'
  return ''
})
const overlayOpacity = computed(() => {
  if (!isDragging.value) return 0
  const distance = Math.abs(currentX.value - startX.value)
  return Math.min(distance / 150, 1)
})

// Touch/Mouse handlers
const getEventCoordinates = (e: TouchEvent | MouseEvent) => {
  if (e instanceof TouchEvent) {
    const touch = e.touches[0]
    if (touch) {
      return { x: touch.clientX, y: touch.clientY }
    }
    // Fallback if no touches
    return { x: 0, y: 0 }
  }
  // It's a MouseEvent
  return { x: e.clientX, y: e.clientY }
}

const onTouchStart = (e: TouchEvent) => {
  const coords = getEventCoordinates(e)
  startX.value = coords.x
  startY.value = coords.y
  isDragging.value = true
  // Store touch start time for tap detection
  touchStartTime.value = Date.now()
}

const onMouseDown = (e: MouseEvent) => {
  const coords = getEventCoordinates(e)
  startX.value = coords.x
  startY.value = coords.y
  isDragging.value = true
  // Store mouse down time for click detection
  touchStartTime.value = Date.now()
}

const onTouchMove = (e: TouchEvent) => {
  if (!isDragging.value) return
  e.preventDefault()
  const coords = getEventCoordinates(e)
  currentX.value = coords.x
  currentY.value = coords.y
  updateSwipeDirection()
}

const onMouseMove = (e: MouseEvent) => {
  if (!isDragging.value) return
  const coords = getEventCoordinates(e)
  currentX.value = coords.x
  currentY.value = coords.y
  updateSwipeDirection()
}

const updateSwipeDirection = () => {
  const deltaX = currentX.value - startX.value
  const deltaY = Math.abs(currentY.value - startY.value)
  
  // Only consider horizontal swipes (ignore vertical scrolling)
  if (Math.abs(deltaX) > deltaY && Math.abs(deltaX) > 50) {
    swipeDirection.value = deltaX > 0 ? 'like' : 'not_like'
  } else {
    swipeDirection.value = null
  }
}

const onTouchEnd = () => {
  handleSwipeEnd()
}

const onMouseEnd = () => {
  handleSwipeEnd()
}

// Handle direct clicks on container (fallback for tap detection)
const handleContainerClick = (e: MouseEvent) => {
  // Only handle if it's a simple click (not part of a drag)
  if (!isDragging.value) {
    // Check if click target is the container or video (not a button or overlay)
    const target = e.target as HTMLElement
    if (target === swipeContainer.value || target === videoElement.value || target.closest('.video-container')) {
      // Small delay to avoid double-triggering with touch events
      setTimeout(() => {
        if (!isDragging.value) {
          togglePlayPause()
        }
      }, 100)
    }
  }
}

const handleSwipeEnd = () => {
  if (!isDragging.value) return
  
  const deltaX = currentX.value - startX.value
  const deltaY = Math.abs(currentY.value - startY.value)
  const threshold = 100 // Minimum swipe distance
  const touchDuration = Date.now() - touchStartTime.value
  const isTap = Math.abs(deltaX) < 10 && deltaY < 10 && touchDuration < 300 // Tap if movement < 10px and duration < 300ms
  
  if (Math.abs(deltaX) > threshold && swipeDirection.value) {
    // Swipe completed
    emit('swiped', swipeDirection.value)
    // Vote on video
    videosStore.voteOnVideo(props.video.id, swipeDirection.value)
  } else if (isTap) {
    // It's a tap/click - toggle play/pause
    togglePlayPause()
  }
  
  // Reset
  isDragging.value = false
  swipeDirection.value = null
  currentX.value = 0
  currentY.value = 0
  touchStartTime.value = 0
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
    // Fail fast if url_mp4 is missing
    if (!props.video.url_mp4) {
      throw new Error(`Video ${props.video.id} is missing url_mp4 - invalid state`)
    }
    
    // Simple MP4 playback - works in all modern browsers
    const mp4Src = getAbsoluteUrl(props.video.url_mp4)
    if (!mp4Src) {
      throw new Error('MP4 URL is invalid or could not be resolved')
    }
    console.log(`[VideoSwiper] Loading MP4: ${mp4Src}`)
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
  (isActive) => {
    if (!videoElement.value) return
    
    if (isActive && !isLoading.value && !hasError.value) {
      videoElement.value.play().catch((err) => {
        console.warn('Play failed:', err)
      })
    } else if (!isActive) {
      videoElement.value.pause()
    }
  }
)

// Cleanup function
const cleanupVideo = () => {
  // Clear timeouts
  if (retryTimeout) {
    clearTimeout(retryTimeout)
    retryTimeout = null
  }
  if (bufferingTimeout) {
    clearTimeout(bufferingTimeout)
    bufferingTimeout = null
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
    videoElement.value.play().catch((err) => {
      console.warn('Autoplay blocked:', err)
      // Autoplay blocked, user interaction required
    })
  }
}

const onVideoCanPlay = () => {
  isLoading.value = false
  isBuffering.value = false
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
  // Initialize video playback when component is mounted
  if (process.client) {
    nextTick(() => {
      initializeVideo()
    })
  }
})

onUnmounted(() => {
  // Complete cleanup
  cleanupVideo()
})
</script>

<style scoped>
@reference "tailwindcss";

.video-container {
  @apply relative w-full h-screen flex items-center justify-center bg-black touch-none;
  user-select: none;
  -webkit-user-select: none;
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

.swipe-overlay-text {
  @apply text-6xl font-bold text-white;
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
</style>
