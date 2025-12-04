<template>
  <div class="min-h-screen bg-black text-white py-8 px-4">
    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold mb-2">{{ t('uploadBulk.title') }}</h1>
        <p class="text-gray-400">{{ t('uploadBulk.subtitle') }}</p>
      </div>

      <!-- Upload Form -->
      <div class="bg-gray-900 rounded-lg p-6 space-y-6">
        <!-- File Upload Area -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">
            {{ t('uploadBulk.videoFiles') }}
          </label>
          
          <!-- Drag & Drop Zone -->
          <div
            ref="dropZone"
            :class="[
              'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
              isDragging ? 'border-blue-500 bg-blue-500/10' : 'border-gray-700 hover:border-gray-600',
              selectedFiles.length > 0 ? 'border-green-500 bg-green-500/10' : ''
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
              multiple
              class="hidden"
              @change="handleFileSelect"
            />
            
            <div v-if="selectedFiles.length === 0" class="space-y-4">
              <div class="text-4xl">📹</div>
              <div>
                <p class="text-lg font-medium mb-1">
                  {{ t('uploadBulk.dropVideos') }}
                </p>
                <p class="text-sm text-gray-400">
                  {{ t('uploadBulk.supportedFormats') }}
                </p>
                <p class="text-sm text-gray-500 mt-2">
                  {{ t('uploadBulk.selectMultiple') }}
                </p>
              </div>
            </div>
            
            <div v-else class="space-y-4">
              <div class="text-4xl">✅</div>
              <div>
                <p class="text-lg font-medium mb-1">
                  {{ selectedFiles.length }} {{ t('uploadBulk.filesSelected') }}
                </p>
                <p class="text-sm text-gray-400">
                  {{ t('uploadBulk.totalSize') }}: {{ formatFileSize(totalSize) }}
                </p>
              </div>
              <button
                type="button"
                @click.stop="clearFiles"
                class="text-sm text-red-400 hover:text-red-300"
              >
                {{ t('uploadBulk.clearAllFiles') }}
              </button>
            </div>
          </div>
          
          <div v-if="fileError" class="mt-2 text-sm text-red-400">
            {{ fileError }}
          </div>
        </div>

        <!-- Selected Files List -->
        <div v-if="selectedFiles.length > 0" class="space-y-3">
          <label class="block text-sm font-medium text-gray-300">
            {{ t('uploadBulk.selectedFiles') }} ({{ selectedFiles.length }})
          </label>
          <div class="space-y-2 max-h-64 overflow-y-auto">
            <div
              v-for="(file, index) in selectedFiles"
              :key="index"
              class="flex items-center justify-between bg-gray-800 rounded-lg p-3"
            >
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-white truncate">{{ file.name }}</p>
                <p class="text-xs text-gray-400">{{ formatFileSize(file.size) }}</p>
              </div>
              <button
                type="button"
                @click="removeFile(index)"
                class="ml-4 text-red-400 hover:text-red-300 text-sm"
                :disabled="uploading"
              >
                {{ t('uploadBulk.remove') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Global Title/Description (applied to all videos) -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label for="global-title" class="block text-sm font-medium text-gray-300 mb-2">
              {{ t('uploadBulk.titlePrefix') }}
            </label>
            <input
              id="global-title"
              v-model="globalTitle"
              type="text"
              maxlength="255"
              class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              :placeholder="t('uploadBulk.titlePrefixPlaceholder')"
              :disabled="uploading"
            />
            <p class="mt-1 text-xs text-gray-500">
              {{ t('uploadBulk.titlePrefixHint') }}
            </p>
          </div>

          <div>
            <label for="global-description" class="block text-sm font-medium text-gray-300 mb-2">
              {{ t('uploadBulk.description') }}
            </label>
            <textarea
              id="global-description"
              v-model="globalDescription"
              rows="3"
              maxlength="1000"
              class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              :placeholder="t('uploadBulk.descriptionPlaceholder')"
              :disabled="uploading"
            />
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="bg-red-900/50 border border-red-700 rounded-lg p-3">
          <p class="text-sm text-red-300">{{ error }}</p>
        </div>

        <!-- Success Message -->
        <div v-if="success && !uploading" class="bg-green-900/50 border border-green-700 rounded-lg p-3">
          <p class="text-sm text-green-300">{{ success }}</p>
        </div>

        <!-- Upload Progress Overview -->
        <div v-if="uploading" class="space-y-4">
          <div class="flex justify-between text-sm text-gray-400">
            <span>{{ t('uploadBulk.uploadingVideos') }}</span>
            <span>{{ completedUploads }} / {{ selectedFiles.length }}</span>
          </div>
          <div class="w-full bg-gray-800 rounded-full h-2">
            <div
              class="bg-blue-600 h-2 rounded-full transition-all duration-300"
              :style="{ width: `${(completedUploads / selectedFiles.length) * 100}%` }"
            />
          </div>

          <!-- Individual File Upload Status -->
          <div class="space-y-2 max-h-64 overflow-y-auto">
            <div
              v-for="(status, index) in uploadStatuses"
              :key="index"
              class="bg-gray-800 rounded-lg p-3"
            >
              <div class="flex items-center justify-between mb-2">
                <p class="text-sm font-medium text-white truncate flex-1">
                  {{ status.filename }}
                </p>
                <span
                  :class="[
                    'text-xs px-2 py-1 rounded',
                    status.status === 'completed' ? 'bg-green-900/50 text-green-300' :
                    status.status === 'uploading' ? 'bg-blue-900/50 text-blue-300' :
                    status.status === 'error' ? 'bg-red-900/50 text-red-300' :
                    'bg-gray-700 text-gray-400'
                  ]"
                >
                  {{ status.status === 'completed' ? t('uploadBulk.done') :
                      status.status === 'uploading' ? t('uploadBulk.uploadingStatus') :
                      status.status === 'error' ? t('uploadBulk.failed') :
                      t('uploadBulk.pending') }}
                </span>
              </div>
              <div v-if="status.status === 'uploading'" class="w-full bg-gray-700 rounded-full h-1.5 mt-2">
                <div
                  class="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                  :style="{ width: `${status.progress}%` }"
                />
              </div>
              <p v-if="status.error" class="text-xs text-red-400 mt-1">{{ status.error }}</p>
              <p v-if="status.videoId" class="text-xs text-gray-500 mt-1">
                Video ID: {{ status.videoId }}
              </p>
            </div>
          </div>
        </div>

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
            :disabled="selectedFiles.length === 0 || uploading"
            class="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
          >
            <span v-if="uploading">
              Uploading... ({{ completedUploads }}/{{ selectedFiles.length }})
            </span>
            <span v-else>
              Upload {{ selectedFiles.length }} Video{{ selectedFiles.length !== 1 ? 's' : '' }}
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useVideosStore } from '~/stores/videos'
import { useAuthStore } from '~/stores/auth'
import { useI18n } from '~/composables/useI18n'

