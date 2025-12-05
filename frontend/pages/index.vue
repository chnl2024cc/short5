<template>
  <div class="w-full bg-black relative page-container">
    <!-- Top Navigation Bar -->
    <div class="absolute top-0 left-0 right-0 z-40 bg-gradient-to-b from-black/80 to-transparent px-4 py-3" style="padding-top: max(calc(0.75rem + env(safe-area-inset-top)), 0.75rem);">
      <div class="flex items-center justify-between">
        <h1 class="text-xl font-bold text-white">{{ t('index.title') }}</h1>
        <div class="flex items-center gap-4">
          <!-- Liked Videos Link - Available for everyone (authenticated users see server-side, unauthenticated see localStorage) -->
          <NuxtLink
            to="/liked"
            class="text-white hover:text-blue-400 transition-colors"
            :title="t('index.likedVideos')"
          >
            <svg
              class="w-6 h-6"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
            </svg>
          </NuxtLink>
          <!-- Show login link as default (SSR-safe), then update after mount based on auth state -->
          <NuxtLink
            v-if="!isMounted || !authStore.isAuthenticated"
            to="/login"
            class="text-white hover:text-blue-400 transition-colors text-sm font-medium"
            :title="t('index.login')"
          >
            {{ t('index.login') }}
          </NuxtLink>
          <NuxtLink
            v-if="isMounted && authStore.isAuthenticated"
            to="/profile"
            class="text-white hover:text-blue-400 transition-colors"
            :title="t('index.profile')"
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
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </NuxtLink>
          <NuxtLink
            v-if="isMounted && authStore.user?.is_admin"
            to="/admin"
            class="text-white hover:text-blue-400 transition-colors"
            :title="t('index.adminDashboard')"
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
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
          </NuxtLink>
        </div>
      </div>
    </div>

    <VideoFeed />
    
    <!-- Floating Upload Button (only for authenticated users, shown after mount) -->
    <NuxtLink
      v-if="isMounted && authStore.isAuthenticated"
      to="/upload"
      class="fixed right-6 z-50 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg transition-all hover:scale-110"
      style="bottom: max(calc(1.5rem + env(safe-area-inset-bottom)), 1.5rem);"
      :title="t('index.uploadVideo')"
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
          d="M12 4v16m8-8H4"
        />
      </svg>
    </NuxtLink>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'
import { useI18n } from '~/composables/useI18n'
import { useVideosStore } from '~/stores/videos'
import { useRoute } from 'vue-router'
import type { Video } from '~/types/video'

// Main feed page - accessible to everyone (anonymous users can view)
definePageMeta({
  // No auth middleware - allow anonymous access
})

const authStore = useAuthStore()
const { t } = useI18n()
const route = useRoute()
const videosStore = useVideosStore()

// Track if component is mounted to avoid hydration mismatches
// During SSR and initial render, show safe default (login link)
// After mount, initialize auth and show correct content
const isMounted = ref(false)

// Dynamic meta tags for video sharing
const videoId = computed(() => route.query.video as string | undefined)
const config = useRuntimeConfig()
const backendBaseUrl = config.public.backendBaseUrl

// Fetch video data server-side for proper meta tags (WhatsApp crawler needs this)
const { data: sharedVideo } = await useAsyncData(
  () => `video-${videoId.value || 'none'}`,
  async () => {
    const id = videoId.value
    if (!id) return null
    
    try {
      // Fetch video data server-side using direct API call
      const apiBaseUrl = config.public.apiBaseUrl
      const response = await $fetch<Video>(`${apiBaseUrl}/videos/${id}`, {
        // Don't require auth for public video sharing
        headers: {},
      })
      return response
    } catch (error) {
      // Video not found or error - return null to use default meta tags
      console.warn('Failed to load shared video for meta tags:', error)
      return null
    }
  },
  {
    // Only fetch if videoId is present
    watch: [videoId],
    // Fetch on server-side for WhatsApp crawler
    server: true,
    // Don't block navigation
    lazy: true,
    default: () => null,
  }
)

// Use composable for public assets and site origin (Nuxt 4 best practice)
const { getPublicAssetUrl, siteOrigin } = usePublicAsset()

