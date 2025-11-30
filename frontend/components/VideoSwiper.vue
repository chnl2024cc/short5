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
      v-if="video.thumbnail && (isLoading || hasError)"
      class="absolute inset-0 bg-cover bg-center"
      :style="{ backgroundImage: `url(${video.thumbnail})` }"
    >
      <div class="absolute inset-0 bg-black/40"></div>
    </div>

    <video
      ref="videoElement"
      class="w-full h-full object-contain"
      :class="{ 'opacity-0': isLoading || hasError }"
      :autoplay="isActive && !isLoading && !hasError"
      :muted="true"
      :loop="true"
      playsinline
      preload="auto"
      @loadedmetadata="onVideoLoaded"
      @timeupdate="onTimeUpdate"
      @waiting="onVideoWaiting"
      @playing="onVideoPlaying"
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
    >
      <div class="swipe-overlay-text">
        {{ overlayText }}
      </div>
    </div>
    
    <!-- Video Info Overlay -->
    <div class="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/60 to-transparent text-white z-30">
      <h3 class="font-bold text-lg">{{ video.title || 'Untitled' }}</h3>
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
const backendBaseUrl = config.public.backendBaseUrl || 'http://localhost:8000'

// Helper to convert relative URLs to absolute URLs
const getAbsoluteUrl = (url: string | null | undefined): string | null => {
  if (!url) return null
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

// Lazy load hls.js - using function to prevent Vite from analyzing at build time
let hlsModule: any = null
let hlsLoaded = false

const loadHls = async (): Promise<any> => {
  if (!process.client) return null
  
  if (hlsLoaded && hlsModule) {
    return hlsModule
  }
  
  try {
    // Use dynamic import with string literal to prevent static analysis
    const moduleName = 'hls.js'
    hlsModule = await import(/* @vite-ignore */ moduleName)
    hlsModule = hlsModule.default || hlsModule
    hlsLoaded = true
    return hlsModule
  } catch (err) {
    console.warn('Failed to load hls.js:', err)
    return null
  }
}

// Get Hls - returns the loaded Hls class
const getHls = async () => {
  if (process.client) {
    return await loadHls()
  }
  return null
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
}>()

const videosStore = useVideosStore()
const swipeContainer = ref<HTMLElement | null>(null)
const videoElement = ref<HTMLVideoElement | null>(null)
let hlsInstance: any = null // Hls instance (type from hls.js library loaded via plugin)

// Video state
const isLoading = ref(true)
const hasError = ref(false)
const errorMessage = ref('')
const isRetrying = ref(false)
const isBuffering = ref(false)
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
}

