<template>
  <div class="min-h-screen flex items-center justify-center bg-black px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="flex items-center justify-center mb-4">
          <NuxtLink
            to="/"
            class="text-gray-400 hover:text-white transition-colors flex items-center gap-2"
            :title="t('register.backToFeed')"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span class="text-sm">{{ t('register.backToFeed') }}</span>
          </NuxtLink>
        </div>
        <h1 class="text-4xl font-bold text-white mb-2">{{ t('register.title') }}</h1>
        <p class="text-gray-400">{{ t('register.subtitle') }}</p>
      </div>

      <div class="bg-gray-900 rounded-lg p-8 shadow-xl">
        <form @submit.prevent="handleRegister" class="space-y-6">
          <div>
            <label for="username" class="block text-sm font-medium text-gray-300 mb-2">
              {{ t('register.username') }}
            </label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              required
              minlength="3"
              maxlength="30"
              pattern="[a-zA-Z0-9_]+"
              class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              :placeholder="t('register.usernamePlaceholder')"
              :disabled="loading"
            />
            <p class="mt-1 text-xs text-gray-500">{{ t('register.usernameHint') }}</p>
          </div>

          <div>
            <label for="email" class="block text-sm font-medium text-gray-300 mb-2">
              {{ t('register.email') }}
            </label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              :placeholder="t('register.emailPlaceholder')"
              :disabled="loading"
            />
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-300 mb-2">
              {{ t('register.password') }}
            </label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              required
              minlength="8"
              class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              :placeholder="t('register.passwordPlaceholder')"
              :disabled="loading"
            />
            <p class="mt-1 text-xs text-gray-500">{{ t('register.passwordHint') }}</p>
          </div>

          <div>
            <label for="confirmPassword" class="block text-sm font-medium text-gray-300 mb-2">
              {{ t('register.confirmPassword') }}
            </label>
            <input
              id="confirmPassword"
              v-model="form.confirmPassword"
              type="password"
              required
              minlength="8"
              class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              :placeholder="t('register.confirmPasswordPlaceholder')"
              :disabled="loading"
            />
          </div>

          <div v-if="error" class="bg-red-900/50 border border-red-700 rounded-lg p-3">
            <p class="text-sm text-red-300">{{ error }}</p>
          </div>

          <button
            type="submit"
            :disabled="loading || !isFormValid"
            class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition-colors duration-200"
          >
            <span v-if="loading">{{ t('register.creatingAccount') }}</span>
            <span v-else>{{ t('register.signUp') }}</span>
          </button>
        </form>

        <div class="mt-6 text-center">
          <p class="text-gray-400 text-sm">
            {{ t('register.hasAccount') }}
            <NuxtLink to="/login" class="text-blue-500 hover:text-blue-400 font-medium">
              {{ t('register.signIn') }}
            </NuxtLink>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { useI18n } from '~/composables/useI18n'

definePageMeta({
  layout: false,
  middleware: 'guest', // Only allow non-authenticated users
})

const authStore = useAuthStore()
const { t } = useI18n()

const form = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const loading = ref(false)
const error = ref<string | null>(null)

const isFormValid = computed(() => {
  return (
    form.value.username.length >= 3 &&
    form.value.email.includes('@') &&
    form.value.password.length >= 8 &&
    form.value.password === form.value.confirmPassword
  )
})

const handleRegister = async () => {
  error.value = null

  // Validate password match
  if (form.value.password !== form.value.confirmPassword) {
    error.value = t('register.passwordsNotMatch')
    return
  }

  // Validate username pattern
  if (!/^[a-zA-Z0-9_]+$/.test(form.value.username)) {
    error.value = t('register.usernameInvalid')
    return
  }

  loading.value = true

  try {
    await authStore.register(
      form.value.username,
      form.value.email,
      form.value.password
    )
    // Redirect to feed
    await navigateTo('/')
  } catch (err: any) {
    error.value = err.message || t('register.registrationFailed')
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
