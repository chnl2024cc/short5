# ============================================
# Stage 1: Dependencies
# ============================================
FROM node:20-alpine AS deps

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

WORKDIR /app

# Copy package files for dependency installation
COPY package.json package-lock.json* ./

# Install all dependencies (including devDependencies needed for build)
# Note: devDependencies are needed for TypeScript compilation and build tools
RUN npm ci --prefer-offline --no-audit && \
    npm cache clean --force

# ============================================
# Stage 2: Builder
# ============================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Build arguments - only variables from external sources (.env or PaaS)
ARG NUXT_PUBLIC_API_BASE_URL
ARG NUXT_PUBLIC_BACKEND_BASE_URL
ARG NODE_ENV=production

# Set environment variables for build (convert ARGs to ENV so Nuxt can access them)
ENV NUXT_PUBLIC_API_BASE_URL=${NUXT_PUBLIC_API_BASE_URL}
ENV NUXT_PUBLIC_BACKEND_BASE_URL=${NUXT_PUBLIC_BACKEND_BASE_URL}
ENV NODE_ENV=${NODE_ENV}
ENV NUXT_TELEMETRY_DISABLED=1
ENV NUXT_DEVTOOLS_ENABLED=false

# Build the application
RUN npm run build

# ============================================
# Stage 3: Production Runtime
# ============================================
FROM node:20-alpine AS runner

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nuxt -u 1001

WORKDIR /app

# Copy built application from builder
COPY --from=builder --chown=nuxt:nodejs /app/.output ./.output

# Copy package files for potential runtime dependencies
COPY --from=builder --chown=nuxt:nodejs /app/package.json ./package.json

# Switch to non-root user
USER nuxt

# Expose the application port
EXPOSE 3000

# Set runtime environment variables (NODE_ENV should be set via docker-compose for flexibility)
ENV HOST=0.0.0.0
ENV PORT=3000
ENV NUXT_TELEMETRY_DISABLED=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start the application
CMD ["node", ".output/server/index.mjs"]
