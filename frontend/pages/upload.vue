<template>
  <div class="min-h-screen bg-black text-white py-8 px-4">
    <div class="max-w-2xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold mb-2">Upload Video</h1>
        <p class="text-gray-400">Share your video with the community</p>
      </div>

      <!-- Upload Form -->
      <div class="bg-gray-900 rounded-lg p-6 space-y-6">
        <!-- File Upload Area -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">
            Video File
          </label>
          
          <!-- Drag & Drop Zone -->
          <div
            ref="dropZone"
            :class="[
              'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
              isDragging ? 'border-blue-500 bg-blue-500/10' : 'border-gray-700 hover:border-gray-600',
              selectedFile ? 'border-green-500 bg-green-500/10' : ''
            ]"
            @dragover.prevent="handleDragOver"
            @dragleave.prevent="handleDragLeave"
            @drop.prevent="handleDrop"
            @click="fileInput?.click()"
          >
            <input
              ref="fileInput"
              type="file"
              accept="video/*"
              class="hidden"
              @change="handleFileSelect"
            />
            
            <div v-if="!selectedFile" class="space-y-4">
              <div class="text-4xl">📹</div>
              <div>
                <p class="text-lg font-medium mb-1">
                  Drop your video here or click to browse
                </p>
                <p class="text-sm text-gray-400">
                  Supported formats: MP4, MOV, AVI (Max 500MB)
                </p>
              </div>
            </div>
            
            <div v-else class="space-y-4">
              <div class="text-4xl">✅</div>
              <div>
                <p class="text-lg font-medium mb-1">{{ selectedFile.name }}</p>
                <p class="text-sm text-gray-400">
                  {{ formatFileSize(selectedFile.size) }}
                </p>
              </div>
              <button
                type="button"
                @click.stop="clearFile"
                class="text-sm text-red-400 hover:text-red-300"
              >
                Remove file
              </button>
            </div>
          </div>
          
          <div v-if="fileError" class="mt-2 text-sm text-red-400">
            {{ fileError }}
          </div>
        </div>

        <!-- Video Preview -->
        <div v-if="selectedFile && videoPreviewUrl" class="space-y-2">
          <label class="block text-sm font-medium text-gray-300">Preview</label>
          <video
            :src="videoPreviewUrl"
            controls
            class="w-full rounded-lg bg-black"
            style="max-height: 400px;"
          />
        </div>

        <!-- Title Input -->
        <div>
          <label for="title" class="block text-sm font-medium text-gray-300 mb-2">
            Title (optional)
          </label>
          <input
            id="title"
            v-model="form.title"
            type="text"
            maxlength="255"
            class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Give your video a title..."
            :disabled="uploading"
          />
        </div>

        <!-- Description Input -->
        <div>
          <label for="description" class="block text-sm font-medium text-gray-300 mb-2">
            Description (optional)
          </label>
          <textarea
            id="description"
            v-model="form.description"
            rows="4"
            maxlength="1000"
            class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            placeholder="Describe your video..."
            :disabled="uploading"
          />
          <p class="mt-1 text-xs text-gray-500">
            {{ form.description?.length || 0 }} / 1000 characters
          </p>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="bg-red-900/50 border border-red-700 rounded-lg p-3">
          <p class="text-sm text-red-300">{{ error }}</p>
        </div>

        <!-- Success Message -->
        <div v-if="success && !uploadedVideoId" class="bg-green-900/50 border border-green-700 rounded-lg p-3">
          <p class="text-sm text-green-300">{{ success }}</p>
        </div>

        <!-- Upload Progress -->
        <div v-if="uploading && !uploadedVideoId" class="space-y-2">
          <div class="flex justify-between text-sm text-gray-400">
            <span>Uploading...</span>
            <span>{{ uploadProgress }}%</span>
          </div>
          <div class="w-full bg-gray-800 rounded-full h-2">
            <div
              class="bg-blue-600 h-2 rounded-full transition-all duration-300"
              :style="{ width: `${uploadProgress}%` }"
            />
          </div>
        </div>

        <!-- Video Processing Status -->
        <VideoProcessingStatus
          v-if="uploadedVideoId"
          :video-id="uploadedVideoId"
          :auto-poll="true"
          @ready="handleVideoReady"
          @failed="handleVideoFailed"
        />

        <!-- Submit Button -->
        <div class="flex gap-4">
          <button
            type="button"
            @click="handleCancel"
            class="flex-1 px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white font-semibold rounded-lg transition-colors"
            :disabled="uploading"
          >
            Cancel
          </button>
          <button
            type="button"
            @click="handleUpload"
            :disabled="!selectedFile || uploading"
            class="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
          >
            <span v-if="uploading">Uploading...</span>
            <span v-else>Upload Video</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useVideosStore } from '~/stores/videos'
