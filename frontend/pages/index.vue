<template>
  <div class="h-screen w-full bg-black relative">
    <VideoFeed />
    
    <!-- Floating Upload Button -->
    <NuxtLink
      to="/upload"
      class="fixed bottom-6 right-6 z-50 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg transition-all hover:scale-110"
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
// Main feed page - requires authentication
definePageMeta({
  middleware: 'auth',
})
</script>

