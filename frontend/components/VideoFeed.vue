<template>
  <div class="feed-container">
    <div
      v-if="videos.length === 0 && !loading"
      class="flex flex-col items-center justify-center px-4"
      style="height: 100%;"
    >
      <div class="text-center max-w-md">
        <div class="text-6xl mb-4">📹</div>
        <h2 class="text-2xl font-bold text-white mb-2">{{ t('videoFeed.noVideosAvailable') }}</h2>
        <p class="text-gray-400 mb-6">
          {{ t('videoFeed.feedEmpty') }}
        </p>
        <div class="flex flex-col gap-3 items-center">
          <button
            @click="refreshFeed"
            class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors w-full sm:w-auto text-center"
          >
            {{ t('videoFeed.refreshFeed') }}
          </button>
          <NuxtLink
            to="/liked"
            class="bg-gray-700 hover:bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold transition-colors w-full sm:w-auto text-center"
          >
            {{ t('videoFeed.viewLikedVideos') }}
          </NuxtLink>
          <NuxtLink
            v-if="isMounted && isAuthenticated"
            to="/upload"
            class="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors w-full sm:w-auto text-center"
          >
            {{ t('videoFeed.uploadVideo') }}
          </NuxtLink>
        </div>
      </div>
    </div>
    
    <div
      v-else
      class="relative w-full"
      style="height: 100%;"
    >
      <VideoSwiper
        v-for="(video, index) in visibleVideos"
        :key="video.id"
        :ref="(el) => setVideoRef(el, index)"
        :video="video"
        :is-active="index === 0"
        class="absolute inset-0"
        :style="{ zIndex: videos.length - (currentIndex + index) }"
        @swiped="handleSwipe"
        @view-update="handleViewUpdate"
        @error="handleVideoError"
      />
    </div>
    
    <!-- Loading Overlay - Shows when feed is loading -->
    <Transition name="fade">
      <div
        v-if="loading"
        class="loading-overlay"
      >
        <div class="loading-content">
          <div class="spinner">
            <div class="spinner-ring"></div>
            <div class="spinner-ring"></div>
            <div class="spinner-ring"></div>
          </div>
          <p class="loading-text">{{ t('videoFeed.loadingFeed') }}</p>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useVideosStore } from '~/stores/videos'
import { useAuthStore } from '~/stores/auth'
import { useApi } from '~/composables/useApi'
import type { Video, FeedResponse } from '~/types/video'

const route = useRoute()
const videosStore = useVideosStore()
const authStore = useAuthStore()
const api = useApi()
const { t } = useI18n()

const isAuthenticated = computed(() => authStore.isAuthenticated)

// Track if component is mounted to avoid hydration mismatches
// During SSR and initial render, don't show auth-dependent content
// After mount, initialize auth and show correct content
const isMounted = ref(false)

const videos = ref<Video[]>([])
const currentIndex = ref(0)
// Start with loading true so overlay appears immediately on page load
const loading = ref(true)
const nextCursor = ref<string | null>(null)
const hasMore = ref(true)
const preloadCount = 2 // Preload next 2 videos
const targetVideoId = ref<string | null>(null)
const searchAttempts = ref(0)
const maxSearchAttempts = 10 // Maximum number of feed loads to search for target video


// Refs for VideoSwiper components to control playback
const videoRefs = ref<Array<any>>([])

// Set video ref helper
const setVideoRef = (el: any, index: number) => {
  if (el) {
    videoRefs.value[index] = el
  }
}

const visibleVideos = computed(() => {
  // Show current video + next preloadCount videos
  return videos.value.slice(currentIndex.value, currentIndex.value + preloadCount + 1)
})

const loadTargetVideo = async (videoId: string) => {
  try {
    // Try to fetch the video directly by ID
    const video = await videosStore.getVideoStatus(videoId)
    
    // Check if video exists and is ready
    if (!video) {
      console.warn(`Video ${videoId} not found`)
      return false
    }
    if (video.status !== 'ready') {
      console.warn(`Video ${videoId} is not ready (status: ${video.status})`)
      return false
    }
    // Skip videos without url_mp4 instead of throwing error
    if (!video.url_mp4) {
      console.warn(`Video ${videoId} is missing url_mp4 - skipping`)
      return false
    }
    
    // Insert at the beginning of the feed
    videos.value.unshift(video)
    currentIndex.value = 0
    targetVideoId.value = null
    searchAttempts.value = 0
    console.log(`Loaded target video directly: ${videoId}`)
    return true
  } catch (error) {
    console.error(`Failed to load target video ${videoId}:`, error)
    return false
  }
}

