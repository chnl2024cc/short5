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
    <video
      ref="videoElement"
      :src="video.url_hls || video.url_mp4"
      class="w-full h-full object-contain"
      :autoplay="isActive"
      :muted="true"
      :loop="true"
      playsinline
      @loadedmetadata="onVideoLoaded"
      @timeupdate="onTimeUpdate"
    />
    
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
    <div class="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/60 to-transparent text-white">
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useVideosStore } from '~/stores/videos'

interface Props {
  video: {
    id: string
    title?: string
    description?: string
    url_hls?: string
    url_mp4?: string
    thumbnail?: string
    user?: {
      id: string
      username: string
    }
    stats?: {
      likes: number
      views: number
    }
  }
  isActive?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isActive: true,
})

const emit = defineEmits<{
  swiped: [direction: 'like' | 'not_like']
  viewUpdate: [seconds: number]
}>()

const videosStore = useVideosStore()
const swipeContainer = ref<HTMLElement | null>(null)
const videoElement = ref<HTMLVideoElement | null>(null)

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

// Video handlers
const onVideoLoaded = () => {
  if (videoElement.value && props.isActive) {
    videoElement.value.play().catch(() => {
      // Autoplay blocked, user interaction required
    })
  }
}

const onTimeUpdate = () => {
  if (videoElement.value && props.isActive) {
    const seconds = Math.floor(videoElement.value.currentTime)
    emit('viewUpdate', seconds)
  }
}

onMounted(() => {
  if (props.isActive && videoElement.value) {
    videoElement.value.play().catch(() => {
      // Autoplay may be blocked
    })
  }
})

onUnmounted(() => {
  if (videoElement.value) {
    videoElement.value.pause()
  }
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
</style>
