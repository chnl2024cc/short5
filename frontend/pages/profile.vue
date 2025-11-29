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
          <h1 class="text-2xl font-bold">Profile</h1>
        </div>
        <button
          @click="handleLogout"
          class="text-gray-400 hover:text-white transition-colors text-sm"
        >
          Logout
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="max-w-4xl mx-auto px-4 py-6">
      <!-- Profile Loading State -->
      <div
        v-if="profilePending"
        class="flex items-center justify-center py-20"
      >
        <div class="text-gray-400 text-lg">Loading profile...</div>
      </div>

      <!-- Profile Error State -->
      <div
        v-else-if="profileError"
        class="bg-red-900/50 border border-red-700 rounded-lg p-6 text-center"
      >
        <p class="text-red-300 mb-4">
          {{ profileError.message || 'Failed to load profile' }}
        </p>
        <button
          @click="handleRefreshProfile"
          class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg"
        >
          Retry
        </button>
      </div>

      <!-- Profile Content -->
      <div v-else-if="profile" class="space-y-6">
        <!-- Profile Header -->
        <div class="bg-gray-900 rounded-lg p-6">
          <div class="flex items-start gap-6">
            <!-- Avatar -->
            <div class="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-3xl font-bold">
              {{ profile.username?.charAt(0)?.toUpperCase() || 'U' }}
            </div>
            
            <!-- User Info -->
            <div class="flex-1">
              <h2 class="text-3xl font-bold mb-2">{{ profile.username || 'User' }}</h2>
              <p class="text-gray-400 mb-4">{{ profile.email || '' }}</p>
              <p v-if="profile.created_at" class="text-sm text-gray-500">
                Joined {{ formatDate(profile.created_at) }}
              </p>
            </div>
          </div>
        </div>

        <!-- Stats Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="bg-gray-900 rounded-lg p-6 text-center">
            <div class="text-3xl font-bold text-blue-400 mb-2">
              {{ profile.stats?.videos_uploaded || 0 }}
            </div>
            <div class="text-sm text-gray-400">Videos Uploaded</div>
          </div>
          
          <div class="bg-gray-900 rounded-lg p-6 text-center">
            <div class="text-3xl font-bold text-red-400 mb-2">
              {{ formatNumber(profile.stats?.total_likes_received || 0) }}
            </div>
            <div class="text-sm text-gray-400">Likes Received</div>
          </div>
          
          <div class="bg-gray-900 rounded-lg p-6 text-center">
            <div class="text-3xl font-bold text-green-400 mb-2">
              {{ formatNumber(profile.stats?.total_views || 0) }}
            </div>
            <div class="text-sm text-gray-400">Total Views</div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <NuxtLink
            to="/upload"
            class="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4v16m8-8H4"
              />
            </svg>
            Upload Video
          </NuxtLink>
          
          <NuxtLink
            to="/liked"
            class="bg-gray-800 hover:bg-gray-700 text-white p-4 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
          >
            <svg
              class="w-5 h-5"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
            </svg>
            Liked Videos
          </NuxtLink>
        </div>

        <!-- My Videos Section -->
        <div class="mt-8">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-xl font-bold">My Videos</h3>
            <NuxtLink
              to="/upload"
              class="text-blue-400 hover:text-blue-300 text-sm"
            >
              Upload New
            </NuxtLink>
          </div>

          <!-- Loading Videos -->
          <div
            v-if="videosPending && videos.length === 0"
            class="text-center py-8 text-gray-400"
          >
            Loading videos...
          </div>

          <!-- Videos Error -->
          <div
            v-else-if="videosError && videos.length === 0"
            class="bg-gray-900 rounded-lg p-6 text-center text-gray-400"
          >
            <p>Failed to load videos. <button @click="refreshVideos" class="text-blue-400 hover:text-blue-300 underline">Retry</button></p>
          </div>

          <!-- Empty State -->
          <div
            v-else-if="videos.length === 0"
            class="bg-gray-900 rounded-lg p-12 text-center"
          >
            <div class="text-6xl mb-4">📹</div>
            <h4 class="text-xl font-bold mb-2">No videos yet</h4>
            <p class="text-gray-400 mb-6">
              Start sharing your content with the community
            </p>
            <NuxtLink
              to="/upload"
              class="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
            >
              Upload Your First Video
            </NuxtLink>
          </div>

          <!-- Videos Grid -->
          <div
            v-else
            class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            <div
              v-for="video in videos"
              :key="video.id"
              class="bg-gray-900 rounded-lg overflow-hidden hover:bg-gray-800 transition-colors cursor-pointer relative group"
              @click="viewVideo(video)"
            >
              <!-- Delete Button -->
              <button
                @click.stop="handleDeleteVideo(video)"
                :disabled="isDeleting === video.id"
                class="absolute top-2 right-2 z-10 bg-red-600 hover:bg-red-700 disabled:bg-red-800 disabled:opacity-50 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                title="Delete video"
              >
                <svg
                  v-if="isDeleting !== video.id"
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
                <svg
                  v-else
                  class="w-4 h-4 animate-spin"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
              </button>
              
              <!-- Thumbnail -->
              <div class="relative aspect-[9/16] bg-gray-800">
                <img
                  v-if="video.thumbnail"
                  :src="video.thumbnail"
                  :alt="video.title || 'Video thumbnail'"
                  class="w-full h-full object-cover"
                />
                <div
                  v-else
                  class="w-full h-full flex items-center justify-center text-gray-600"
                >
                  <svg
                    class="w-16 h-16"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                
                <!-- Status Badge -->
                <div
                  v-if="video.status && video.status !== 'ready'"
                  class="absolute top-2 left-2 bg-yellow-600 text-white text-xs px-2 py-1 rounded"
                >
                  {{ getStatusLabel(video.status) }}
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
                <h4 class="font-semibold text-sm mb-1 line-clamp-2">
                  {{ video.title || 'Untitled' }}
                </h4>
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

          <!-- Load More -->
          <div
            v-if="hasMoreVideos && !videosPending && videos.length > 0"
            class="flex justify-center mt-6"
          >
            <button
              @click="loadMoreVideos"
              class="bg-gray-800 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
            >
              Load More
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { useApi } from '~/composables/useApi'