definePageMeta({
  middleware: 'auth',
})

const videosStore = useVideosStore()
const authStore = useAuthStore()
const { t } = useI18n()

// Ensure auth store is initialized
onMounted(() => {
  if (process.client) {
    authStore.initFromStorage()
    
    // Double-check authentication after initialization
    if (!authStore.isAuthenticated) {
      console.warn('User not authenticated on bulk upload page, redirecting to login')
      navigateTo('/login')
      return
    }
    
    // Verify token exists
    const token = authStore.token || localStorage.getItem('token')
    if (!token) {
      console.error('No authentication token found, redirecting to login')
      navigateTo('/login')
      return
    }
  }
})

const fileInput = ref<HTMLInputElement | null>(null)
const dropZone = ref<HTMLElement | null>(null)
const selectedFiles = ref<File[]>([])
const isDragging = ref(false)

const globalTitle = ref('')
const globalDescription = ref('')

const uploading = ref(false)
const error = ref<string | null>(null)
const fileError = ref<string | null>(null)
const success = ref<string | null>(null)
const completedUploads = ref(0)

interface UploadStatus {
  filename: string
  status: 'pending' | 'uploading' | 'completed' | 'error'
  progress: number
  error?: string
  videoId?: string
}

const uploadStatuses = ref<UploadStatus[]>([])

// File size limit: 500MB
const MAX_FILE_SIZE = 500 * 1024 * 1024
const ALLOWED_FORMATS = ['.mp4', '.mov', '.avi']

const totalSize = computed(() => {
  return selectedFiles.value.reduce((sum, file) => sum + file.size, 0)
})

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
  const files = target.files
  if (files && files.length > 0) {
    processFiles(Array.from(files))
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
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    processFiles(Array.from(files))
  }
}

