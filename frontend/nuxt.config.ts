// https://nuxt.com/docs/api/configuration/nuxt-config
const isProduction = process.env.NODE_ENV === 'production'

export default defineNuxtConfig({
  compatibilityDate: '2024-04-03',
  devtools: { enabled: !isProduction },
  
  modules: [
    '@nuxt/ui',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    // Only load devtools in development - completely exclude in production
    ...(!isProduction ? ['@nuxt/devtools'] : []),
  ],

  css: ['~/assets/css/main.css'],

  postcss: {
    plugins: {
      '@tailwindcss/postcss': {},
      autoprefixer: {},
    },
  },

  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL,
      backendBaseUrl: process.env.NUXT_PUBLIC_BACKEND_BASE_URL,
    },
  },

  app: {
    head: {
      title: 'Short-Video Platform',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Short-Video Platform - TikTok-like experience' },
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
      ],
    },
  },

  typescript: {
    strict: true,
    // Disable type checking during build to avoid blocking on type errors
    // Type checking should be done in CI/CD or locally, not during Docker builds
    typeCheck: false,
  },

  vite: {
    build: {
      sourcemap: !isProduction,
    },
    // Explicitly disable devtools-related plugins in production
    ...(isProduction && {
      server: {
        hmr: false,
      },
    }),
  },
})