const onMouseDown = (e: MouseEvent) => {
  const coords = getEventCoordinates(e)
  startX.value = coords.x
  startY.value = coords.y
  isDragging.value = true
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

const handleSwipeEnd = () => {
  if (!isDragging.value) return
  
  const deltaX = currentX.value - startX.value
  const threshold = 100 // Minimum swipe distance
  
  if (Math.abs(deltaX) > threshold && swipeDirection.value) {
    // Swipe completed
    emit('swiped', swipeDirection.value)
    // Vote on video
    videosStore.voteOnVideo(props.video.id, swipeDirection.value)
  }
  
  // Reset
  isDragging.value = false
  swipeDirection.value = null
  currentX.value = 0
  currentY.value = 0
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
  
  // Clean up previous HLS instance
  if (hlsInstance) {
    try {
      hlsInstance.destroy()
    } catch (e) {
      console.warn('Error destroying HLS instance:', e)
    }
    hlsInstance = null
  }
  
  // Clear any existing retry timeout
  if (retryTimeout) {
    clearTimeout(retryTimeout)
    retryTimeout = null
  }
  
  try {
    // Handle HLS playback
    if (props.video.url_hls) {
      const hlsSrc = getAbsoluteUrl(props.video.url_hls)
      if (!hlsSrc) {
        throw new Error('HLS URL is invalid')
      }
      
      console.log(`[VideoSwiper] Loading HLS from: ${hlsSrc}`)
      
      // Check if browser supports native HLS (Safari)
      if (video.canPlayType('application/vnd.apple.mpegurl')) {
        // Native HLS support (Safari)
        video.src = hlsSrc
        video.load()
        
        // Set up error handlers for native HLS
        video.addEventListener('error', handleNativeVideoError, { once: true })
      } else {
        // Load hls.js dynamically for browsers with MSE support (Chrome, Firefox, Edge)
        const Hls = await loadHls()
        
        if (Hls && Hls.isSupported()) {
          // Use hls.js for browsers with MSE support
          hlsInstance = new Hls({
          enableWorker: true,
          lowLatencyMode: false,
          backBufferLength: 90,
          maxBufferLength: 30,
          maxMaxBufferLength: 60,
          maxBufferSize: 60 * 1000 * 1000, // 60MB
          maxBufferHole: 0.5,
          highBufferWatchdogPeriod: 2,
          nudgeOffset: 0.1,
          nudgeMaxRetry: 3,
          maxFragLoadingTimeOut: 20,
          fragLoadingTimeOut: 20,
          manifestLoadingTimeOut: 10,
          levelLoadingTimeOut: 10,
        })
        
        hlsInstance.loadSource(hlsSrc)
        hlsInstance.attachMedia(video)
        
        hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
          isLoading.value = false
          if (props.isActive) {
            video.play().catch((err) => {
              console.warn('Autoplay blocked:', err)
              // Autoplay blocked, user interaction required
            })
          }
        })
        
        hlsInstance.on(Hls.Events.ERROR, (event: any, data: any) => {
          handleHlsError(data)
        })
        
        // Monitor buffering
          hlsInstance.on(Hls.Events.BUFFER_APPENDING, () => {
            isBuffering.value = false
            if (bufferingTimeout) {
              clearTimeout(bufferingTimeout)
              bufferingTimeout = null
            }
          })
        } else {
          console.warn('HLS.js not available or not supported, falling back to MP4')
          // Fallback to MP4 if available
          const mp4Src = getAbsoluteUrl(props.video.url_mp4)
          if (mp4Src) {
            console.log(`[VideoSwiper] Falling back to MP4: ${mp4Src}`)
            video.src = mp4Src
            video.load()
            video.addEventListener('error', handleNativeVideoError, { once: true })
          } else {
            throw new Error('HLS not supported and no MP4 fallback available')
          }
        }
      }
    } else if (props.video.url_mp4) {
      // Direct MP4 playback (no HLS)
      const mp4Src = getAbsoluteUrl(props.video.url_mp4)
      if (!mp4Src) {
        throw new Error('MP4 URL is invalid')
      }
      console.log(`[VideoSwiper] Loading MP4: ${mp4Src}`)
      video.src = mp4Src
      video.load()
      video.addEventListener('error', handleNativeVideoError, { once: true })
    } else {
      throw new Error('No video URL available')
    }
  } catch (error: any) {
    console.error('Error initializing video:', error)
    handleVideoError(error)
  }
}

// Handle HLS-specific errors with retry logic
const handleHlsError = async (data: any) => {
  if (!process.client || !hlsInstance) return
  
  const Hls = await loadHls()
  if (!Hls) return
  
  console.error('HLS error:', data)
  
  if (data.fatal) {
    switch (data.type) {
      case Hls.ErrorTypes.NETWORK_ERROR:
        console.error('Fatal network error, attempting recovery...')
        if (retryCount.value < maxRetries) {
          retryCount.value++
          retryTimeout = setTimeout(() => {
            hlsInstance?.startLoad()
          }, retryDelay)
        } else {
          // Network error after max retries, try MP4 fallback
          console.error('Network error persists, falling back to MP4')
          await fallbackToMp4()
        }
        break
      case Hls.ErrorTypes.MEDIA_ERROR:
        console.error('Fatal media error, attempting recovery...')
        try {
          hlsInstance.recoverMediaError()
        } catch (e) {
          console.error('Media error recovery failed:', e)
          if (retryCount.value < maxRetries) {
            retryCount.value++
            retryTimeout = setTimeout(() => {
              hlsInstance?.recoverMediaError()
            }, retryDelay)
          } else {
            await fallbackToMp4()
          }
        }
        break
      default:
        console.error('Fatal HLS error, falling back to MP4')
        await fallbackToMp4()
        break
    }
  }
}

// Fallback to MP4 if HLS fails
const fallbackToMp4 = async () => {
  if (!videoElement.value || !props.video.url_mp4) {
    handleVideoError(new Error('HLS failed and no MP4 fallback available'))
    return
  }
  
  console.log('Falling back to MP4 playback')
  
  if (hlsInstance) {
    try {
      hlsInstance.destroy()
    } catch (e) {
      console.warn('Error destroying HLS during fallback:', e)
    }
    hlsInstance = null
  }
  
  const video = videoElement.value
  video.src = props.video.url_mp4
  video.load()
  video.addEventListener('error', handleNativeVideoError, { once: true })
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
  
  // Clean up HLS instance
  if (hlsInstance) {
    try {
      hlsInstance.destroy()
    } catch (e) {
      console.warn('Error destroying HLS during cleanup:', e)
    }
    hlsInstance = null
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
  if (bufferingTimeout) {
    clearTimeout(bufferingTimeout)
    bufferingTimeout = null
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
