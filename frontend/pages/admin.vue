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
          <h1 class="text-2xl font-bold">Admin Dashboard</h1>
        </div>
        <div class="flex items-center gap-4">
          <span class="text-sm text-gray-400">{{ authStore.user?.username }}</span>
          <button
            @click="handleLogout"
            class="text-gray-400 hover:text-white transition-colors text-sm"
          >
            Logout
          </button>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="max-w-7xl mx-auto px-4 py-6">
      <!-- Access Denied -->
      <div
        v-if="!isAdmin"
        class="bg-red-900/50 border border-red-700 rounded-lg p-8 text-center"
      >
        <div class="text-6xl mb-4">🔒</div>
        <h2 class="text-2xl font-bold mb-2">Access Denied</h2>
        <p class="text-gray-400 mb-6">
          You need administrator privileges to access this page.
        </p>
        <NuxtLink
          to="/"
          class="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
        >
          Go to Feed
        </NuxtLink>
      </div>

      <!-- Admin Dashboard -->
      <div v-else>
        <!-- Tabs -->
        <div class="flex gap-2 mb-6 border-b border-gray-800">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'px-4 py-2 font-semibold transition-colors border-b-2',
              activeTab === tab.id
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-white',
            ]"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Loading State -->
        <div
          v-if="loading"
          class="flex items-center justify-center py-20"
        >
          <div class="text-gray-400 text-lg">Loading...</div>
        </div>

        <!-- Stats Tab -->
        <div v-else-if="activeTab === 'stats'" class="space-y-6">
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-2">Total Users</div>
              <div class="text-3xl font-bold">{{ stats?.users?.total || 0 }}</div>
            </div>
            
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-2">Total Videos</div>
              <div class="text-3xl font-bold">{{ stats?.videos?.total || 0 }}</div>
            </div>
            
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-2">Pending Reports</div>
              <div class="text-3xl font-bold text-yellow-400">
                {{ stats?.reports?.pending || 0 }}
              </div>
            </div>
            
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-2">Total Reports</div>
              <div class="text-3xl font-bold">{{ stats?.reports?.total || 0 }}</div>
            </div>
          </div>

          <!-- Videos by Status -->
          <div class="bg-gray-900 rounded-lg p-6">
            <h3 class="text-xl font-bold mb-4">Videos by Status</h3>
            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
              <div
                v-for="(count, status) in stats?.videos?.by_status"
                :key="status"
                class="text-center"
              >
                <div class="text-2xl font-bold mb-1">{{ count }}</div>
                <div class="text-sm text-gray-400 capitalize">{{ status }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Pending Videos Tab -->
        <div v-else-if="activeTab === 'videos'" class="space-y-6">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-bold">Pending Videos</h2>
            <button
              @click="() => loadPendingVideos()"
              class="text-blue-400 hover:text-blue-300 text-sm"
            >
              Refresh
            </button>
          </div>

          <!-- Loading Videos -->
          <div
            v-if="videosLoading && pendingVideos.length === 0"
            class="text-center py-8 text-gray-400"
          >
            Loading videos...
          </div>

          <!-- Empty State -->
          <div
            v-else-if="pendingVideos.length === 0"
            class="bg-gray-900 rounded-lg p-12 text-center"
          >
            <div class="text-6xl mb-4">✅</div>
            <h4 class="text-xl font-bold mb-2">All Clear!</h4>
            <p class="text-gray-400">No videos pending moderation.</p>
          </div>

          <!-- Videos List -->
          <div v-else class="space-y-4">
            <div
              v-for="video in pendingVideos"
              :key="video.id"
              class="bg-gray-900 rounded-lg p-6"
            >
              <div class="flex flex-col sm:flex-row gap-6">
                <!-- Thumbnail -->
                <div class="relative w-full sm:w-48 h-64 sm:h-32 bg-gray-800 rounded-lg overflow-hidden flex-shrink-0">
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
                      class="w-12 h-12"
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
                  <div
                    class="absolute top-2 left-2 bg-yellow-600 text-white text-xs px-2 py-1 rounded"
                  >
                    {{ video.status }}
                  </div>
                </div>

                <!-- Video Info -->
                <div class="flex-1">
                  <h3 class="text-lg font-bold mb-2">
                    {{ video.title || 'Untitled' }}
                  </h3>
                  <p
                    v-if="video.description"
                    class="text-sm text-gray-400 mb-4 line-clamp-2"
                  >
                    {{ video.description }}
                  </p>
                  <div class="flex flex-wrap gap-4 text-sm text-gray-500 mb-4">
                    <span>By: {{ video.user?.username }}</span>
                    <span>•</span>
                    <span>{{ formatDate(video.created_at) }}</span>
                    <span>•</span>
                    <span>Likes: {{ video.stats?.likes || 0 }}</span>
                    <span>•</span>
                    <span>Views: {{ video.stats?.views || 0 }}</span>
                  </div>
                  
                  <!-- Actions -->
                  <div class="flex gap-3">
                    <button
                      @click="approveVideo(video.id)"
                      :disabled="processingVideo === video.id"
                      class="bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-semibold transition-colors"
                    >
                      {{ processingVideo === video.id ? 'Processing...' : 'Approve' }}
                    </button>
                    <button
                      @click="showRejectDialog(video)"
                      :disabled="processingVideo === video.id"
                      class="bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-semibold transition-colors"
                    >
                      Reject
                    </button>
                    <a
                      v-if="video.url_hls"
                      :href="video.url_hls"
                      target="_blank"
                      class="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
                    >
                      Preview
                    </a>
                  </div>
                </div>
              </div>
            </div>

            <!-- Load More -->
            <div
              v-if="hasMoreVideos && !videosLoading"
              class="flex justify-center"
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

        <!-- Reports Tab -->
        <div v-else-if="activeTab === 'reports'" class="space-y-6">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-bold">Reports</h2>
            <div class="flex gap-2">
              <select
                v-model="reportStatusFilter"
                @change="() => loadReports()"
                class="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700"
              >
                <option value="">All Status</option>
                <option value="pending">Pending</option>
                <option value="resolved">Resolved</option>
                <option value="dismissed">Dismissed</option>
              </select>
              <button
                @click="() => loadReports()"
                class="text-blue-400 hover:text-blue-300 text-sm"
              >
                Refresh
              </button>
            </div>
          </div>

          <!-- Loading Reports -->
          <div
            v-if="reportsLoading && reports.length === 0"
            class="text-center py-8 text-gray-400"
          >
            Loading reports...
          </div>

          <!-- Empty State -->
          <div
            v-else-if="reports.length === 0"
            class="bg-gray-900 rounded-lg p-12 text-center"
          >
            <div class="text-6xl mb-4">📋</div>
            <h4 class="text-xl font-bold mb-2">No Reports</h4>
            <p class="text-gray-400">No reports found.</p>
          </div>

          <!-- Reports List -->
          <div v-else class="space-y-4">
            <div
              v-for="report in reports"
              :key="report.id"
              class="bg-gray-900 rounded-lg p-6"
            >
              <div class="flex items-start justify-between mb-4">
                <div class="flex-1">
                  <div class="flex items-center gap-3 mb-2">
                    <span
                      :class="[
                        'px-3 py-1 rounded-full text-xs font-semibold',
                        report.status === 'pending'
                          ? 'bg-yellow-600 text-white'
                          : report.status === 'resolved'
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-600 text-white',
                      ]"
                    >
                      {{ report.status.toUpperCase() }}
                    </span>
                    <span class="px-3 py-1 bg-blue-600 text-white rounded-full text-xs font-semibold">
                      {{ report.type.toUpperCase() }}
                    </span>
                  </div>
                  <p class="text-gray-400 mb-2">
                    Reported by <span class="text-white font-semibold">{{ report.reporter?.username }}</span>
                    on {{ formatDate(report.created_at) }}
                  </p>
                  <p
                    v-if="report.reason"
                    class="text-sm text-gray-300 mb-4"
                  >
                    <span class="font-semibold">Reason:</span> {{ report.reason }}
                  </p>
                  
                  <!-- Target Info -->
                  <div
                    v-if="report.target"
                    class="bg-gray-800 rounded-lg p-4 mb-4"
                  >
                    <div class="text-sm font-semibold mb-2">
                      {{ report.type === 'video' ? 'Video' : 'User' }}:
                    </div>
                    <div
                      v-if="report.type === 'video'"
                      class="text-sm text-gray-300"
                    >
                      <div class="font-semibold">{{ report.target.title || 'Untitled' }}</div>
                      <div class="text-gray-400">
                        By: {{ report.target.user?.username }}
                      </div>
                    </div>
                    <div
                      v-else
                      class="text-sm text-gray-300"
                    >
                      <div class="font-semibold">{{ report.target.username }}</div>
                    </div>
                  </div>

                  <!-- Resolver Info -->
                  <div
                    v-if="report.resolver"
                    class="text-sm text-gray-400"
                  >
                    {{ report.status === 'resolved' ? 'Resolved' : 'Dismissed' }} by
                    <span class="text-white font-semibold">{{ report.resolver.username }}</span>
                    <span v-if="report.resolved_at">
                      on {{ formatDate(report.resolved_at) }}
                    </span>
                  </div>
                </div>

                <!-- Actions -->
                <div
                  v-if="report.status === 'pending'"
                  class="flex flex-col gap-2 ml-4"
                >
                  <button
                    @click="resolveReport(report.id, 'resolve')"
                    :disabled="processingReport === report.id"
                    class="bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-semibold transition-colors text-sm whitespace-nowrap"
                  >
                    Resolve
                  </button>
                  <button
                    @click="resolveReport(report.id, 'dismiss')"
                    :disabled="processingReport === report.id"
                    class="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-semibold transition-colors text-sm whitespace-nowrap"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>

            <!-- Load More -->
            <div
              v-if="hasMoreReports && !reportsLoading"
              class="flex justify-center"
            >
              <button
                @click="loadMoreReports"
                class="bg-gray-800 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                Load More
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Reject Video Dialog -->
    <div
      v-if="rejectDialogOpen"
      class="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      @click.self="rejectDialogOpen = false"
    >
      <div class="bg-gray-900 rounded-lg p-6 max-w-md w-full">
        <h3 class="text-xl font-bold mb-4">Reject Video</h3>
        <p class="text-gray-400 mb-4">
          Are you sure you want to reject this video?
        </p>
        <div class="mb-4">
          <label class="block text-sm font-semibold mb-2">
            Reason (optional)
          </label>
          <textarea
            v-model="rejectReason"
            class="w-full bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500"
            rows="3"
            placeholder="Enter rejection reason..."
          />
        </div>
        <div class="flex gap-3">
          <button
            @click="rejectDialogOpen = false"
            class="flex-1 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
          >
            Cancel
          </button>
          <button
            @click="confirmReject"
            :disabled="processingVideo === selectedVideoId"
            class="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-semibold transition-colors"
          >
            {{ processingVideo === selectedVideoId ? 'Processing...' : 'Reject' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { useApi } from '~/composables/useApi'

definePageMeta({
  middleware: 'admin',
})

const authStore = useAuthStore()
const api = useApi()

const isAdmin = computed(() => authStore.user?.is_admin === true)

const tabs = [
  { id: 'stats', label: 'Overview' },
  { id: 'videos', label: 'Pending Videos' },
  { id: 'reports', label: 'Reports' },
]
const activeTab = ref('stats')
const loading = ref(false)

// Stats
const stats = ref<any | null>(null)

// Videos
const pendingVideos = ref<any[]>([])
const videosLoading = ref(false)
const nextVideoCursor = ref<string | null>(null)
const hasMoreVideos = ref(true)
const processingVideo = ref<string | null>(null)

// Reports
const reports = ref<any[]>([])
const reportsLoading = ref(false)
const reportStatusFilter = ref('')
const nextReportCursor = ref<string | null>(null)
const hasMoreReports = ref(true)
const processingReport = ref<string | null>(null)

// Reject Dialog
const rejectDialogOpen = ref(false)
const selectedVideoId = ref<string | null>(null)
const rejectReason = ref('')

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const loadStats = async () => {
  loading.value = true
  try {
    stats.value = await api.get('/admin/stats')
  } catch (err) {
    console.error('Failed to load stats:', err)
  } finally {
    loading.value = false
  }
}

const loadPendingVideos = async (cursor?: string) => {
  if (videosLoading.value || (!hasMoreVideos.value && cursor)) return
  
  videosLoading.value = true
  try {
    const response = await api.get<{
      videos: any[]
      next_cursor: string | null
      has_more: boolean
    }>(`/admin/videos/pending${cursor ? `?cursor=${cursor}` : ''}`)
    
    if (cursor) {
      pendingVideos.value.push(...response.videos)
    } else {
      pendingVideos.value = response.videos
    }
    
    nextVideoCursor.value = response.next_cursor
    hasMoreVideos.value = response.has_more
  } catch (err) {
    console.error('Failed to load pending videos:', err)
  } finally {
    videosLoading.value = false
  }
}

const loadMoreVideos = () => {
  if (hasMoreVideos.value && nextVideoCursor.value) {
    loadPendingVideos(nextVideoCursor.value)
  }
}

const approveVideo = async (videoId: string) => {
  processingVideo.value = videoId
  try {
    await api.post(`/admin/videos/${videoId}/approve`)
    // Remove from list
    pendingVideos.value = pendingVideos.value.filter(v => v.id !== videoId)
    // Reload stats
    loadStats()
  } catch (err) {
    console.error('Failed to approve video:', err)
    alert('Failed to approve video. Please try again.')
  } finally {
    processingVideo.value = null
  }
}

const showRejectDialog = (video: any) => {
  selectedVideoId.value = video.id
  rejectReason.value = ''
  rejectDialogOpen.value = true
}

const confirmReject = async () => {
  if (!selectedVideoId.value) return
  
  processingVideo.value = selectedVideoId.value
  try {
    await api.post(`/admin/videos/${selectedVideoId.value}/reject`, {
      reason: rejectReason.value || undefined,
    })
    // Remove from list
    pendingVideos.value = pendingVideos.value.filter(v => v.id !== selectedVideoId.value)
    // Close dialog
    rejectDialogOpen.value = false
    selectedVideoId.value = null
    rejectReason.value = ''
    // Reload stats
    loadStats()
  } catch (err) {
    console.error('Failed to reject video:', err)
    alert('Failed to reject video. Please try again.')
  } finally {
    processingVideo.value = null
  }
}

const loadReports = async (cursor?: string) => {
  if (reportsLoading.value || (!hasMoreReports.value && cursor)) return
  
  reportsLoading.value = true
  try {
    const params = new URLSearchParams()
    if (reportStatusFilter.value) {
      params.append('status', reportStatusFilter.value)
    }
    if (cursor) {
      params.append('cursor', cursor)
    }
    
    const response = await api.get<{
      reports: any[]
      next_cursor: string | null
      has_more: boolean
    }>(`/admin/reports${params.toString() ? `?${params.toString()}` : ''}`)
    
    if (cursor) {
      reports.value.push(...response.reports)
    } else {
      reports.value = response.reports
    }
    
    nextReportCursor.value = response.next_cursor
    hasMoreReports.value = response.has_more
  } catch (err) {
    console.error('Failed to load reports:', err)
  } finally {
    reportsLoading.value = false
  }
}

const loadMoreReports = () => {
  if (hasMoreReports.value && nextReportCursor.value) {
    loadReports(nextReportCursor.value)
  }
}

const resolveReport = async (reportId: string, action: 'resolve' | 'dismiss') => {
  processingReport.value = reportId
  try {
    await api.post(`/admin/reports/${reportId}/resolve`, { action })
    // Update report in list
    const report = reports.value.find(r => r.id === reportId)
    if (report) {
      report.status = action === 'resolve' ? 'resolved' : 'dismissed'
    }
    // Reload stats
    loadStats()
  } catch (err) {
    console.error('Failed to resolve report:', err)
    alert('Failed to resolve report. Please try again.')
  } finally {
    processingReport.value = null
  }
}

const handleLogout = async () => {
  try {
    await authStore.logout()
    navigateTo('/login')
  } catch (err) {
    console.error('Logout failed:', err)
  }
}

// Watch for tab changes
watch(activeTab, (newTab) => {
  if (newTab === 'stats') {
    loadStats()
  } else if (newTab === 'videos') {
    loadPendingVideos()
  } else if (newTab === 'reports') {
    loadReports()
  }
})

onMounted(() => {
  if (isAdmin.value) {
    loadStats()
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