definePageMeta({
  middleware: 'auth',
})

const authStore = useAuthStore()
const api = useApi()

// Profile data using useAsyncData (Nuxt best practice)
const {
  data: profile,
  pending: profilePending,
  error: profileError,
  refresh: refreshProfile,
} = await useAsyncData(
  'user-profile',
  async () => {
    // Initialize auth from storage if needed
    if (process.client && !authStore.token) {
      authStore.initFromStorage()
    }
    return await authStore.fetchProfile()
  },
  {
    server: false, // Only fetch on client since it requires auth
    lazy: true, // Don't block navigation
    default: () => null,
  }
)

// Videos data - using manual loading for pagination support
const videos = ref<any[]>([])
const videosPending = ref(false)
const videosError = ref<Error | null>(null)
const videosCursor = ref<string | null>(null)
const hasMoreVideos = ref(true)
const isDeleting = ref<string | null>(null)

const loadVideos = async (cursor?: string | null) => {
  if (videosPending.value || (!hasMoreVideos.value && cursor)) return
  
  videosPending.value = true
  videosError.value = null
  
  try {
    const response = await api.get<{
      videos: any[]
      next_cursor: string | null
      has_more: boolean
    }>(`/users/me/videos${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ''}`)
    
    if (cursor) {
      videos.value.push(...(response.videos || []))
    } else {
      videos.value = response.videos || []
    }
    
    videosCursor.value = response.next_cursor
    hasMoreVideos.value = response.has_more || false
  } catch (err: any) {
    console.error('Failed to load videos:', err)
    videosError.value = err
  } finally {
    videosPending.value = false
  }
}

const refreshVideos = () => {
  videosCursor.value = null
  hasMoreVideos.value = true
  loadVideos()
}

const handleRefreshProfile = () => {
  refreshProfile()
}

// Load initial videos
onMounted(() => {
  loadVideos()
})

const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return 'Unknown date'
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return 'Invalid date'
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  } catch (e) {
    console.error('Error formatting date:', e)
    return 'Invalid date'
  }
}

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatDuration = (seconds: number): string => {
  if (!seconds || seconds < 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const getStatusLabel = (status: string): string => {
  const statusMap: Record<string, string> = {
    uploading: 'Uploading...',
    processing: 'Processing...',
    ready: 'Ready',
    failed: 'Failed',
    rejected: 'Rejected',
  }
  return statusMap[status] || status
}

const loadMoreVideos = () => {
  if (hasMoreVideos.value && videosCursor.value) {
    loadVideos(videosCursor.value)
  }
}

const viewVideo = (video: any) => {
  // Navigate to feed or video detail page
  navigateTo('/')
}

const handleDeleteVideo = async (video: any) => {
  // Confirmation dialog
  if (!confirm(`Are you sure you want to delete "${video.title || 'this video'}"? This action cannot be undone.`)) {
    return
  }
  
  isDeleting.value = video.id
  
  try {
    await api.delete(`/videos/${video.id}`)
    
    // Optimistic UI update: Remove from list
    videos.value = videos.value.filter(v => v.id !== video.id)
    
    // Refresh profile stats
    await refreshProfile()
    
    // You could use a toast notification here for success message
  } catch (err: any) {
    console.error('Failed to delete video:', err)
    console.error('Error details:', {
      status: err.response?.status,
      statusText: err.response?.statusText,
      data: err.response?.data,
      message: err.message
    })
    const errorMessage = err.response?.data?.detail || err.message || 'Failed to delete video. Please try again.'
    alert(errorMessage)
  } finally {
    isDeleting.value = null
  }
}

const handleLogout = async () => {
  try {
    await authStore.logout()
    navigateTo('/login')
  } catch (err) {
    console.error('Logout failed:', err)
    // Still navigate to login even if logout API call fails
    navigateTo('/login')
  }
}

onMounted(() => {
  // Initialize auth from storage if needed
  if (process.client && !authStore.token) {
    authStore.initFromStorage()
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
