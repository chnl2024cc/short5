<template>
  <div class="min-h-screen flex items-center justify-center bg-black px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="flex items-center justify-center mb-4">
          <NuxtLink
            to="/"
            class="text-gray-400 hover:text-white transition-colors flex items-center gap-2"
            :title="t('login.backToFeed')"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span class="text-sm">{{ t('login.backToFeed') }}</span>
          </NuxtLink>
        </div>
        <h1 class="text-4xl font-bold text-white mb-2">{{ t('login.title') }}</h1>
        <p class="text-gray-400">{{ t('login.subtitle') }}</p>
      </div>

      <div class="bg-gray-900 rounded-lg p-8 shadow-xl">
        <form @submit.prevent="handleLogin" class="space-y-6">
          <div>
            <label for="email" class="block text-sm font-medium text-gray-300 mb-2">
              {{ t('login.email') }}
            </label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              :placeholder="t('login.emailPlaceholder')"
              :disabled="loading"
            />
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-300 mb-2">
              {{ t('login.password') }}
            </label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              required
              minlength="8"
              class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              :placeholder="t('login.passwordPlaceholder')"
              :disabled="loading"
            />
          </div>

          <div v-if="error" class="bg-red-900/50 border border-red-700 rounded-lg p-3">
            <p class="text-sm text-red-300">{{ error }}</p>
          </div>

          <button
            type="submit"
            :disabled="loading || !form.email || !form.password"
            class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition-colors duration-200"
          >
            <span v-if="loading">{{ t('login.signingIn') }}</span>
            <span v-else>{{ t('login.signIn') }}</span>
          </button>
        </form>

        <div class="mt-6 text-center">
          <p class="text-gray-400 text-sm">
            {{ t('login.noAccount') }}
            <NuxtLink to="/register" class="text-blue-500 hover:text-blue-400 font-medium">
              {{ t('login.signUp') }}
            </NuxtLink>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { useI18n } from '~/composables/useI18n'

definePageMeta({
  layout: false,
  middleware: 'guest', // Only allow non-authenticated users
})

const authStore = useAuthStore()
const { t } = useI18n()

const form = ref({
  email: '',
  password: '',
})

const loading = ref(false)
const error = ref<string | null>(null)

const handleLogin = async () => {
  error.value = null
  loading.value = true

  try {
    await authStore.login(form.value.email, form.value.password)
    // Redirect to feed
    await navigateTo('/')
  } catch (err: any) {
    error.value = err.message || t('login.invalidCredentials')
  } finally {
    loading.value = false
  }
}

// Redirect if already authenticated
onMounted(() => {
  if (authStore.isAuthenticated) {
    navigateTo('/')
  }
})
</script>