const loadFeed = async (cursor?: string) => {
  // Only prevent loading more if already loading more (cursor provided)
  // Initial load should proceed even if loading is true (we just set it)
  if ((loading.value && cursor) || (!hasMore.value && cursor)) return
  
  loading.value = true
  try {
    const response = await api.get<FeedResponse>(`/feed${cursor ? `?cursor=${cursor}` : ''}`)
    
    // Filter out videos without url_mp4 - skip them instead of failing
    const validVideos = (response.videos || []).filter((video) => {
      if (!video.url_mp4) {
        console.warn(`Skipping video ${video.id} - missing url_mp4`)
        return false
      }
      return true
    })
    
    if (cursor) {
      // Append to existing videos
      videos.value.push(...validVideos)
    } else {
      // Replace videos, but preserve target video if it was loaded directly
      const routeVideoId = route.query.video as string | undefined
      const targetVideo = routeVideoId 
        ? videos.value.find(v => v.id === routeVideoId)
        : null
      
      videos.value = validVideos
      
      // If we had a target video loaded directly, make sure it's still in the list
      if (targetVideo && !videos.value.find(v => v.id === targetVideo.id)) {
        videos.value.unshift(targetVideo)
        currentIndex.value = 0 // Target video is at index 0
      } else {
        currentIndex.value = 0
      }
    }
    
    nextCursor.value = response.next_cursor
    hasMore.value = response.has_more
    
    // Check if we're looking for a specific video (from route query or targetVideoId)
    const routeVideoId = route.query.video as string | undefined
    const searchVideoId = targetVideoId.value || routeVideoId
    
    if (searchVideoId) {
      const targetIndex = videos.value.findIndex(v => v.id === searchVideoId)
      if (targetIndex >= 0) {
        // Found the target video!
        // If it's not at index 0, move it there so it plays immediately
        if (targetIndex !== 0) {
          const targetVideo = videos.value[targetIndex]
          if (targetVideo) {
            videos.value.splice(targetIndex, 1)
            videos.value.unshift(targetVideo)
          }
        }
        currentIndex.value = 0
        targetVideoId.value = null // Clear target
        searchAttempts.value = 0
      } else if (hasMore.value && searchAttempts.value < maxSearchAttempts) {
        // Not found yet, keep searching
        searchAttempts.value++
        await loadFeed(nextCursor.value || undefined)
        return
      } else {
        // Not found in feed - try to load it directly
        console.log(`Video ${searchVideoId} not found in feed, trying to load directly...`)
        const loaded = await loadTargetVideo(searchVideoId)
        if (!loaded) {
          // Video might not be ready or user has already voted on it
          console.warn(`Could not load target video ${searchVideoId}`)
          targetVideoId.value = null
          searchAttempts.value = 0
        }
      }
    }
    
    // Preload next videos if needed
    if (hasMore.value && videos.value.length - currentIndex.value < preloadCount + 1) {
      await loadFeed(nextCursor.value || undefined)
    }
  } catch (error) {
    console.error('Failed to load feed:', error)
  } finally {
    loading.value = false
  }
}

const handleSwipe = async (direction: 'like' | 'not_like' | 'share') => {
  const currentVideo = videos.value[currentIndex.value]
  if (!currentVideo) return
  
  // Share swipe doesn't remove video from feed
  if (direction === 'share') {
    // Share functionality is handled in VideoSwiper component
    // Video stays in feed, no need to remove or advance
    return
  }
  
  // IMPORTANT: Get reference to next video BEFORE removing current video
  // The next video is at index 1 (since index 0 is the current one being swiped)
  const nextVideoRef = videoRefs.value[1]
  
  // Remove swiped video from feed
  videos.value.splice(currentIndex.value, 1)
  
  // IMPORTANT: Play the next video immediately while we still have user gesture context
  // This is critical for iOS Safari which requires user interaction to play videos
  // The next video is now at index 0 after the splice
  await nextTick()
  const activeVideoRef = videoRefs.value[0] || nextVideoRef
  if (activeVideoRef && typeof activeVideoRef.playVideo === 'function') {
    // Call playVideo immediately to use the swipe gesture context
    // Use setTimeout(0) to ensure it runs in the same event loop but after DOM update
    setTimeout(() => {
      activeVideoRef.playVideo().catch((err: any) => {
        console.warn('Failed to play next video after swipe:', err)
      })
    }, 0)
  }
  
  // If we're at the end, try to load more
  if (currentIndex.value >= videos.value.length - preloadCount && hasMore.value) {
    await loadFeed(nextCursor.value || undefined)
  }
  
  // Don't increment index since we removed the current video
  // The next video is now at currentIndex
}

