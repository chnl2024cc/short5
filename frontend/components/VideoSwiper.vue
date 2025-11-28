<template>
  <div class="video-container">
    <video
      ref="videoElement"
      :src="video.url_hls || video.url_mp4"
      class="w-full h-full object-contain"
      autoplay
      muted
      loop
      playsinline
    />
    <div
      v-if="showOverlay"
      :class="['swipe-overlay', overlayClass]"
    >
      <div :class="['swipe-overlay-text']">
        {{ overlayText }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Video swiper component with swipe gestures
// TODO: Implement swipe detection, overlay animation, and vote API call
</script>

