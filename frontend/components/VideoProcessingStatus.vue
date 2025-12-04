<template>
  <div class="bg-gray-900 rounded-lg p-6 space-y-4">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-white">{{ t('videoProcessing.title') }}</h3>
      <div class="text-sm text-gray-400">
        {{ t('videoProcessing.videoId') }}: {{ videoId.substring(0, 8) }}...
      </div>
    </div>

    <!-- Status Indicator -->
    <div class="space-y-3">
      <!-- Uploading Step -->
      <div class="flex items-center gap-3">
        <div
          :class="[
            'w-3 h-3 rounded-full transition-all',
            statusStep >= 1 ? 'bg-blue-500' : 'bg-gray-600',
          ]"
        />
        <div class="flex-1">
          <div class="text-sm font-medium text-gray-300">{{ t('videoProcessing.uploading') }}</div>
          <div class="text-xs text-gray-500">{{ t('videoProcessing.uploadingDescription') }}</div>
        </div>
        <div v-if="statusStep === 1" class="text-xs text-blue-400">{{ t('videoProcessing.inProgress') }}</div>
        <div v-else-if="statusStep > 1" class="text-xs text-green-400">{{ t('videoProcessing.complete') }}</div>
      </div>

      <!-- Processing Step -->
      <div class="flex items-center gap-3">
        <div
          :class="[
            'w-3 h-3 rounded-full transition-all',
            statusStep >= 2 ? 'bg-blue-500' : 'bg-gray-600',
            statusStep === 2 && 'animate-pulse',
          ]"
        />
        <div class="flex-1">
          <div class="text-sm font-medium text-gray-300">{{ t('videoProcessing.processing') }}</div>
          <div class="text-xs text-gray-500">{{ processingMessage }}</div>
        </div>
        <div v-if="statusStep === 2" class="text-xs text-blue-400">{{ t('videoProcessing.inProgress') }}</div>
        <div v-else-if="statusStep > 2" class="text-xs text-green-400">{{ t('videoProcessing.complete') }}</div>
      </div>

      <!-- Ready Step -->
      <div class="flex items-center gap-3">
        <div
          :class="[
            'w-3 h-3 rounded-full transition-all',
            statusStep >= 3 ? 'bg-green-500' : 'bg-gray-600',
          ]"
        />
        <div class="flex-1">
          <div class="text-sm font-medium text-gray-300">{{ t('videoProcessing.ready') }}</div>
          <div class="text-xs text-gray-500">{{ t('videoProcessing.readyDescription') }}</div>
        </div>
        <div v-if="statusStep >= 3" class="text-xs text-green-400">{{ t('videoProcessing.complete') }}</div>
      </div>
    </div>

    <!-- Progress Bar -->
    <div v-if="statusStep < 3" class="space-y-2">
      <div class="flex justify-between text-xs text-gray-400">
        <span>{{ statusText }}</span>
        <span>{{ elapsedTime }}</span>
      </div>
      <div class="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
        <div
          class="bg-blue-600 h-2 rounded-full transition-all duration-500"
          :style="{ width: `${progressPercent}%` }"
        />
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="errorReason" class="bg-red-900/50 border border-red-700 rounded-lg p-3">
      <div class="flex items-start gap-2">
        <span class="text-red-400">⚠️</span>
        <div class="flex-1">
          <div class="text-sm font-medium text-red-300">{{ t('videoProcessing.processingFailed') }}</div>
          <div class="text-xs text-red-400 mt-1">{{ errorReason }}</div>
        </div>
      </div>
    </div>

    <!-- Success Message -->
    <div v-if="status === 'ready'" class="bg-green-900/50 border border-green-700 rounded-lg p-3">
      <div class="flex items-center gap-2">
        <span class="text-green-400">✓</span>
        <div class="text-sm text-green-300">{{ t('videoProcessing.processingCompleted') }}</div>
      </div>
    </div>

    <!-- Polling Status -->
    <div v-if="isPolling" class="text-xs text-gray-500 flex items-center gap-2">
      <div class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
      <span>{{ t('videoProcessing.checkingStatus') }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useVideosStore } from '~/stores/videos'
