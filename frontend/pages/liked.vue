<template>
  <div class="min-h-screen bg-black text-white">
    <!-- Header -->
    <div class="sticky top-0 z-10 bg-black/95 backdrop-blur-sm border-b border-gray-800 px-4 py-4">
      <div class="flex items-center justify-between max-w-7xl mx-auto">
        <div class="flex items-center gap-4">
          <NuxtLink
            to="/"
            class="text-gray-400 hover:text-white transition-colors"
          >
            <svg
              class="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </NuxtLink>
          <h1 class="text-2xl font-bold">Liked Videos</h1>
        </div>
        <div class="text-sm text-gray-400">
          {{ totalCount }} {{ totalCount === 1 ? 'video' : 'videos' }}
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="max-w-7xl mx-auto px-4 py-6">
      <!-- Loading State -->
      <div
        v-if="loading && videos.length === 0"
        class="flex items-center justify-center py-20"
      >
        <div class="text-center">
          <div class="text-gray-400 text-lg mb-2">Loading liked videos...</div>
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="videos.length === 0"
        class="flex flex-col items-center justify-center py-20"
      >
        <div class="text-6xl mb-4">❤️</div>
        <h2 class="text-2xl font-bold mb-2">No liked videos yet</h2>
        <p class="text-gray-400 text-center mb-6">
          Start swiping right on videos you like to save them here
        </p>
        <NuxtLink
          to="/"
          class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
        >
          Browse Feed
        </NuxtLink>
      </div>

      <!-- Video Grid -->
      <div
        v-else
        class="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 sm:gap-4"
      >
        <div
          v-for="video in videos"
          :key="video.id"
          class="bg-gray-900 rounded-lg overflow-hidden hover:bg-gray-800 transition-colors cursor-pointer relative group"
          @click="playVideo(video)"
        >
          <!-- Share Button -->
          <button
            @click.stop="handleShareVideo(video)"
            class="absolute top-2 right-2 z-5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white p-2 rounded-full touch-manipulation"
            title="Share video"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
              />
            </svg>
          </button>
          
          <!-- Thumbnail -->
          <div class="relative aspect-[9/16] bg-gray-800">
            <img
              :src="getAbsoluteUrl(video.thumbnail)"
              :alt="video.title || 'Video thumbnail'"
              class="w-full h-full object-cover"
            />
            <!-- Play Overlay -->
            <div class="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 hover:opacity-100 transition-opacity">
              <div class="bg-white/90 rounded-full p-4">
                <svg
                  class="w-8 h-8 text-black"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
            </div>

            <!-- Duration Badge -->
            <div
              v-if="video.duration_seconds"
              class="absolute bottom-2 right-2 bg-black/75 text-white text-xs px-2 py-1 rounded"
            >
              {{ formatDuration(video.duration_seconds) }}
            </div>
          </div>

          <!-- Video Info -->
          <div class="p-3">
            <h3 class="font-semibold text-sm mb-1 line-clamp-2">
              {{ video.title || 'Untitled' }}
            </h3>
            <p class="text-xs text-gray-400 mb-2">
              @{{ video.user?.username }}
            </p>
            <div class="flex items-center gap-4 text-xs text-gray-500">
              <span class="flex items-center gap-1">
                <svg
                  class="w-4 h-4"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                </svg>
                {{ video.stats?.likes || 0 }}
              </span>
              <span class="flex items-center gap-1">
                <svg
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
                {{ video.stats?.views || 0 }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Load More Button / Infinite Scroll Trigger -->
      <div
        v-if="hasMore && !loading"
        ref="loadMoreRef"
        class="flex justify-center mt-8"
      >
        <button
          @click="loadMore"
          class="bg-gray-800 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
        >
          Load More
        </button>
      </div>

      <!-- Loading More Indicator -->
      <div
        v-if="loading && videos.length > 0"
        class="flex justify-center py-8"
      >
        <div class="text-gray-400">Loading more videos...</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useVideosStore } from '~/stores/videos'

// No auth middleware - allow unauthenticated users to see their localStorage liked videos

const videosStore = useVideosStore()

// Helper to convert relative URLs to absolute URLs
const config = useRuntimeConfig()
const backendBaseUrl = config.public.backendBaseUrl

const getAbsoluteUrl = (url: string | null | undefined): string => {
  // Handle missing URLs gracefully - return placeholder instead of throwing
  if (!url) {
    return 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="600"%3E%3Crect fill="%23333" width="400" height="600"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="18" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3ENo thumbnail%3C/text%3E%3C/svg%3E'
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

const videos = ref<any[]>([])
const loading = ref(false)
const nextCursor = ref<string | null>(null)
const hasMore = ref(true)
const totalCount = computed(() => videos.value.length)

const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const loadLikedVideos = async (cursor?: string) => {
  if (loading.value || (!hasMore.value && cursor)) return
  
  loading.value = true
  try {
    const response = await videosStore.fetchLikedVideos(cursor)
    
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
      // Replace videos
      videos.value = validVideos
    }
    
    nextCursor.value = response.next_cursor
    hasMore.value = response.has_more
  } catch (error) {
    console.error('Failed to load liked videos:', error)
  } finally {
    loading.value = false
  }
}

const loadMore = () => {
  if (hasMore.value && nextCursor.value) {
    loadLikedVideos(nextCursor.value)
  }
}

const playVideo = (video: any) => {
  // Only navigate if video has url_mp4 - skip videos without it
  if (!video.url_mp4) {
    console.warn(`Cannot view video ${video.id} - missing url_mp4`)
    alert('This video is not ready for playback yet. Please try again later.')
    return
  }
  // Navigate to the feed starting at this specific video
  // The VideoFeed component will detect the ?video query param and jump to that video
  navigateTo(`/?video=${video.id}`)
}

const handleShareVideo = async (video: any) => {
  if (!process.client) return
  
  try {
    const shareUrl = `${window.location.origin}/?video=${video.id}`
    
    // Try to use Web Share API if available (mobile)
    if (navigator.share) {
      try {
        await navigator.share({
          title: video.title || 'Check out this video',
          text: video.description || '',
          url: shareUrl,
        })
        return
      } catch (err: any) {
        // User cancelled or share failed, fall back to clipboard
        if (err.name !== 'AbortError') {
          console.warn('Web Share API failed:', err)
        }
      }
    }
    
    // Fall back to clipboard
    await navigator.clipboard.writeText(shareUrl)
    alert('Link copied to clipboard!')
  } catch (error) {
    console.error('Failed to share video:', error)
    // Fallback: show the URL in an alert
    alert(`Share this link: ${window.location.origin}/?video=${video.id}`)
  }
}

// Infinite scroll using Intersection Observer
let observer: IntersectionObserver | null = null
const loadMoreRef = ref<HTMLElement | null>(null)

// Load videos on mount and set up infinite scroll
onMounted(() => {
  loadLikedVideos()
  
  // Set up intersection observer for infinite scroll
  if ('IntersectionObserver' in window) {
    observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]
        if (entry && entry.isIntersecting && hasMore.value && !loading.value && nextCursor.value) {
          loadMore()
        }
      },
      { threshold: 0.1, rootMargin: '100px' }
    )
    
    // Watch for when loadMoreRef becomes available or changes
    watch(loadMoreRef, (element, oldElement) => {
      if (observer) {
        // Disconnect from old element if it exists
        if (oldElement) {
          observer.unobserve(oldElement)
        }
        // Observe new element if it exists
        if (element) {
          observer.observe(element)
        }
      }
    }, { immediate: true })
  }
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
  }
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
