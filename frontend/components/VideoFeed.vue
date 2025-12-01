<template>
  <div class="feed-container">
    <div
      v-if="loading && videos.length === 0"
      class="flex items-center justify-center h-screen"
    >
      <div class="text-white text-xl">Loading feed...</div>
    </div>
    
    <div
      v-else-if="videos.length === 0"
      class="flex items-center justify-center h-screen"
    >
      <div class="text-white text-xl">No videos available</div>
    </div>
    
    <div
      v-else
      class="relative w-full h-screen"
    >
      <VideoSwiper
        v-for="(video, index) in visibleVideos"
        :key="video.id"
        :video="video"
        :is-active="index === 0"
        class="absolute inset-0"
        :style="{ zIndex: videos.length - (currentIndex + index) }"
        @swiped="handleSwipe"
        @view-update="handleViewUpdate"
        @error="handleVideoError"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useVideosStore } from '~/stores/videos'
import { useApi } from '~/composables/useApi'
import type { Video, FeedResponse } from '~/types/video'

const route = useRoute()
const videosStore = useVideosStore()
const api = useApi()

const videos = ref<Video[]>([])
const currentIndex = ref(0)
const loading = ref(false)
const nextCursor = ref<string | null>(null)
const hasMore = ref(true)
const preloadCount = 2 // Preload next 2 videos
const targetVideoId = ref<string | null>(null)
const searchAttempts = ref(0)
const maxSearchAttempts = 10 // Maximum number of feed loads to search for target video

const visibleVideos = computed(() => {
  // Show current video + next preloadCount videos
  return videos.value.slice(currentIndex.value, currentIndex.value + preloadCount + 1)
})

const loadTargetVideo = async (videoId: string) => {
  try {
    // Try to fetch the video directly by ID
    const video = await videosStore.getVideoStatus(videoId)
    
    // Check if video is ready and has MP4
    if (video && video.status === 'ready' && video.url_mp4) {
      // Insert at the beginning of the feed
      videos.value.unshift(video)
      currentIndex.value = 0
      targetVideoId.value = null
      searchAttempts.value = 0
      console.log(`Loaded target video directly: ${videoId}`)
      return true
    } else {
      console.warn(`Video ${videoId} is not ready or has no MP4: status=${video?.status}, url_mp4=${video?.url_mp4}`)
      return false
    }
  } catch (error) {
    console.error(`Failed to load target video ${videoId}:`, error)
    return false
  }
}

const loadFeed = async (cursor?: string) => {
  if (loading.value || (!hasMore.value && cursor)) return
  
  loading.value = true
  try {
    const response = await api.get<FeedResponse>(`/feed${cursor ? `?cursor=${cursor}` : ''}`)
    
    if (cursor) {
      // Append to existing videos
      videos.value.push(...response.videos)
    } else {
      // Replace videos, but preserve target video if it was loaded directly
      const routeVideoId = route.query.video as string | undefined
      const targetVideo = routeVideoId 
        ? videos.value.find(v => v.id === routeVideoId)
        : null
      
      videos.value = response.videos
      
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

const handleSwipe = async (direction: 'like' | 'not_like') => {
  const currentVideo = videos.value[currentIndex.value]
  if (!currentVideo) return
  
  // Remove swiped video from feed
  videos.value.splice(currentIndex.value, 1)
  
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

// Load feed on mount
onMounted(async () => {
  // Check if there's a video query parameter
  const videoId = route.query.video as string | undefined
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
})

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
</script>

<style scoped>
@reference "tailwindcss";

.feed-container {
  @apply relative w-full h-screen overflow-hidden bg-black;
}

.feed-container video {
  @apply w-full h-full object-contain;
}
</style>