import { useI18n } from '~/composables/useI18n'
import type { Video, VideoStatus } from '~/types/video'

interface Props {
  videoId: string
  autoPoll?: boolean
  pollInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoPoll: true,
  pollInterval: 2000, // Poll every 2 seconds
})

const emit = defineEmits<{
  statusChanged: [status: VideoStatus]
  ready: [videoData: Video]
  failed: [error: string]
}>()

const videosStore = useVideosStore()
const { t } = useI18n()

const status = ref<VideoStatus>('uploading')
const errorReason = ref<string | null>(null)
const videoData = ref<Video | null>(null)
const isPolling = ref(false)
const startTime = ref<number>(Date.now())
const lastUpdateTime = ref<number>(Date.now())

let pollTimer: NodeJS.Timeout | null = null

const statusStep = computed(() => {
  if (status.value === 'ready') return 3
  if (status.value === 'processing') return 2
  if (status.value === 'uploading') return 1
  if (status.value === 'failed') return 2
  return 0
})

const progressPercent = computed(() => {
  if (status.value === 'ready') return 100
  if (status.value === 'processing') {
    // Estimate progress based on elapsed time (rough estimate)
    const elapsed = (Date.now() - startTime.value) / 1000
    // Assume processing takes 30-60 seconds on average
    const estimatedTotal = 45
    const progress = Math.min(90, (elapsed / estimatedTotal) * 60) // 60% of progress is processing
    return 10 + progress // 10% for upload, rest for processing
  }
  if (status.value === 'uploading') return 10
  if (status.value === 'failed') return 0
  return 0
})

const statusText = computed(() => {
  if (status.value === 'uploading') return 'Uploading video...'
  if (status.value === 'processing') return 'Processing video...'
  if (status.value === 'ready') return 'Ready'
  if (status.value === 'failed') return 'Failed'
  return 'Unknown'
})

const processingMessage = computed(() => {
  if (status.value === 'processing') {
    const elapsed = (Date.now() - startTime.value) / 1000
    if (elapsed < 10) return 'Validating video file...'
    if (elapsed < 30) return 'Transcoding to MP4 format...'
    if (elapsed < 50) return 'Generating thumbnails...'
    return 'Finalizing video...'
  }
  return 'Processing video file...'
})

const elapsedTime = computed(() => {
  const seconds = Math.floor((Date.now() - startTime.value) / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
})

const checkStatus = async () => {
  if (isPolling.value) return // Prevent concurrent requests
  
  isPolling.value = true
  try {
    const data = await videosStore.getVideoStatus(props.videoId)
    videoData.value = data
    const newStatus: VideoStatus = data.status
    
    if (newStatus !== status.value) {
      status.value = newStatus
      errorReason.value = data.error_reason || null
      lastUpdateTime.value = Date.now()
      emit('statusChanged', newStatus)
      
      if (newStatus === 'ready') {
        emit('ready', data)
        stopPolling()
      } else if (newStatus === 'failed') {
        emit('failed', errorReason.value || 'Processing failed')
        stopPolling()
      }
    }
  } catch (error: unknown) {
    console.error('Failed to check video status:', error)
    // Don't stop polling on error, might be temporary
  } finally {
    isPolling.value = false
  }
}

const startPolling = () => {
  if (!props.autoPoll) return
  
  // Check immediately
  checkStatus()
  
  // Then poll at interval
  pollTimer = setInterval(() => {
    if (status.value !== 'ready' && status.value !== 'failed') {
      checkStatus()
    } else {
      stopPolling()
    }
  }, props.pollInterval)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(() => {
  if (props.autoPoll) {
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})

// Expose methods for parent component
defineExpose({
  checkStatus,
  startPolling,
  stopPolling,
})
</script>
