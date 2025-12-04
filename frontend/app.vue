<template>
  <div class="app-wrapper">
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

// Initialize auth store from localStorage on app load
if (process.client) {
  const authStore = useAuthStore()
  authStore.initFromStorage()
}
</script>

<style>
.app-wrapper {
  width: 100%;
  /* Use proper viewport height cascade for mobile browsers (especially iOS Safari) */
  height: 100vh; /* Fallback for older browsers */
  height: 100svh; /* Small viewport (iOS toolbars visible) */
  height: 100dvh; /* Dynamic viewport (correct when bars collapse) */
  min-height: 100vh; /* Fallback */
  min-height: 100svh; /* Small viewport (iOS toolbars visible) */
  min-height: 100dvh; /* Dynamic viewport (correct when bars collapse) */
  overflow: hidden;
}
</style>