import { useAuthStore } from '~/stores/auth'

definePageMeta({
  middleware: 'auth',
})

const videosStore = useVideosStore()
const authStore = useAuthStore()

// Ensure auth store is initialized
onMounted(() => {
  if (process.client) {
    authStore.initFromStorage()
  }
})

const fileInput = ref<HTMLInputElement | null>(null)
const dropZone = ref<HTMLElement | null>(null)
const selectedFile = ref<File | null>(null)
const videoPreviewUrl = ref<string | null>(null)
const isDragging = ref(false)

const form = ref({
  title: '',
  description: '',
})

const uploading = ref(false)
const uploadProgress = ref(0)
const error = ref<string | null>(null)
const fileError = ref<string | null>(null)
const success = ref<string | null>(null)
const uploadedVideoId = ref<string | null>(null)

// File size limit: 500MB
const MAX_FILE_SIZE = 500 * 1024 * 1024
const ALLOWED_FORMATS = ['.mp4', '.mov', '.avi']

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const validateFile = (file: File): string | null => {
  // Check file type
  const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
  if (!ALLOWED_FORMATS.includes(fileExt)) {
    return `Invalid file format. Allowed: ${ALLOWED_FORMATS.join(', ')}`
  }
  
  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    return `File too large. Maximum size: ${formatFileSize(MAX_FILE_SIZE)}`
  }
  
  return null
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    processFile(file)
  }
}

const handleDragOver = (event: DragEvent) => {
  isDragging.value = true
  event.preventDefault()
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  const file = event.dataTransfer?.files[0]
  if (file) {
    processFile(file)
  }
}

const processFile = (file: File) => {
  error.value = null
  fileError.value = null
  success.value = null
  
  const validationError = validateFile(file)
  if (validationError) {
    fileError.value = validationError
    return
  }
  
  selectedFile.value = file
  
  // Create preview URL
  if (videoPreviewUrl.value) {
    URL.revokeObjectURL(videoPreviewUrl.value)
  }
  videoPreviewUrl.value = URL.createObjectURL(file)
}

const clearFile = () => {
  selectedFile.value = null
  if (videoPreviewUrl.value) {
    URL.revokeObjectURL(videoPreviewUrl.value)
    videoPreviewUrl.value = null
  }
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  error.value = null
  fileError.value = null
}

const handleUpload = async () => {
  if (!selectedFile.value) return
  
  error.value = null
  success.value = null
  
  // Check if user is authenticated
  if (!authStore.isAuthenticated) {
    error.value = 'You must be logged in to upload videos. Please log in and try again.'
    return
  }
  
  // Verify token exists
  const token = authStore.token || (process.client ? localStorage.getItem('token') : null)
  if (!token) {
    error.value = 'Authentication token not found. Please log in again.'
    navigateTo('/login')
    return
  }
  
  uploading.value = true
  uploadProgress.value = 0
  
  let progressInterval: NodeJS.Timeout | null = null
  
  try {
    // Simulate upload progress (since we can't track actual progress with fetch)
    progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)
    
    const uploadResponse = (await videosStore.uploadVideo(
      selectedFile.value,
      form.value.title || undefined,
      form.value.description || undefined
    )) as { video_id: string; status: string; message?: string }
    
    if (progressInterval) {
      clearInterval(progressInterval)
    }
    uploadProgress.value = 100
    
    // Store the uploaded video ID for status monitoring
    uploadedVideoId.value = uploadResponse?.video_id || ''
    success.value = 'Video uploaded successfully! Processing has started.'
    uploading.value = false
  } catch (err: any) {
    if (progressInterval) {
      clearInterval(progressInterval)
    }
    error.value = err.message || 'Upload failed. Please try again.'
    uploading.value = false
    uploadProgress.value = 0
  }
}

const handleVideoReady = (videoData: any) => {
  success.value = 'Video processing completed! Your video is now ready.'
  
  // Redirect to profile page after 3 seconds to see the uploaded video
  setTimeout(() => {
    navigateTo('/profile')
  }, 3000)
}

const handleVideoFailed = (errorMessage: string) => {
  error.value = `Video processing failed: ${errorMessage}`
  uploadedVideoId.value = null
}

const handleCancel = () => {
  if (uploading.value) return
  
  clearFile()
  form.value = { title: '', description: '' }
  uploadedVideoId.value = null
  navigateTo('/')
}

// Cleanup preview URL on unmount
onUnmounted(() => {
  if (videoPreviewUrl.value) {
    URL.revokeObjectURL(videoPreviewUrl.value)
  }
})
</script>
