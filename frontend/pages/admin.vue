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
          <h1 class="text-2xl font-bold">{{ t('admin.title') }}</h1>
        </div>
        <div class="flex items-center gap-4">
          <span class="text-sm text-gray-400">{{ authStore.user?.username }}</span>
          <button
            @click="handleLogout"
            class="text-gray-400 hover:text-white transition-colors text-sm"
          >
            {{ t('admin.logout') }}
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
        <h2 class="text-2xl font-bold mb-2">{{ t('admin.accessDenied') }}</h2>
        <p class="text-gray-400 mb-6">
          {{ t('admin.accessDeniedDescription') }}
        </p>
        <NuxtLink
          to="/"
          class="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
        >
          {{ t('admin.goToFeed') }}
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
          <div class="text-gray-400 text-lg">{{ t('admin.loading') }}</div>
        </div>

        <!-- Stats Tab -->
        <div v-else-if="activeTab === 'stats'" class="space-y-6">
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-2">{{ t('admin.stats.totalUsers') }}</div>
              <div class="text-3xl font-bold">{{ stats?.users?.total || 0 }}</div>
            </div>
            
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-2">{{ t('admin.stats.totalVideos') }}</div>
              <div class="text-3xl font-bold">{{ stats?.videos?.total || 0 }}</div>
            </div>
            
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-2">{{ t('admin.stats.pendingReports') }}</div>
              <div class="text-3xl font-bold text-yellow-400">
                {{ stats?.reports?.pending || 0 }}
              </div>
            </div>
            
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-2">{{ t('admin.stats.totalReports') }}</div>
              <div class="text-3xl font-bold">{{ stats?.reports?.total || 0 }}</div>
            </div>
          </div>

          <!-- Videos by Status -->
          <div class="bg-gray-900 rounded-lg p-6">
            <h3 class="text-xl font-bold mb-4">{{ t('admin.stats.videosByStatus') }}</h3>
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
            <h2 class="text-xl font-bold">{{ t('admin.pendingVideos.title') }}</h2>
            <button
              @click="() => loadPendingVideos()"
              class="text-blue-400 hover:text-blue-300 text-sm"
            >
              {{ t('admin.pendingVideos.refresh') }}
            </button>
          </div>

          <!-- Loading Videos -->
          <div
            v-if="videosLoading && pendingVideos.length === 0"
            class="text-center py-8 text-gray-400"
          >
            {{ t('admin.pendingVideos.loadingVideos') }}
          </div>

          <!-- Empty State -->
          <div
            v-else-if="pendingVideos.length === 0"
            class="bg-gray-900 rounded-lg p-12 text-center"
          >
            <div class="text-6xl mb-4">✅</div>
            <h4 class="text-xl font-bold mb-2">{{ t('admin.pendingVideos.allClear') }}</h4>
            <p class="text-gray-400">{{ t('admin.pendingVideos.noPendingVideos') }}</p>
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
                    :src="getAbsoluteUrl(video.thumbnail)"
                    :alt="video.title || 'Video thumbnail'"
                    class="w-full h-full object-cover"
                  />
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
                    <span>{{ t('admin.pendingVideos.by') }}: {{ video.user?.username }}</span>
                    <span>•</span>
                    <span>{{ formatDate(video.created_at) }}</span>
                    <span>•</span>
                    <span>{{ t('admin.pendingVideos.likes') }}: {{ video.stats?.likes || 0 }}</span>
                    <span>•</span>
                    <span>{{ t('admin.pendingVideos.views') }}: {{ video.stats?.views || 0 }}</span>
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
                      :href="getAbsoluteUrl(video.url_mp4)"
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
                {{ t('admin.pendingVideos.loadMore') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Reports Tab -->
        <div v-else-if="activeTab === 'reports'" class="space-y-6">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-bold">{{ t('admin.reports.title') }}</h2>
            <div class="flex gap-2">
              <select
                v-model="reportStatusFilter"
                @change="() => loadReports()"
                class="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700"
              >
                <option value="">{{ t('admin.reports.allStatus') }}</option>
                <option value="pending">{{ t('admin.reports.pending') }}</option>
                <option value="resolved">{{ t('admin.reports.resolved') }}</option>
                <option value="dismissed">{{ t('admin.reports.dismissed') }}</option>
              </select>
              <button
                @click="() => loadReports()"
                class="text-blue-400 hover:text-blue-300 text-sm"
              >
                {{ t('admin.reports.refresh') }}
              </button>
            </div>
          </div>

          <!-- Loading Reports -->
          <div
            v-if="reportsLoading && reports.length === 0"
            class="text-center py-8 text-gray-400"
          >
            {{ t('admin.reports.loadingReports') }}
          </div>

          <!-- Empty State -->
          <div
            v-else-if="reports.length === 0"
            class="bg-gray-900 rounded-lg p-12 text-center"
          >
            <div class="text-6xl mb-4">📋</div>
            <h4 class="text-xl font-bold mb-2">{{ t('admin.reports.noReports') }}</h4>
            <p class="text-gray-400">{{ t('admin.reports.noReportsDescription') }}</p>
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
                    {{ t('admin.reports.reportedBy') }} <span class="text-white font-semibold">{{ report.reporter?.username }}</span>
                    {{ t('admin.reports.on') }} {{ formatDate(report.created_at) }}
                  </p>
                  <p
                    v-if="report.reason"
                    class="text-sm text-gray-300 mb-4"
                  >
                    <span class="font-semibold">{{ t('admin.reports.reason') }}:</span> {{ report.reason }}
                  </p>
                  
                  <!-- Target Info -->
                  <div
                    v-if="report.target"
                    class="bg-gray-800 rounded-lg p-4 mb-4"
                  >
                    <div class="text-sm font-semibold mb-2">
                      {{ report.type === 'video' ? t('admin.reports.video') : t('admin.reports.user') }}:
                    </div>
                    <div
                      v-if="report.type === 'video'"
                      class="text-sm text-gray-300"
                    >
                      <div class="font-semibold">{{ report.target.title || t('profile.untitled') }}</div>
                      <div class="text-gray-400">
                        {{ t('admin.pendingVideos.by') }}: {{ report.target.user?.username }}
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
                    {{ report.status === 'resolved' ? t('admin.reports.resolvedBy') : t('admin.reports.dismissedBy') }}
                    <span class="text-white font-semibold">{{ report.resolver.username }}</span>
                    <span v-if="report.resolved_at">
                      {{ t('admin.reports.on') }} {{ formatDate(report.resolved_at) }}
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
                    {{ t('admin.reports.resolve') }}
                  </button>
                  <button
                    @click="resolveReport(report.id, 'dismiss')"
                    :disabled="processingReport === report.id"
                    class="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-semibold transition-colors text-sm whitespace-nowrap"
                  >
                    {{ t('admin.reports.dismiss') }}
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
                {{ t('admin.reports.loadMore') }}
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
        <h3 class="text-xl font-bold mb-4">{{ t('admin.rejectDialog.title') }}</h3>
        <p class="text-gray-400 mb-4">
          {{ t('admin.rejectDialog.description') }}
        </p>
        <div class="mb-4">
          <label class="block text-sm font-semibold mb-2">
            {{ t('admin.rejectDialog.reason') }}
          </label>
          <textarea
            v-model="rejectReason"
            class="w-full bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500"
            rows="3"
            :placeholder="t('admin.rejectDialog.reasonPlaceholder')"
          />
        </div>
        <div class="flex gap-3">
          <button
            @click="rejectDialogOpen = false"
            class="flex-1 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
          >
            {{ t('admin.rejectDialog.cancel') }}
          </button>
          <button
            @click="confirmReject"
            :disabled="processingVideo === selectedVideoId"
            class="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-semibold transition-colors"
          >
            {{ processingVideo === selectedVideoId ? t('admin.rejectDialog.processing') : t('admin.rejectDialog.reject') }}
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
import { useI18n } from '~/composables/useI18n'

definePageMeta({
  middleware: 'admin',
})

const authStore = useAuthStore()
const api = useApi()
const { t } = useI18n()

// Helper to convert relative URLs to absolute URLs
const config = useRuntimeConfig()
const backendBaseUrl = config.public.backendBaseUrl

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

const isAdmin = computed(() => authStore.user?.is_admin === true)

const tabs = [
  { id: 'stats', label: t('admin.tabs.overview') },
  { id: 'videos', label: t('admin.tabs.pendingVideos') },
  { id: 'reports', label: t('admin.tabs.reports') },
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
    alert(t('errors.generic'))
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
    alert(t('errors.generic'))
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
    alert(t('errors.generic'))
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
