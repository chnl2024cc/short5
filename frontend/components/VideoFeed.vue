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
        :is-active="index === currentIndex"
        class="absolute inset-0"
        :style="{ zIndex: videos.length - index }"
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

const videosStore = useVideosStore()
const api = useApi()

const videos = ref<Video[]>([])
const currentIndex = ref(0)
const loading = ref(false)
const nextCursor = ref<string | null>(null)
const hasMore = ref(true)
const preloadCount = 2 // Preload next 2 videos

const visibleVideos = computed(() => {
  // Show current video + next preloadCount videos
  return videos.value.slice(currentIndex.value, currentIndex.value + preloadCount + 1)
})

const loadFeed = async (cursor?: string) => {
  if (loading.value || (!hasMore.value && cursor)) return
  
  loading.value = true
  try {
    const response = await api.get<FeedResponse>(`/feed${cursor ? `?cursor=${cursor}` : ''}`)
    
    if (cursor) {
      // Append to existing videos
      videos.value.push(...response.videos)
    } else {
      // Replace videos
      videos.value = response.videos
      currentIndex.value = 0
    }
    
    nextCursor.value = response.next_cursor
    hasMore.value = response.has_more
    
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

// Load feed on mount
onMounted(() => {
  loadFeed()
})

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