const processFiles = (files: File[]) => {
  error.value = null
  fileError.value = null
  success.value = null
  
  const validFiles: File[] = []
  const errors: string[] = []
  
  for (const file of files) {
    const validationError = validateFile(file)
    if (validationError) {
      errors.push(`${file.name}: ${validationError}`)
    } else {
      // Check if file is already in the list (by name and size)
      const isDuplicate = selectedFiles.value.some(
        f => f.name === file.name && f.size === file.size
      )
      if (!isDuplicate) {
        validFiles.push(file)
      }
    }
  }
  
  if (errors.length > 0) {
    fileError.value = errors.join('; ')
  }
  
  if (validFiles.length > 0) {
    selectedFiles.value.push(...validFiles)
  }
}

const removeFile = (index: number) => {
  selectedFiles.value.splice(index, 1)
  // Also remove from upload statuses if exists
  if (uploadStatuses.value[index]) {
    uploadStatuses.value.splice(index, 1)
  }
}

const clearFiles = () => {
  selectedFiles.value = []
  uploadStatuses.value = []
  completedUploads.value = 0
  error.value = null
  fileError.value = null
  success.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const handleUpload = async () => {
  if (selectedFiles.value.length === 0) return
  
  error.value = null
  success.value = null
  
  // Check if user is authenticated
  if (!authStore.isAuthenticated) {
    error.value = t('uploadBulk.mustBeLoggedIn')
    return
  }
  
  // Verify token exists
  const token = authStore.token || (process.client ? localStorage.getItem('token') : null)
  if (!token) {
    error.value = t('uploadBulk.authTokenNotFound')
    navigateTo('/login')
    return
  }
  
  uploading.value = true
  completedUploads.value = 0
  
  // Initialize upload statuses
  uploadStatuses.value = selectedFiles.value.map(file => ({
    filename: file.name,
    status: 'pending' as const,
    progress: 0,
  }))
  
  const uploadResults: Array<{ success: boolean; videoId?: string; error?: string }> = []
  
  // Upload files sequentially to avoid overwhelming the server
  for (let i = 0; i < selectedFiles.value.length; i++) {
    const file = selectedFiles.value[i]
    const status = uploadStatuses.value[i]
    
    // Generate title for this video
    const filenameWithoutExt = file.name.replace(/\.[^/.]+$/, '')
    const title = globalTitle.value
      ? `${globalTitle.value} - ${filenameWithoutExt}`
      : filenameWithoutExt
    
    status.status = 'uploading'
    status.progress = 0
    
    // Simulate progress (since we can't track actual progress with fetch)
    const progressInterval = setInterval(() => {
      if (status.progress < 90 && status.status === 'uploading') {
        status.progress += 10
      }
    }, 200)
    
    try {
      const uploadResponse = (await videosStore.uploadVideo(
        file,
        title || undefined,
        globalDescription.value || undefined
      )) as { video_id: string; status: string; message?: string }
      
      clearInterval(progressInterval)
      status.progress = 100
      status.status = 'completed'
      status.videoId = uploadResponse?.video_id || ''
      
      uploadResults.push({ success: true, videoId: status.videoId })
      completedUploads.value++
    } catch (err: any) {
      clearInterval(progressInterval)
      status.status = 'error'
      status.error = err.message || 'Upload failed'
      status.progress = 0
      
      uploadResults.push({ success: false, error: status.error })
      completedUploads.value++
    }
  }
  
  uploading.value = false
  
  // Show summary
  const successCount = uploadResults.filter(r => r.success).length
  const failCount = uploadResults.filter(r => !r.success).length
  
  if (successCount > 0 && failCount === 0) {
    success.value = t('uploadBulk.successAll').replace('{count}', String(successCount))
  } else if (successCount > 0) {
    success.value = t('uploadBulk.successPartial').replace('{success}', String(successCount)).replace('{failed}', String(failCount))
  } else {
    error.value = t('uploadBulk.failedAll')
  }
  
  // Redirect to profile page after 5 seconds if all succeeded
  if (successCount === selectedFiles.value.length) {
    setTimeout(() => {
      navigateTo('/profile')
    }, 5000)
  }
}

const handleCancel = () => {
  if (uploading.value) return
  
  clearFiles()
  globalTitle.value = ''
  globalDescription.value = ''
  navigateTo('/')
}

// Cleanup on unmount
onUnmounted(() => {
  // No preview URLs to clean up in bulk upload
})
</script>
