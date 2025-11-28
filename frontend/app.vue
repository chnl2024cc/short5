<template>
  <div>
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