const handleViewUpdate = async (seconds: number) => {
  const currentVideo = videos.value[currentIndex.value]
  if (!currentVideo) return
  
  // Update view every 5 seconds
  if (seconds % 5 === 0) {
    try {
      await api.post(`/videos/${currentVideo.id}/view`, {
        watched_seconds: seconds,
      })
    } catch (error) {
      console.error('Failed to update view:', error)
    }
  }
}

const handleVideoError = (error: Error) => {
  console.error('Video playback error:', error)
  // Remove the problematic video from feed and move to next
  const currentVideo = videos.value[currentIndex.value]
  if (currentVideo) {
    videos.value.splice(currentIndex.value, 1)
    // If we're at the end, try to load more
    if (currentIndex.value >= videos.value.length - preloadCount && hasMore.value) {
      loadFeed(nextCursor.value || undefined)
    }
  }
}

// Function to ensure target video is active
const ensureTargetVideoActive = async () => {
  const routeVideoId = route.query.video as string | undefined
  if (!routeVideoId) return
  
  // Check if video is already in the list
  const targetVideo = videos.value.find(v => v.id === routeVideoId)
  if (targetVideo) {
    const targetIndex = videos.value.indexOf(targetVideo)
    // Move to index 0 if not already there
    if (targetIndex !== 0) {
      videos.value.splice(targetIndex, 1)
      videos.value.unshift(targetVideo)
    }
    currentIndex.value = 0
    return
  }
  
  // Try to load it directly
  const loaded = await loadTargetVideo(routeVideoId)
  if (loaded) {
    currentIndex.value = 0
  } else {
    // Set target for feed search
    targetVideoId.value = routeVideoId
  }
}


// Track share click when a shared link is opened
const trackShareClick = async (videoId: string, sharerId: string) => {
  if (!process.client) return
  
  try {
    // Get clicker's session_id (the person who opened the link)
    const { useSession } = await import('~/composables/useSession')
    const { getOrCreateSessionId } = useSession()
    const clickerId = getOrCreateSessionId()
    
    // Track share click - creates new click record (allows multiple clicks per share)
    const clickPayload: { sharer_session_id: string; clicker_session_id: string } = {
      sharer_session_id: sharerId, // Who created the share
      clicker_session_id: clickerId, // Who opened the link
    }
    
    await api.post(`/videos/${videoId}/share/click`, clickPayload)
    console.log(`Tracked share click for video ${videoId} - sharer: ${sharerId}, clicker: ${clickerId}`)
  } catch (error) {
    // Don't block user experience if share tracking fails
    console.warn('Failed to track share click:', error)
  }
}

const initializeFeed = async () => {
  // Reset feed state
  videos.value = []
  currentIndex.value = 0
  nextCursor.value = null
  hasMore.value = true
  searchAttempts.value = 0
  targetVideoId.value = null
  
  // Check if there's a video query parameter
  const videoId = route.query.video as string | undefined
  const sharerId = route.query.ref as string | undefined
  
  // Track share click if both video and ref parameters are present
  if (videoId && sharerId && process.client) {
    // Track share click asynchronously (don't block feed loading)
    trackShareClick(videoId, sharerId)
  }
  
  if (videoId) {
    targetVideoId.value = videoId
    // Try to load the target video directly first
    const loaded = await loadTargetVideo(videoId)
    if (!loaded) {
      // If direct load fails, it will be searched in the feed
      console.log(`Direct load failed, will search in feed for: ${videoId}`)
    } else {
      // Video loaded, ensure it's active
      currentIndex.value = 0
    }
  }
  // Load the feed (will search for target video if not already loaded)
  await loadFeed()
  
  // After feed loads, ensure target video is active
  await ensureTargetVideoActive()
}