// Get absolute URL helper for backend assets (videos, thumbnails)
const getAbsoluteUrl = (url: string | null | undefined, fallback: string): string => {
  if (url) {
    // If already absolute, return as-is
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url
    }
    // If relative, prepend backend base URL
    if (url.startsWith('/')) {
      return `${backendBaseUrl}${url}`
    }
    // Otherwise, assume it's relative to backend
    return `${backendBaseUrl}/${url}`
  }
  // Return absolute fallback URL for public assets
  return getPublicAssetUrl(fallback).value
}

// Compute OG image URL (must be absolute for WhatsApp)
const ogImage = computed(() => {
  if (sharedVideo.value?.thumbnail) {
    return getAbsoluteUrl(sharedVideo.value.thumbnail, '/og-image.svg')
  }
  return getPublicAssetUrl('/og-image.svg').value
})

// Compute OG URL (must be absolute)
const ogUrl = computed(() => {
  if (videoId.value) {
    return `${siteOrigin.value}/?video=${videoId.value}`
  }
  return siteOrigin.value
})

// Set dynamic meta tags for video sharing
useHead({
  title: computed(() => sharedVideo.value?.title 
    ? `${sharedVideo.value.title} - Short5 Platform`
    : 'Short5 Platform'),
  meta: [
    {
      name: 'description',
      content: computed(() => sharedVideo.value?.description 
        ? sharedVideo.value.description
        : 'Short5 Platform - Short Video Swiper like Tinder experience'),
    },
    {
      property: 'og:type',
      content: computed(() => sharedVideo.value ? 'video.other' : 'website'),
    },
    {
      property: 'og:title',
      content: computed(() => sharedVideo.value?.title 
        ? `${sharedVideo.value.title} - Short5 Platform`
        : 'Short5 Platform - Share Amazing Videos'),
    },
    {
      property: 'og:description',
      content: computed(() => sharedVideo.value?.description 
        ? sharedVideo.value.description
        : 'Short5 Platform - Short Video Swiper like Tinder experience'),
    },
    {
      property: 'og:image',
      content: ogImage,
    },
    {
      property: 'og:image:width',
      content: '1200',
    },
    {
      property: 'og:image:height',
      content: '630',
    },
    {
      property: 'og:image:alt',
      content: computed(() => sharedVideo.value?.title 
        ? sharedVideo.value.title
        : 'Short5 Platform'),
    },
    {
      property: 'og:url',
      content: ogUrl,
    },
    {
      name: 'twitter:card',
      content: 'summary_large_image',
    },
    {
      name: 'twitter:title',
      content: computed(() => sharedVideo.value?.title 
        ? `${sharedVideo.value.title} - Short5 Platform`
        : 'Short5 Platform - Share Amazing Videos'),
    },
    {
      name: 'twitter:description',
      content: computed(() => sharedVideo.value?.description 
        ? sharedVideo.value.description
        : 'Short5 Platform - Short Video Swiper like Tinder experience'),
    },
    {
      name: 'twitter:image',
      content: ogImage,
    },
    {
      name: 'twitter:image:alt',
      content: computed(() => sharedVideo.value?.title 
        ? sharedVideo.value.title
        : 'Short5 Platform'),
    },
  ],
  link: [
    {
      rel: 'icon',
      type: 'image/svg+xml',
      href: getPublicAssetUrl('/icon.svg'),
    },
    {
      rel: 'apple-touch-icon',
      href: getPublicAssetUrl('/icon.svg'),
    },
  ],
})

onMounted(async () => {
  if (process.client) {
    authStore.initFromStorage()
    // Set mounted flag after auth is initialized to trigger reactive update
    isMounted.value = true
  }
})
</script>

<style scoped>
.page-container {
  /* Use proper viewport height cascade for mobile browsers (especially iOS Safari) */
  height: 100vh; /* Fallback for older browsers */
  height: 100svh; /* Small viewport (iOS toolbars visible) */
  height: 100dvh; /* Dynamic viewport (correct when bars collapse) */
  min-height: 100vh; /* Fallback */
  min-height: 100svh; /* Small viewport (iOS toolbars visible) */
  min-height: 100dvh; /* Dynamic viewport (correct when bars collapse) */
  /* Account for bottom safe area (home indicator) */
  padding-bottom: env(safe-area-inset-bottom);
  overflow: hidden;
  position: relative;
}
</style>

