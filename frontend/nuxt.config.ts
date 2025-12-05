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
      title: 'Short5 Platform',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover' },
        { name: 'description', content: 'Short5 Platform - Short Video Swiper like Tinder experience' },
        // Open Graph / Facebook
        { property: 'og:type', content: 'website' },
        { property: 'og:site_name', content: 'Short5 Platform' },
        { property: 'og:title', content: 'Short5 Platform - Share Amazing Videos' },
        { property: 'og:description', content: 'Short5 Platform - Short Video Swiper like Tinder experience' },
        { property: 'og:image', content: '/og-image.svg' },
        { property: 'og:image:width', content: '1200' },
        { property: 'og:image:height', content: '630' },
        { property: 'og:image:alt', content: 'Short5 Platform 💯' },
        { property: 'og:image:type', content: 'image/svg+xml' },
        // Twitter Card
        { name: 'twitter:card', content: 'summary_large_image' },
        { name: 'twitter:title', content: 'Short5 Platform - Share Amazing Videos' },
        { name: 'twitter:description', content: 'Short5 Platform - Short Video Swiper like Tinder experience' },
        { name: 'twitter:image', content: '/og-image.svg' },
        { name: 'twitter:image:alt', content: 'Short5 Platform 💯' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/icon.svg' },
        { rel: 'apple-touch-icon', href: '/icon.svg' },
        { rel: 'manifest', href: '/manifest.json' },
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

