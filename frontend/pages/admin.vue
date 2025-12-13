<template>
  <div class="min-h-screen bg-black text-white">
    <!-- Header -->
    <div class="sticky top-0 z-10 bg-black/95 backdrop-blur-sm border-b border-gray-800 px-4 py-4" style="padding-top: max(calc(1rem + env(safe-area-inset-top)), 1rem);">
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
        <div class="flex gap-2 mb-6 border-b border-gray-800 overflow-x-auto">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'px-4 py-2 font-semibold transition-colors border-b-2 whitespace-nowrap flex-shrink-0',
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

        <!-- Error State -->
        <div
          v-if="error"
          class="bg-red-900/50 border border-red-700 rounded-lg p-4 mb-6"
        >
          <p class="text-red-300">{{ error }}</p>
          <button
            @click="loadStats()"
            class="mt-2 text-blue-400 hover:text-blue-300 text-sm"
          >
            Retry
          </button>
        </div>

        <!-- Stats Tab -->
        <div v-if="activeTab === 'stats' && !loading" class="space-y-6">
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
            <div v-if="stats?.videos?.by_status" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
              <div
                v-for="(count, status) in stats.videos.by_status"
                :key="status"
                class="text-center"
              >
                <div class="text-2xl font-bold mb-1">{{ count }}</div>
                <div class="text-sm text-gray-400 capitalize">{{ status }}</div>
              </div>
            </div>
            <div v-else class="text-gray-400 text-center py-4">
              No status data available
            </div>
          </div>

          <!-- Debug Info (remove in production) -->
          <details class="bg-gray-900 rounded-lg p-4 mt-6">
            <summary class="cursor-pointer text-sm text-gray-400">Debug: Raw Stats Data</summary>
            <pre class="mt-2 text-xs text-gray-500 overflow-auto">{{ JSON.stringify(stats, null, 2) }}</pre>
          </details>
        </div>

        <!-- Share Analytics Tab -->
        <div v-else-if="activeTab === 'shareAnalytics'" class="space-y-6">
          <div class="flex items-center justify-between flex-wrap gap-4">
            <h2 class="text-xl font-bold">Share Analytics</h2>
            <div class="flex items-center gap-4">
              <select
                v-model="shareAnalyticsPeriod"
                class="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="day">Daily</option>
                <option value="week">Weekly</option>
              </select>
              <select
                v-model="shareAnalyticsDays"
                class="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option :value="7">Last 7 days</option>
                <option :value="14">Last 14 days</option>
                <option :value="30">Last 30 days</option>
                <option :value="60">Last 60 days</option>
                <option :value="90">Last 90 days</option>
              </select>
              <button
                @click="loadShareAnalytics"
                :disabled="shareAnalyticsLoading"
                class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                {{ shareAnalyticsLoading ? 'Loading...' : 'Refresh' }}
              </button>
            </div>
          </div>

          <!-- Loading -->
          <div v-if="shareAnalyticsLoading && !shareAnalyticsData" class="text-center py-8 text-gray-400">
            Loading share analytics...
          </div>

          <!-- Summary Cards -->
          <div v-if="shareAnalyticsData" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Total Shares</div>
              <div class="text-2xl font-bold">{{ shareAnalyticsData.summary?.total_shares?.toLocaleString() || 0 }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Total Clicks</div>
              <div class="text-2xl font-bold">{{ shareAnalyticsData.summary?.total_clicks?.toLocaleString() || 0 }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Unique Clickers</div>
              <div class="text-2xl font-bold">{{ shareAnalyticsData.summary?.unique_clickers?.toLocaleString() || 0 }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Shares with Clicks</div>
              <div class="text-2xl font-bold">{{ shareAnalyticsData.summary?.shares_with_clicks?.toLocaleString() || 0 }}</div>
            </div>
          </div>

          <!-- Metrics Cards -->
          <div v-if="shareAnalyticsData" class="grid grid-cols-2 lg:grid-cols-5 gap-4 mt-4">
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Click-Through Rate</div>
              <div class="text-2xl font-bold text-blue-400">{{ shareAnalyticsData.metrics?.click_through_rate || 0 }}%</div>
              <div class="text-xs text-gray-500 mt-1">Clicks per 100 shares</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Avg Clicks/Share</div>
              <div class="text-2xl font-bold">{{ shareAnalyticsData.metrics?.avg_clicks_per_share || 0 }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Conversion Rate</div>
              <div class="text-2xl font-bold text-green-400">{{ shareAnalyticsData.metrics?.share_conversion_rate || 0 }}%</div>
              <div class="text-xs text-gray-500 mt-1">Shares that got clicks</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Avg Clicks/Clicker</div>
              <div class="text-2xl font-bold">{{ shareAnalyticsData.metrics?.avg_clicks_per_clicker || 0 }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Time to First Click</div>
              <div class="text-2xl font-bold">{{ shareAnalyticsData.metrics?.avg_time_to_first_click_hours || 0 }}h</div>
            </div>
          </div>

          <!-- Time Series Charts -->
          <div v-if="shareAnalyticsData && shareAnalyticsData.over_time" class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <!-- Shares Over Time -->
            <div class="bg-gray-900 rounded-lg p-6">
              <h3 class="text-lg font-bold mb-4">Shares Over Time</h3>
              <div class="space-y-2 max-h-64 overflow-y-auto">
                <div
                  v-for="item in shareAnalyticsData.over_time.shares"
                  :key="item.date"
                  class="flex items-center justify-between p-2 hover:bg-gray-800 rounded"
                >
                  <span class="text-sm text-gray-300">{{ formatAnalyticsDate(item.date, shareAnalyticsPeriod) }}</span>
                  <span class="text-sm font-bold text-blue-400">{{ item.shares || 0 }}</span>
                </div>
              </div>
            </div>

            <!-- Clicks Over Time -->
            <div class="bg-gray-900 rounded-lg p-6">
              <h3 class="text-lg font-bold mb-4">Clicks Over Time</h3>
              <div class="space-y-2 max-h-64 overflow-y-auto">
                <div
                  v-for="item in shareAnalyticsData.over_time.clicks"
                  :key="item.date"
                  class="flex items-center justify-between p-2 hover:bg-gray-800 rounded"
                >
                  <span class="text-sm text-gray-300">{{ formatAnalyticsDate(item.date, shareAnalyticsPeriod) }}</span>
                  <span class="text-sm font-bold text-green-400">{{ item.clicks || 0 }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Top Videos -->
          <div v-if="shareAnalyticsData && shareAnalyticsData.top_videos" class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <!-- Most Shared Videos -->
            <div class="bg-gray-900 rounded-lg p-6">
              <h3 class="text-lg font-bold mb-4">Most Shared Videos</h3>
              <div v-if="shareAnalyticsData.top_videos.most_shared && shareAnalyticsData.top_videos.most_shared.length > 0" class="space-y-3">
                <div
                  v-for="(video, index) in shareAnalyticsData.top_videos.most_shared"
                  :key="video.video_id"
                  class="p-3 bg-gray-800 rounded hover:bg-gray-700 transition-colors"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="text-gray-500 text-xs font-bold">#{{ index + 1 }}</span>
                        <span class="text-white text-sm font-medium truncate">{{ video.title || 'Untitled' }}</span>
                      </div>
                    </div>
                    <div class="text-right flex-shrink-0">
                      <div class="text-sm font-bold text-blue-400">{{ video.share_count || 0 }}</div>
                      <div class="text-xs text-gray-500">shares</div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="text-gray-400 text-center py-4 text-sm">No shared videos in this period</div>
            </div>

            <!-- Most Clicked Videos -->
            <div class="bg-gray-900 rounded-lg p-6">
              <h3 class="text-lg font-bold mb-4">Most Clicked Videos</h3>
              <div v-if="shareAnalyticsData.top_videos.most_clicked && shareAnalyticsData.top_videos.most_clicked.length > 0" class="space-y-3">
                <div
                  v-for="(video, index) in shareAnalyticsData.top_videos.most_clicked"
                  :key="video.video_id"
                  class="p-3 bg-gray-800 rounded hover:bg-gray-700 transition-colors"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="text-gray-500 text-xs font-bold">#{{ index + 1 }}</span>
                        <span class="text-white text-sm font-medium truncate">{{ video.title || 'Untitled' }}</span>
                      </div>
                    </div>
                    <div class="text-right flex-shrink-0">
                      <div class="text-sm font-bold text-green-400">{{ video.click_count || 0 }}</div>
                      <div class="text-xs text-gray-500">clicks</div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="text-gray-400 text-center py-4 text-sm">No clicked videos in this period</div>
            </div>
          </div>

          <!-- Top Sharers -->
          <div v-if="shareAnalyticsData && shareAnalyticsData.top_sharers" class="bg-gray-900 rounded-lg p-6 mt-6">
            <h3 class="text-lg font-bold mb-4">Top Sharers</h3>
            <div v-if="shareAnalyticsData.top_sharers && shareAnalyticsData.top_sharers.length > 0" class="space-y-2">
              <div
                v-for="(sharer, index) in shareAnalyticsData.top_sharers"
                :key="sharer.sharer_session_id"
                class="flex items-center justify-between p-2 hover:bg-gray-800 rounded"
              >
                <div class="flex items-center gap-3">
                  <span class="text-gray-500 text-sm w-6">#{{ index + 1 }}</span>
                  <span class="text-white text-sm font-mono">{{ sharer.sharer_session_id.substring(0, 8) }}...</span>
                </div>
                <span class="text-gray-400 text-sm">{{ sharer.share_count }} shares</span>
              </div>
            </div>
            <div v-else class="text-gray-400 text-center py-4 text-sm">No sharers in this period</div>
          </div>

          <!-- Empty State -->
          <div v-else-if="!shareAnalyticsLoading && shareAnalyticsData && (!shareAnalyticsData.summary || shareAnalyticsData.summary.total_shares === 0)" class="bg-gray-900 rounded-lg p-12 text-center">
            <div class="text-6xl mb-4">📤</div>
            <h4 class="text-xl font-bold mb-2">No Share Data</h4>
            <p class="text-gray-400">No share analytics data available for the selected period.</p>
          </div>
        </div>

        <!-- Ad Analytics Tab -->
        <div v-else-if="activeTab === 'adAnalytics'" class="space-y-6">
          <div class="flex items-center justify-between flex-wrap gap-4">
            <h2 class="text-xl font-bold">Ad Analytics</h2>
            <div class="flex items-center gap-4">
              <select
                v-model="adAnalyticsPeriod"
                class="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="day">Daily</option>
                <option value="week">Weekly</option>
              </select>
              <select
                v-model="adAnalyticsDays"
                class="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option :value="7">Last 7 days</option>
                <option :value="14">Last 14 days</option>
                <option :value="30">Last 30 days</option>
                <option :value="60">Last 60 days</option>
                <option :value="90">Last 90 days</option>
              </select>
              <button
                @click="loadAdAnalytics"
                :disabled="adAnalyticsLoading"
                class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                {{ adAnalyticsLoading ? 'Loading...' : 'Refresh' }}
              </button>
            </div>
          </div>

          <!-- Loading -->
          <div v-if="adAnalyticsLoading && !adAnalyticsData" class="text-center py-8 text-gray-400">
            Loading ad analytics...
          </div>

          <!-- Summary Cards -->
          <div v-if="adAnalyticsData" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Total Clicks</div>
              <div class="text-2xl font-bold">{{ adAnalyticsData.totals?.clicks?.toLocaleString() || 0 }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Total Views</div>
              <div class="text-2xl font-bold">{{ adAnalyticsData.totals?.views?.toLocaleString() || 0 }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Unique Clickers</div>
              <div class="text-2xl font-bold">{{ adAnalyticsData.totals?.unique_clickers?.toLocaleString() || 0 }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Auth Clickers</div>
              <div class="text-2xl font-bold">{{ adAnalyticsData.totals?.unique_auth_clickers?.toLocaleString() || 0 }}</div>
            </div>
          </div>

          <!-- Metrics Cards -->
          <div v-if="adAnalyticsData" class="grid grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Click-Through Rate</div>
              <div class="text-2xl font-bold text-blue-400">{{ adAnalyticsData.metrics?.click_through_rate || 0 }}%</div>
              <div class="text-xs text-gray-500 mt-1">Clicks per 100 views</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Avg Clicks/View</div>
              <div class="text-2xl font-bold">{{ adAnalyticsData.metrics?.avg_clicks_per_view || 0 }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Avg Clicks/Clicker</div>
              <div class="text-2xl font-bold">{{ adAnalyticsData.metrics?.avg_clicks_per_clicker || 0 }}</div>
            </div>
          </div>

          <!-- Time Series Charts -->
          <div v-if="adAnalyticsData && (adAnalyticsData.clicks_over_time || adAnalyticsData.views_over_time)" class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <!-- Clicks Over Time -->
            <div class="bg-gray-900 rounded-lg p-6">
              <h3 class="text-lg font-bold mb-4">Clicks Over Time</h3>
              <div class="space-y-2 max-h-64 overflow-y-auto">
                <div
                  v-for="item in adAnalyticsData.clicks_over_time"
                  :key="item.date"
                  class="flex items-center justify-between p-2 hover:bg-gray-800 rounded"
                >
                  <span class="text-sm text-gray-300">{{ formatAnalyticsDate(item.date, adAnalyticsPeriod) }}</span>
                  <span class="text-sm font-bold text-green-400">{{ item.clicks || 0 }}</span>
                </div>
              </div>
            </div>

            <!-- Views Over Time -->
            <div class="bg-gray-900 rounded-lg p-6">
              <h3 class="text-lg font-bold mb-4">Views Over Time</h3>
              <div class="space-y-2 max-h-64 overflow-y-auto">
                <div
                  v-for="item in adAnalyticsData.views_over_time"
                  :key="item.date"
                  class="flex items-center justify-between p-2 hover:bg-gray-800 rounded"
                >
                  <span class="text-sm text-gray-300">{{ formatAnalyticsDate(item.date, adAnalyticsPeriod) }}</span>
                  <span class="text-sm font-bold text-blue-400">{{ item.views || 0 }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Top Performing Ad Videos -->
          <div v-if="adAnalyticsData && adAnalyticsData.top_videos" class="bg-gray-900 rounded-lg p-6 mt-6">
            <h3 class="text-lg font-bold mb-4">Top Performing Ad Videos</h3>
            <div v-if="adAnalyticsData.top_videos && adAnalyticsData.top_videos.length > 0" class="space-y-3">
              <div
                v-for="(video, index) in adAnalyticsData.top_videos"
                :key="video.id"
                class="p-3 bg-gray-800 rounded hover:bg-gray-700 transition-colors"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="text-gray-500 text-sm">#{{ index + 1 }}</span>
                      <h4 class="font-semibold truncate">{{ video.title || 'Untitled' }}</h4>
                    </div>
                    <p class="text-sm text-gray-400">by @{{ video.user?.username || 'Unknown' }}</p>
                  </div>
                  <div class="flex items-center gap-4 text-sm">
                    <div class="text-center">
                      <div class="text-gray-400 text-xs">Clicks</div>
                      <div class="font-bold text-green-400">{{ video.clicks || 0 }}</div>
                    </div>
                    <div class="text-center">
                      <div class="text-gray-400 text-xs">Views</div>
                      <div class="font-bold text-blue-400">{{ video.views || 0 }}</div>
                    </div>
                    <div class="text-center">
                      <div class="text-gray-400 text-xs">CTR</div>
                      <div class="font-bold text-yellow-400">{{ video.ctr?.toFixed(2) || 0 }}%</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-gray-400">
              No ad video data available
            </div>
          </div>

          <div v-else-if="!adAnalyticsLoading && adAnalyticsData && (!adAnalyticsData.totals || adAnalyticsData.totals.clicks === 0)" class="bg-gray-900 rounded-lg p-12 text-center">
            <div class="text-6xl mb-4">📢</div>
            <h4 class="text-xl font-bold mb-2">No Ad Data</h4>
            <p class="text-gray-400">No ad analytics data available for the selected period.</p>
          </div>
        </div>

        <!-- Visitor Analytics Tab -->
        <div v-else-if="activeTab === 'visitorAnalytics'" class="space-y-6">
          <div class="flex items-center justify-between flex-wrap gap-4">
            <h2 class="text-xl font-bold">Visitor Analytics</h2>
            <div class="flex items-center gap-4">
              <select
                v-model="visitorAnalyticsDays"
                class="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700"
              >
                <option :value="7">Last 7 days</option>
                <option :value="14">Last 14 days</option>
                <option :value="30">Last 30 days</option>
                <option :value="60">Last 60 days</option>
                <option :value="90">Last 90 days</option>
              </select>
              <button
                @click="loadVisitorAnalytics"
                :disabled="visitorAnalyticsLoading"
                class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                {{ visitorAnalyticsLoading ? 'Loading...' : 'Refresh' }}
              </button>
            </div>
          </div>

          <!-- Loading -->
          <div v-if="visitorAnalyticsLoading && !visitorAnalyticsData" class="text-center py-8 text-gray-400">
            Loading visitor analytics...
          </div>

          <!-- Summary Cards -->
          <div v-if="visitorAnalyticsData" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Total Visits</div>
              <div class="text-2xl font-bold">{{ visitorAnalyticsData.total_visits?.toLocaleString() || 0 }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Unique Visitors</div>
              <div class="text-2xl font-bold">{{ visitorAnalyticsData.unique_visitors?.toLocaleString() || 0 }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Countries</div>
              <div class="text-2xl font-bold">{{ visitorAnalyticsData.unique_countries || 0 }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Locations Tracked</div>
              <div class="text-2xl font-bold">{{ visitorLocations?.length || 0 }}</div>
            </div>
          </div>

          <!-- Map Visualization -->
          <div v-if="visitorLocations && visitorLocations.length > 0" class="bg-gray-900 rounded-lg p-6">
            <h3 class="text-lg font-bold mb-4">Visitor Locations Map</h3>
            <VisitorMap :locations="visitorLocations" />
          </div>

          <!-- Top Countries -->
          <div v-if="visitorAnalyticsData?.top_countries" class="bg-gray-900 rounded-lg p-6">
            <h3 class="text-lg font-bold mb-4">Top Countries</h3>
            <div class="space-y-2">
              <div
                v-for="(country, index) in visitorAnalyticsData.top_countries"
                :key="country.country"
                class="flex items-center justify-between p-2 hover:bg-gray-800 rounded"
              >
                <div class="flex items-center gap-3">
                  <span class="text-gray-500 text-sm w-6">#{{ index + 1 }}</span>
                  <span class="text-white">{{ country.country_name || country.country }}</span>
                </div>
                <div class="text-right">
                  <div class="text-sm font-bold">{{ country.visits.toLocaleString() }} visits</div>
                  <div class="text-xs text-gray-500">{{ country.visitors }} visitors</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Top Cities -->
          <div v-if="visitorAnalyticsData?.top_cities" class="bg-gray-900 rounded-lg p-6">
            <h3 class="text-lg font-bold mb-4">Top Cities</h3>
            <div class="space-y-2">
              <div
                v-for="(city, index) in visitorAnalyticsData.top_cities"
                :key="`${city.city}-${city.country}`"
                class="flex items-center justify-between p-2 hover:bg-gray-800 rounded"
              >
                <div class="flex items-center gap-3">
                  <span class="text-gray-500 text-sm w-6">#{{ index + 1 }}</span>
                  <span class="text-white">{{ city.city }}, {{ city.country_name || city.country }}</span>
                </div>
                <div class="text-right">
                  <div class="text-sm font-bold">{{ city.visits.toLocaleString() }} visits</div>
                  <div class="text-xs text-gray-500">{{ city.visitors }} visitors</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Top URLs -->
          <div v-if="visitorAnalyticsData?.top_urls" class="bg-gray-900 rounded-lg p-6">
            <h3 class="text-lg font-bold mb-4">Most Visited URLs</h3>
            <div class="space-y-2">
              <div
                v-for="(url, index) in visitorAnalyticsData.top_urls"
                :key="url.url"
                class="flex items-center justify-between p-2 hover:bg-gray-800 rounded"
              >
                <div class="flex items-center gap-3 flex-1 min-w-0">
                  <span class="text-gray-500 text-sm w-6">#{{ index + 1 }}</span>
                  <span class="text-white text-sm truncate">{{ url.url }}</span>
                </div>
                <div class="text-right flex-shrink-0 ml-4">
                  <div class="text-sm font-bold">{{ url.visits.toLocaleString() }} visits</div>
                  <div class="text-xs text-gray-500">{{ url.visitors }} visitors</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Recent Visits Table -->
          <div v-if="recentVisits && recentVisits.length > 0" class="bg-gray-900 rounded-lg overflow-hidden">
            <h3 class="text-lg font-bold mb-4 p-6 pb-0">Recent Visits</h3>
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead class="bg-gray-800">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Time</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">URL</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Location</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">User</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-800">
                  <tr v-for="visit in recentVisits" :key="visit.id" class="hover:bg-gray-800">
                    <td class="px-4 py-3 text-sm text-gray-300">
                      {{ formatDate(visit.visited_at) }}
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-300 truncate max-w-xs">
                      {{ visit.url }}
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-300">
                      <div v-if="visit.city || visit.country_name">
                        {{ visit.city }}{{ visit.city && visit.country_name ? ', ' : '' }}{{ visit.country_name }}
                      </div>
                      <div v-else class="text-gray-500">Unknown</div>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-300">
                      {{ visit.user_id ? 'Authenticated' : 'Anonymous' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Analytics Tab -->
        <div v-else-if="activeTab === 'analytics'" class="space-y-6">
          <div class="flex items-center justify-between flex-wrap gap-4">
            <h2 class="text-xl font-bold">Analytics</h2>
            <div class="flex items-center gap-4">
              <select
                v-model="analyticsPeriod"
                class="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="day">Daily</option>
                <option value="week">Weekly</option>
              </select>
              <select
                v-model="analyticsDays"
                class="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option :value="7">Last 7 days</option>
                <option :value="14">Last 14 days</option>
                <option :value="30">Last 30 days</option>
                <option :value="60">Last 60 days</option>
                <option :value="90">Last 90 days</option>
              </select>
              <button
                @click="loadAnalytics"
                :disabled="analyticsLoading"
                class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                {{ analyticsLoading ? 'Loading...' : 'Refresh' }}
              </button>
            </div>
          </div>

          <!-- Loading -->
          <div v-if="analyticsLoading && !analyticsData" class="text-center py-8 text-gray-400">
            Loading analytics...
          </div>

          <!-- Summary Cards -->
          <div v-if="analyticsData" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Total Views</div>
              <div class="text-2xl font-bold">{{ analyticsData.totals?.views?.toLocaleString() || 0 }}</div>
              <div class="text-xs text-gray-500 mt-1">Avg: {{ analyticsData.averages?.views_per_period || 0 }}/{{ analyticsPeriod }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">Total Likes</div>
              <div class="text-2xl font-bold">{{ analyticsData.totals?.likes?.toLocaleString() || 0 }}</div>
              <div class="text-xs text-gray-500 mt-1">Avg: {{ analyticsData.averages?.likes_per_period || 0 }}/{{ analyticsPeriod }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">New Videos</div>
              <div class="text-2xl font-bold">{{ analyticsData.totals?.new_videos?.toLocaleString() || 0 }}</div>
            </div>
            <div class="bg-gray-900 rounded-lg p-6">
              <div class="text-sm text-gray-400 mb-1">New Users</div>
              <div class="text-2xl font-bold">{{ analyticsData.totals?.new_users?.toLocaleString() || 0 }}</div>
            </div>
          </div>

          <!-- Daily Share & Click Overview -->
          <div v-if="analyticsData && analytics.length > 0 && analyticsData.totals?.shares !== undefined" class="bg-gray-900 rounded-lg p-6 mt-6">
            <h3 class="text-lg font-bold mb-4">Daily Share & Click Overview</h3>
            <p class="text-sm text-gray-400 mb-4">Overview of shares created and links opened per day</p>
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead class="bg-gray-800">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Date</th>
                    <th class="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Shares Created</th>
                    <th class="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Links Opened (Clicks)</th>
                    <th class="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">CTR</th>
                    <th class="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Clicks/Share</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-800">
                  <tr 
                    v-for="item in analytics" 
                    :key="item.date" 
                    class="hover:bg-gray-800"
                  >
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                      {{ formatAnalyticsDate(item.date) }}
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-right">
                      <span class="font-semibold text-blue-400">{{ (item.shares || 0).toLocaleString() }}</span>
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-right">
                      <span class="font-semibold text-green-400">{{ (item.share_clicks || 0).toLocaleString() }}</span>
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-300">
                      {{ item.shares ? ((item.share_clicks || 0) / item.shares * 100).toFixed(1) : 0 }}%
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-300">
                      {{ item.shares ? ((item.share_clicks || 0) / item.shares).toFixed(2) : '0.00' }}
                    </td>
                  </tr>
                </tbody>
                <tfoot v-if="analyticsData.totals" class="bg-gray-800">
                  <tr>
                    <td class="px-4 py-3 text-sm font-bold text-gray-200">Total</td>
                    <td class="px-4 py-3 text-sm text-right font-bold text-blue-400">
                      {{ (analyticsData.totals.shares || 0).toLocaleString() }}
                    </td>
                    <td class="px-4 py-3 text-sm text-right font-bold text-green-400">
                      {{ (analyticsData.totals.share_clicks || 0).toLocaleString() }}
                    </td>
                    <td class="px-4 py-3 text-sm text-right font-bold text-gray-200">
                      {{ analyticsData.share_metrics?.click_through_rate || 0 }}%
                    </td>
                    <td class="px-4 py-3 text-sm text-right font-bold text-gray-200">
                      {{ analyticsData.totals.shares ? (analyticsData.totals.share_clicks / analyticsData.totals.shares).toFixed(2) : '0.00' }}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <!-- Analytics Table -->
          <div v-if="analyticsData && analytics.length > 0" class="bg-gray-900 rounded-lg overflow-hidden">
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead class="bg-gray-800">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Date</th>
                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Views</th>
                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Likes</th>
                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Videos</th>
                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Users</th>
                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Shares</th>
                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Clicks</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-800">
                  <tr v-for="item in analytics" :key="item.date" class="hover:bg-gray-800">
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {{ formatAnalyticsDate(item.date) }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                      {{ item.views?.toLocaleString() || 0 }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                      {{ item.likes?.toLocaleString() || 0 }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                      {{ item.videos?.toLocaleString() || 0 }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                      {{ item.users?.toLocaleString() || 0 }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                      {{ item.shares?.toLocaleString() || 0 }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                      {{ item.share_clicks?.toLocaleString() || 0 }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else-if="!analyticsLoading && analyticsData && analytics.length === 0" class="bg-gray-900 rounded-lg p-12 text-center">
            <div class="text-6xl mb-4">📊</div>
            <h4 class="text-xl font-bold mb-2">No Data</h4>
            <p class="text-gray-400">No analytics data available for the selected period.</p>
          </div>

          <!-- Additional Details -->
          <div v-if="analyticsData && analytics.length > 0" class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <!-- Engagement Metrics -->
            <div class="bg-gray-900 rounded-lg p-6">
              <h3 class="text-lg font-bold mb-4">Engagement Metrics</h3>
              <div class="space-y-4">
                <div>
                  <div class="flex justify-between items-center mb-1">
                    <span class="text-sm text-gray-400">Engagement Rate</span>
                    <span class="text-lg font-bold">{{ analyticsData.engagement_rate || 0 }}%</span>
                  </div>
                  <div class="text-xs text-gray-500">Likes per 100 views</div>
                </div>
                <div v-if="analyticsData.growth">
                  <div class="flex justify-between items-center mb-1">
                    <span class="text-sm text-gray-400">Views Growth</span>
                    <span :class="['text-lg font-bold', analyticsData.growth.views_growth >= 0 ? 'text-green-400' : 'text-red-400']">
                      {{ analyticsData.growth.views_growth >= 0 ? '+' : '' }}{{ analyticsData.growth.views_growth || 0 }}%
                    </span>
                  </div>
                  <div class="text-xs text-gray-500">Second half vs first half</div>
                </div>
                <div v-if="analyticsData.growth">
                  <div class="flex justify-between items-center mb-1">
                    <span class="text-sm text-gray-400">Likes Growth</span>
                    <span :class="['text-lg font-bold', analyticsData.growth.likes_growth >= 0 ? 'text-green-400' : 'text-red-400']">
                      {{ analyticsData.growth.likes_growth >= 0 ? '+' : '' }}{{ analyticsData.growth.likes_growth || 0 }}%
                    </span>
                  </div>
                  <div class="text-xs text-gray-500">Second half vs first half</div>
                </div>
              </div>
            </div>

            <!-- Most Active Users -->
            <div class="bg-gray-900 rounded-lg p-6">
              <h3 class="text-lg font-bold mb-4">Most Active Users</h3>
              <div v-if="analyticsData.most_active_users && analyticsData.most_active_users.length > 0" class="space-y-2">
                <div
                  v-for="(user, index) in analyticsData.most_active_users"
                  :key="user.id"
                  class="flex items-center justify-between p-2 hover:bg-gray-800 rounded"
                >
                  <div class="flex items-center gap-3">
                    <span class="text-gray-500 text-sm w-6">#{{ index + 1 }}</span>
                    <span class="text-white">{{ user.username }}</span>
                  </div>
                  <span class="text-gray-400 text-sm">{{ user.videos_uploaded }} videos</span>
                </div>
              </div>
              <div v-else class="text-gray-400 text-center py-4 text-sm">No active users in this period</div>
            </div>
          </div>

          <!-- Top Videos -->
          <div v-if="analyticsData && (analyticsData.top_videos_by_views?.length > 0 || analyticsData.top_videos_by_likes?.length > 0)" class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <!-- Top Videos by Views -->
            <div class="bg-gray-900 rounded-lg p-6">
              <h3 class="text-lg font-bold mb-4">Top Videos by Views</h3>
              <div v-if="analyticsData.top_videos_by_views && analyticsData.top_videos_by_views.length > 0" class="space-y-3">
                <div
                  v-for="(video, index) in analyticsData.top_videos_by_views"
                  :key="video.id"
                  class="p-3 bg-gray-800 rounded hover:bg-gray-700 transition-colors"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="text-gray-500 text-xs font-bold">#{{ index + 1 }}</span>
                        <span class="text-white text-sm font-medium truncate">{{ video.title || 'Untitled' }}</span>
                      </div>
                      <div class="text-xs text-gray-400">by @{{ video.user?.username || 'Unknown' }}</div>
                    </div>
                    <div class="text-right flex-shrink-0">
                      <div class="text-sm font-bold text-blue-400">{{ video.views?.toLocaleString() || 0 }}</div>
                      <div class="text-xs text-gray-500">views</div>
                      <div class="text-xs text-gray-500 mt-1">{{ video.likes || 0 }} likes</div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="text-gray-400 text-center py-4 text-sm">No videos in this period</div>
            </div>

            <!-- Top Videos by Likes -->
            <div class="bg-gray-900 rounded-lg p-6">
              <h3 class="text-lg font-bold mb-4">Top Videos by Likes</h3>
              <div v-if="analyticsData.top_videos_by_likes && analyticsData.top_videos_by_likes.length > 0" class="space-y-3">
                <div
                  v-for="(video, index) in analyticsData.top_videos_by_likes"
                  :key="video.id"
                  class="p-3 bg-gray-800 rounded hover:bg-gray-700 transition-colors"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="text-gray-500 text-xs font-bold">#{{ index + 1 }}</span>
                        <span class="text-white text-sm font-medium truncate">{{ video.title || 'Untitled' }}</span>
                      </div>
                      <div class="text-xs text-gray-400">by @{{ video.user?.username || 'Unknown' }}</div>
                    </div>
                    <div class="text-right flex-shrink-0">
                      <div class="text-sm font-bold text-pink-400">{{ video.likes?.toLocaleString() || 0 }}</div>
                      <div class="text-xs text-gray-500">likes</div>
                      <div class="text-xs text-gray-500 mt-1">{{ video.views || 0 }} views</div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="text-gray-400 text-center py-4 text-sm">No videos in this period</div>
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

        <!-- All Videos Tab -->
        <div v-else-if="activeTab === 'allVideos'" class="space-y-6">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-bold">All Videos</h2>
            <div class="flex gap-2">
              <select
                v-model="allVideosStatusFilter"
                @change="() => loadAllVideos()"
                class="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700"
              >
                <option value="">All Status</option>
                <option value="uploading">Uploading</option>
                <option value="processing">Processing</option>
                <option value="ready">Ready</option>
                <option value="failed">Failed</option>
                <option value="rejected">Rejected</option>
              </select>
              <button
                @click="() => loadAllVideos()"
                class="text-blue-400 hover:text-blue-300 text-sm"
              >
                Refresh
              </button>
            </div>
          </div>

          <!-- Loading Videos -->
          <div
            v-if="allVideosLoading && allVideos.length === 0"
            class="text-center py-8 text-gray-400"
          >
            Loading videos...
          </div>

          <!-- Empty State -->
          <div
            v-else-if="allVideos.length === 0"
            class="bg-gray-900 rounded-lg p-12 text-center"
          >
            <div class="text-6xl mb-4">📹</div>
            <h4 class="text-xl font-bold mb-2">No Videos Found</h4>
            <p class="text-gray-400">No videos match the current filter.</p>
          </div>

          <!-- Videos List -->
          <div v-else class="space-y-4">
            <div
              v-for="video in allVideos"
              :key="video.id"
              class="bg-gray-900 rounded-lg p-6"
            >
              <div class="flex flex-col sm:flex-row gap-6">
                <!-- Thumbnail -->
                <div class="relative w-full sm:w-48 h-64 sm:h-32 bg-gray-800 rounded-lg overflow-hidden flex-shrink-0">
                  <img
                    v-if="video.thumbnail"
                    :src="getAbsoluteUrl(video.thumbnail)"
                    :alt="video.title || 'Video thumbnail'"
                    class="w-full h-full object-cover"
                  />
                  <div
                    :class="[
                      'absolute top-2 left-2 text-white text-xs px-2 py-1 rounded',
                      video.status === 'ready' ? 'bg-green-600' :
                      video.status === 'processing' || video.status === 'uploading' ? 'bg-yellow-600' :
                      video.status === 'failed' ? 'bg-red-600' : 'bg-gray-600'
                    ]"
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
                  <div class="flex gap-3 flex-wrap">
                    <a
                      :href="`/?video=${video.id}`"
                      target="_blank"
                      class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors text-sm"
                    >
                      View in Feed
                    </a>
                    <a
                      v-if="video.url_mp4"
                      :href="getAbsoluteUrl(video.url_mp4)"
                      target="_blank"
                      class="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg font-semibold transition-colors text-sm"
                    >
                      Preview
                    </a>
                    <button
                      v-if="video.status === 'ready'"
                      @click="approveVideo(video.id)"
                      :disabled="processingVideo === video.id"
                      class="bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-semibold transition-colors text-sm"
                    >
                      Approve
                    </button>
                    <button
                      v-if="video.status !== 'rejected'"
                      @click="showRejectDialog(video)"
                      :disabled="processingVideo === video.id"
                      class="bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-semibold transition-colors text-sm"
                    >
                      Reject
                    </button>
                    <button
                      @click="deleteVideoAdmin(video.id)"
                      :disabled="deletingVideo === video.id"
                      class="bg-red-800 hover:bg-red-900 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-semibold transition-colors text-sm"
                    >
                      {{ deletingVideo === video.id ? 'Deleting...' : 'Delete' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Load More -->
            <div
              v-if="hasMoreAllVideos && !allVideosLoading"
              class="flex justify-center"
            >
              <button
                @click="loadMoreAllVideos"
                class="bg-gray-800 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                Load More
              </button>
            </div>
          </div>
        </div>

        <!-- Users Tab -->
        <div v-else-if="activeTab === 'users'" class="space-y-6">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-bold">Users</h2>
            <div class="flex gap-2">
              <input
                v-model="usersSearch"
                @keyup.enter="searchUsers"
                type="text"
                placeholder="Search by username or email..."
                class="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700"
              />
              <button
                @click="searchUsers"
                class="text-blue-400 hover:text-blue-300 text-sm px-4 py-2"
              >
                Search
              </button>
              <button
                @click="() => loadUsers()"
                class="text-blue-400 hover:text-blue-300 text-sm"
              >
                Refresh
              </button>
            </div>
          </div>

          <!-- Loading Users -->
          <div
            v-if="usersLoading && users.length === 0"
            class="text-center py-8 text-gray-400"
          >
            Loading users...
          </div>

          <!-- Empty State -->
          <div
            v-else-if="users.length === 0"
            class="bg-gray-900 rounded-lg p-12 text-center"
          >
            <div class="text-6xl mb-4">👥</div>
            <h4 class="text-xl font-bold mb-2">No Users Found</h4>
            <p class="text-gray-400">No users match the current search.</p>
          </div>

          <!-- Users List -->
          <div v-else class="space-y-4">
            <div
              v-for="user in users"
              :key="user.id"
              class="bg-gray-900 rounded-lg p-6"
            >
              <div class="flex items-center justify-between">
                <div class="flex-1">
                  <div class="flex items-center gap-3 mb-2">
                    <h3 class="text-lg font-bold">{{ user.username }}</h3>
                    <span
                      v-if="user.is_admin"
                      class="px-2 py-1 bg-purple-600 text-white rounded text-xs font-semibold"
                    >
                      ADMIN
                    </span>
                    <span
                      v-if="!user.is_active"
                      class="px-2 py-1 bg-red-600 text-white rounded text-xs font-semibold"
                    >
                      BANNED
                    </span>
                  </div>
                  <p class="text-sm text-gray-400 mb-2">{{ user.email }}</p>
                  <div class="flex gap-4 text-sm text-gray-500">
                    <span>Videos: {{ user.video_count || 0 }}</span>
                    <span>•</span>
                    <span>Joined: {{ formatDate(user.created_at) }}</span>
                  </div>
                </div>

                <!-- Actions -->
                <div class="flex flex-col gap-2 ml-4">
                  <button
                    @click="toggleUserActive(user.id, user.is_active)"
                    :disabled="updatingUser === user.id"
                    :class="[
                      'px-4 py-2 rounded-lg font-semibold transition-colors text-sm whitespace-nowrap',
                      user.is_active
                        ? 'bg-red-600 hover:bg-red-700 text-white'
                        : 'bg-green-600 hover:bg-green-700 text-white',
                      updatingUser === user.id && 'disabled:bg-gray-700 disabled:cursor-not-allowed'
                    ]"
                  >
                    {{ updatingUser === user.id ? 'Updating...' : (user.is_active ? 'Ban' : 'Unban') }}
                  </button>
                  <button
                    v-if="!user.is_admin"
                    @click="toggleUserAdmin(user.id, user.is_admin)"
                    :disabled="updatingUser === user.id"
                    class="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-semibold transition-colors text-sm whitespace-nowrap"
                  >
                    Make Admin
                  </button>
                </div>
              </div>
            </div>

            <!-- Load More -->
            <div
              v-if="hasMoreUsers && !usersLoading"
              class="flex justify-center"
            >
              <button
                @click="loadMoreUsers"
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
                    <div class="flex items-center justify-between mb-2">
                      <div class="text-sm font-semibold">
                        {{ report.type === 'video' ? t('admin.reports.video') : t('admin.reports.user') }}:
                      </div>
                      <div class="flex gap-2">
                        <NuxtLink
                          v-if="report.type === 'video'"
                          :to="`/?video=${report.target.id}`"
                          target="_blank"
                          class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs font-semibold transition-colors"
                        >
                          View Video
                        </NuxtLink>
                        <NuxtLink
                          v-else
                          :to="`/users/${report.target.id}`"
                          target="_blank"
                          class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs font-semibold transition-colors"
                        >
                          View User
                        </NuxtLink>
                      </div>
                    </div>
                    <div
                      v-if="report.type === 'video'"
                      class="text-sm text-gray-300"
                    >
                      <div class="font-semibold mb-1">{{ report.target.title || t('profile.untitled') }}</div>
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
import { ref, computed, onMounted, watch, defineAsyncComponent } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { useApi } from '~/composables/useApi'
import { useI18n } from '~/composables/useI18n'

definePageMeta({
  middleware: 'admin',
})

// Lazy-load VisitorMap component (only loads when Visitor Analytics tab is active)
// This ensures Leaflet library is NOT bundled in the main app bundle
const VisitorMap = defineAsyncComponent(() => import('~/components/VisitorMap.vue'))

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

// Check admin status - handle both boolean and string from localStorage
const isAdmin = computed(() => {
  const adminStatus = authStore.user?.is_admin
  return adminStatus === true || adminStatus === 'true'
})

const tabs = [
  { id: 'stats', label: t('admin.tabs.overview') || 'Overview' },
  { id: 'analytics', label: 'Analytics' },
  { id: 'shareAnalytics', label: 'Share Analytics' },
  { id: 'adAnalytics', label: 'Ad Analytics' },
  { id: 'visitorAnalytics', label: 'Visitor Analytics' },
  { id: 'videos', label: t('admin.tabs.pendingVideos') || 'Pending Videos' },
  { id: 'allVideos', label: t('admin.tabs.allVideos') || 'All Videos' },
  { id: 'users', label: t('admin.tabs.users') || 'Users' },
  { id: 'reports', label: t('admin.tabs.reports') || 'Reports' },
]
const activeTab = ref('stats')
const loading = ref(false)
const error = ref<string | null>(null)

// Stats
const stats = ref<any | null>(null)

// Videos
const pendingVideos = ref<any[]>([])
const videosLoading = ref(false)
const nextVideoCursor = ref<string | null>(null)
const hasMoreVideos = ref(true)
const processingVideo = ref<string | null>(null)

// All Videos
const allVideos = ref<any[]>([])
const allVideosLoading = ref(false)
const allVideosStatusFilter = ref('')
const nextAllVideoCursor = ref<string | null>(null)
const hasMoreAllVideos = ref(true)
const deletingVideo = ref<string | null>(null)

// Users
const users = ref<any[]>([])
const usersLoading = ref(false)
const usersSearch = ref('')
const nextUserCursor = ref<string | null>(null)
const hasMoreUsers = ref(true)
const updatingUser = ref<string | null>(null)
const selectedUser = ref<any | null>(null)

// Analytics
const analytics = ref<any[]>([])
const analyticsLoading = ref(false)
const analyticsPeriod = ref<'day' | 'week'>('day')
const analyticsDays = ref(30)
const analyticsData = ref<any | null>(null)

// Share Analytics
const shareAnalytics = ref<any[]>([])
const shareAnalyticsLoading = ref(false)
const shareAnalyticsPeriod = ref<'day' | 'week'>('week')
const shareAnalyticsDays = ref(30)
const shareAnalyticsData = ref<any | null>(null)

// Ad Analytics
const adAnalyticsLoading = ref(false)
const adAnalyticsPeriod = ref<'day' | 'week'>('week')
const adAnalyticsDays = ref(30)
const adAnalyticsData = ref<any | null>(null)

// Visitor Analytics
const visitorAnalyticsData = ref<any | null>(null)
const visitorLocations = ref<any[]>([])
const recentVisits = ref<any[]>([])
const visitorAnalyticsLoading = ref(false)
const visitorAnalyticsDays = ref(30)

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

const formatAnalyticsDate = (dateString: string, period?: 'day' | 'week'): string => {
  const date = new Date(dateString)
  const usePeriod = period || analyticsPeriod.value
  if (usePeriod === 'week') {
    // For weeks, show the start of the week
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }) + ' (Week)'
  }
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const loadStats = async () => {
  loading.value = true
  error.value = null
  try {
    stats.value = await api.get('/admin/stats')
    console.log('Stats loaded:', stats.value)
  } catch (err: any) {
    console.error('Failed to load stats:', err)
    error.value = err.message || 'Failed to load statistics'
  } finally {
    loading.value = false
  }
}

const loadAnalytics = async () => {
  analyticsLoading.value = true
  try {
    const response = await api.get<{
      period: string
      days: number
      analytics: Array<{
        date: string
        views: number
        likes: number
        videos: number
        users: number
        shares?: number
        share_clicks?: number
      }>
      totals: {
        views: number
        likes: number
        new_videos: number
        new_users: number
        shares?: number
        share_clicks?: number
      }
      averages: {
        views_per_period: number
        likes_per_period: number
        shares_per_period?: number
        share_clicks_per_period?: number
      }
      share_metrics?: {
        click_through_rate: number
      }
      top_videos_by_views?: Array<{
        id: string
        title: string
        user: { id: string; username: string }
        views: number
        likes: number
        created_at: string | null
      }>
      top_videos_by_likes?: Array<{
        id: string
        title: string
        user: { id: string; username: string }
        views: number
        likes: number
        created_at: string | null
      }>
      most_active_users?: Array<{
        id: string
        username: string
        videos_uploaded: number
      }>
      engagement_rate?: number
      growth?: {
        views_growth: number
        likes_growth: number
      }
    }>(`/admin/analytics?period=${analyticsPeriod.value}&days=${analyticsDays.value}`)
    analyticsData.value = response
    analytics.value = response.analytics || []
  } catch (err: any) {
    console.error('Failed to load analytics:', err)
    error.value = err.message || 'Failed to load analytics'
  } finally {
    analyticsLoading.value = false
  }
}

const loadShareAnalytics = async () => {
  shareAnalyticsLoading.value = true
  try {
    const response = await api.get<{
      period: string
      days: number
      video_id?: string
      summary: {
        total_shares: number
        total_clicks: number
        unique_clickers: number
        shares_with_clicks: number
      }
      metrics: {
        click_through_rate: number
        avg_clicks_per_share: number
        share_conversion_rate: number
        avg_clicks_per_clicker: number
        avg_time_to_first_click_hours: number
      }
      over_time: {
        shares: Array<{ date: string; shares: number }>
        clicks: Array<{ date: string; clicks: number }>
      }
      top_videos: {
        most_shared: Array<{ video_id: string; title: string; share_count: number }>
        most_clicked: Array<{ video_id: string; title: string; click_count: number }>
      }
      top_sharers: Array<{ sharer_session_id: string; share_count: number }>
    }>(`/admin/shares/analytics?period=${shareAnalyticsPeriod.value}&days=${shareAnalyticsDays.value}`)
    shareAnalyticsData.value = response
  } catch (err: any) {
    console.error('Failed to load share analytics:', err)
    error.value = err.message || 'Failed to load share analytics'
  } finally {
    shareAnalyticsLoading.value = false
  }
}

const loadAdAnalytics = async () => {
  adAnalyticsLoading.value = true
  try {
    const response = await api.get<{
      period: string
      days: number
      totals: {
        clicks: number
        views: number
        unique_clickers: number
        unique_auth_clickers: number
      }
      metrics: {
        click_through_rate: number
        avg_clicks_per_view: number
        avg_clicks_per_clicker: number
      }
      clicks_over_time: Array<{ date: string; clicks: number }>
      views_over_time: Array<{ date: string; views: number }>
      top_videos: Array<{
        id: string
        title: string
        user: { id: string; username: string }
        clicks: number
        views: number
        ctr: number
      }>
    }>(`/admin/ads/analytics?period=${adAnalyticsPeriod.value}&days=${adAnalyticsDays.value}`)
    adAnalyticsData.value = response
  } catch (err: any) {
    console.error('Failed to load ad analytics:', err)
    error.value = err.message || 'Failed to load ad analytics'
  } finally {
    adAnalyticsLoading.value = false
  }
}

const loadVisitorAnalytics = async () => {
  visitorAnalyticsLoading.value = true
  try {
    // Load stats
    const statsResponse = await api.get(`/admin/visitors/stats?days=${visitorAnalyticsDays.value}`)
    visitorAnalyticsData.value = statsResponse
    
    // Load locations for map
    const locationsResponse = await api.get(`/admin/visitors/locations?days=${visitorAnalyticsDays.value}`)
    visitorLocations.value = locationsResponse
    
    // Load recent visits
    const recentResponse = await api.get('/admin/visitors/recent?limit=50')
    recentVisits.value = recentResponse
  } catch (err: any) {
    console.error('Failed to load visitor analytics:', err)
    error.value = err.message || 'Failed to load visitor analytics'
  } finally {
    visitorAnalyticsLoading.value = false
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

// All Videos Functions
const loadAllVideos = async (cursor?: string) => {
  if (allVideosLoading.value || (!hasMoreAllVideos.value && cursor)) return
  
  allVideosLoading.value = true
  try {
    const params = new URLSearchParams()
    if (allVideosStatusFilter.value) {
      params.append('status', allVideosStatusFilter.value)
    }
    if (cursor) {
      params.append('cursor', cursor)
    }
    
    const response = await api.get<{
      videos: any[]
      next_cursor: string | null
      has_more: boolean
    }>(`/admin/videos${params.toString() ? `?${params.toString()}` : ''}`)
    
    if (cursor) {
      allVideos.value.push(...response.videos)
    } else {
      allVideos.value = response.videos
    }
    
    nextAllVideoCursor.value = response.next_cursor
    hasMoreAllVideos.value = response.has_more
  } catch (err) {
    console.error('Failed to load all videos:', err)
  } finally {
    allVideosLoading.value = false
  }
}

const loadMoreAllVideos = () => {
  if (hasMoreAllVideos.value && nextAllVideoCursor.value) {
    loadAllVideos(nextAllVideoCursor.value)
  }
}

const deleteVideoAdmin = async (videoId: string) => {
  if (!confirm('Are you sure you want to delete this video? This action cannot be undone.')) {
    return
  }
  
  deletingVideo.value = videoId
  try {
    await api.delete(`/admin/videos/${videoId}`)
    // Remove from list
    allVideos.value = allVideos.value.filter(v => v.id !== videoId)
    // Reload stats
    loadStats()
  } catch (err) {
    console.error('Failed to delete video:', err)
    alert(t('errors.generic'))
  } finally {
    deletingVideo.value = null
  }
}

// Users Functions
const loadUsers = async (cursor?: string) => {
  if (usersLoading.value || (!hasMoreUsers.value && cursor)) return
  
  usersLoading.value = true
  try {
    const params = new URLSearchParams()
    if (usersSearch.value) {
      params.append('search', usersSearch.value)
    }
    if (cursor) {
      params.append('cursor', cursor)
    }
    
    const response = await api.get<{
      users: any[]
      next_cursor: string | null
      has_more: boolean
    }>(`/admin/users${params.toString() ? `?${params.toString()}` : ''}`)
    
    if (cursor) {
      users.value.push(...response.users)
    } else {
      users.value = response.users
    }
    
    nextUserCursor.value = response.next_cursor
    hasMoreUsers.value = response.has_more
  } catch (err) {
    console.error('Failed to load users:', err)
  } finally {
    usersLoading.value = false
  }
}

const loadMoreUsers = () => {
  if (hasMoreUsers.value && nextUserCursor.value) {
    loadUsers(nextUserCursor.value)
  }
}

const searchUsers = () => {
  users.value = []
  nextUserCursor.value = null
  hasMoreUsers.value = true
  loadUsers()
}

const toggleUserActive = async (userId: string, currentStatus: boolean) => {
  updatingUser.value = userId
  try {
    await api.patch(`/admin/users/${userId}`, { is_active: !currentStatus })
    // Update user in list
    const user = users.value.find(u => u.id === userId)
    if (user) {
      user.is_active = !currentStatus
    }
    // Reload stats
    loadStats()
  } catch (err) {
    console.error('Failed to update user:', err)
    alert(t('errors.generic'))
  } finally {
    updatingUser.value = null
  }
}

const toggleUserAdmin = async (userId: string, currentStatus: boolean) => {
  if (!confirm(`Are you sure you want to ${currentStatus ? 'remove' : 'grant'} admin privileges?`)) {
    return
  }
  
  updatingUser.value = userId
  try {
    await api.patch(`/admin/users/${userId}`, { is_admin: !currentStatus })
    // Update user in list
    const user = users.value.find(u => u.id === userId)
    if (user) {
      user.is_admin = !currentStatus
    }
  } catch (err) {
    console.error('Failed to update user:', err)
    alert(t('errors.generic'))
  } finally {
    updatingUser.value = null
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
  } else if (newTab === 'analytics') {
    loadAnalytics()
  } else if (newTab === 'shareAnalytics') {
    loadShareAnalytics()
  } else if (newTab === 'adAnalytics') {
    loadAdAnalytics()
  } else if (newTab === 'visitorAnalytics') {
    loadVisitorAnalytics()
  } else if (newTab === 'videos') {
    loadPendingVideos()
  } else if (newTab === 'allVideos') {
    loadAllVideos()
  } else if (newTab === 'users') {
    loadUsers()
  } else if (newTab === 'reports') {
    loadReports()
  }
})

watch([analyticsPeriod, analyticsDays], () => {
  if (activeTab.value === 'analytics') {
    loadAnalytics()
  }
})

watch([shareAnalyticsPeriod, shareAnalyticsDays], () => {
  if (activeTab.value === 'shareAnalytics') {
    loadShareAnalytics()
  }
})

onMounted(() => {
  // Initialize auth from storage on mount
  authStore.initFromStorage()
  
  // Double-check admin status on client-side (handle both boolean and string)
  if (!authStore.isAuthenticated) {
    navigateTo('/login')
    return
  }
  
  const adminStatus = authStore.user?.is_admin
  const isUserAdmin = adminStatus === true || adminStatus === 'true'
  if (!isUserAdmin) {
    navigateTo('/')
    return
  }
  
  // Load stats - user is admin, so load data
  loadStats()
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
