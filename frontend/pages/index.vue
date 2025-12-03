<template>
  <div class="w-full bg-black relative" style="height: 100dvh; height: 100vh; min-height: 100dvh; min-height: 100vh;">
    <!-- Top Navigation Bar -->
    <div class="absolute top-0 left-0 right-0 z-40 bg-gradient-to-b from-black/80 to-transparent px-4 py-3">
      <div class="flex items-center justify-between">
        <h1 class="text-xl font-bold text-white">Short5</h1>
        <div class="flex items-center gap-4">
          <!-- Liked Videos Link - Available for everyone (authenticated users see server-side, unauthenticated see localStorage) -->
          <NuxtLink
            to="/liked"
            class="text-white hover:text-blue-400 transition-colors"
            title="Liked Videos"
          >
            <svg
              class="w-6 h-6"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
            </svg>
          </NuxtLink>
          <NuxtLink
            v-if="authStore.isAuthenticated"
            to="/profile"
            class="text-white hover:text-blue-400 transition-colors"
            title="Profile"
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
            v-if="!authStore.isAuthenticated"
            to="/login"
            class="text-white hover:text-blue-400 transition-colors text-sm font-medium"
            title="Login"
          >
            Login
          </NuxtLink>
          <NuxtLink
            v-if="authStore.user?.is_admin"
            to="/admin"
            class="text-white hover:text-blue-400 transition-colors"
            title="Admin Dashboard"
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
    
    <!-- Floating Upload Button (only for authenticated users) -->
    <NuxtLink
      v-if="authStore.isAuthenticated"
      to="/upload"
      class="fixed right-6 z-50 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg transition-all hover:scale-110"
      style="bottom: calc(1.5rem + env(safe-area-inset-bottom));"
      title="Upload Video"
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

// Main feed page - accessible to everyone (anonymous users can view)
definePageMeta({
  // No auth middleware - allow anonymous access
})

const authStore = useAuthStore()

// Initialize auth store on mount
onMounted(() => {
  if (process.client) {
    authStore.initFromStorage()
  }
})
</script>