const refreshFeed = async () => {
  isRefreshing = true
  try {
    // Clear any query parameters and refresh the feed
    if (route.path !== '/' || route.query.video) {
      // Navigate to "/" to clear query parameters
      await navigateTo('/', { replace: true })
    }
    // Always refresh the feed
    await initializeFeed()
  } finally {
    isRefreshing = false
  }
}

onMounted(async () => {
  // Initialize auth store from localStorage
  if (process.client) {
    authStore.initFromStorage()
    // Set mounted flag after auth is initialized to trigger reactive update
    isMounted.value = true
  }
  await initializeFeed()
})

// Watch for route changes (e.g., navigating to "/" to refresh)
// Only trigger on actual route changes, not when refreshFeed() is called directly
let isRefreshing = false
watch(
  () => [route.path, route.query.video],
  async ([newPath, newVideoId], [oldPath, oldVideoId]) => {
    // If navigating to "/" (feed page) and it's a different route or video query changed
    // Don't trigger if we're already refreshing (to avoid double-loading)
    if (newPath === '/' && (oldPath !== newPath || oldVideoId !== newVideoId) && !isRefreshing) {
      await initializeFeed()
    }
  }
)

// Watch for route query changes (e.g., user navigates with different video ID)
watch(
  () => route.query.video,
  async (newVideoId) => {
    if (newVideoId) {
      targetVideoId.value = newVideoId as string
      await ensureTargetVideoActive()
    }
  }
)

// Watch for when we need to load more
watch(
  () => currentIndex.value,
  (newIndex) => {
    // Load more when we're close to the end
    if (newIndex >= videos.value.length - preloadCount && hasMore.value && !loading.value) {
      loadFeed(nextCursor.value || undefined)
    }
  }
)

// Watch for video changes and ensure the active video plays (fallback for iOS Safari)
watch(
  () => visibleVideos.value[0]?.id,
  async (newVideoId) => {
    if (newVideoId) {
      // Small delay to ensure DOM is updated
      await nextTick()
      const activeVideoRef = videoRefs.value[0]
      if (activeVideoRef && typeof activeVideoRef.playVideo === 'function') {
        // Try to play, but this might fail on iOS Safari without user gesture
        activeVideoRef.playVideo().catch(() => {
          // Silent fail - user will need to tap to play
        })
      }
    }
  }
)
</script>

<style scoped>
.feed-container {
  position: relative;
  width: 100%;
  /* Fill parent container (page-container) which uses viewport units */
  height: 100%;
  min-height: 100%;
  overflow: hidden;
  background-color: black;
}

.feed-container video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* Loading Overlay Styles */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  text-align: center;
}

/* Modern Spinner Animation */
.spinner {
  position: relative;
  width: 64px;
  height: 64px;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}

.spinner-ring:nth-child(1) {
  animation-delay: -0.45s;
}

.spinner-ring:nth-child(2) {
  animation-delay: -0.3s;
  border-top-color: #60a5fa;
  width: 80%;
  height: 80%;
  top: 10%;
  left: 10%;
}

.spinner-ring:nth-child(3) {
  animation-delay: -0.15s;
  border-top-color: #93c5fd;
  width: 60%;
  height: 60%;
  top: 20%;
  left: 20%;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-text {
  color: white;
  font-size: 1rem;
  font-weight: 500;
  letter-spacing: 0.025em;
  margin: 0;
}

/* Fade Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, backdrop-filter 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  backdrop-filter: blur(0px);
  -webkit-backdrop-filter: blur(0px);
}

/* Mobile Optimizations */
@media (max-width: 640px) {
  .spinner {
    width: 56px;
    height: 56px;
  }
  
  .spinner-ring {
    border-width: 2.5px;
  }
  
  .loading-text {
    font-size: 0.9rem;
  }
  
  .loading-content {
    gap: 1.25rem;
  }
}

/* Small Mobile */
@media (max-width: 375px) {
  .spinner {
    width: 48px;
    height: 48px;
  }
  
  .spinner-ring {
    border-width: 2px;
  }
  
  .loading-text {
    font-size: 0.85rem;
  }
}
</style>
