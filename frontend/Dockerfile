FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy application code
COPY . .

# Build arguments for runtime config (can be overridden)
ARG NUXT_PUBLIC_API_BASE_URL
ARG NUXT_PUBLIC_BACKEND_BASE_URL

# Set build-time environment variables (fallback to defaults if not provided)
ENV NUXT_PUBLIC_API_BASE_URL=${NUXT_PUBLIC_API_BASE_URL}
ENV NUXT_PUBLIC_BACKEND_BASE_URL=${NUXT_PUBLIC_BACKEND_BASE_URL}
ENV NODE_ENV=production

# Verify environment variables are set (for debugging)
RUN echo "Building with NUXT_PUBLIC_API_BASE_URL=${NUXT_PUBLIC_API_BASE_URL}"
RUN echo "Building with NUXT_PUBLIC_BACKEND_BASE_URL=${NUXT_PUBLIC_BACKEND_BASE_URL}"

# Build the application
RUN npm run build

# Production image
FROM node:20-alpine

WORKDIR /app

# Copy built application from builder (Nuxt 4 output structure)
COPY --from=builder /app/.output ./.output

# Expose port (Nuxt listens on 3000 by default)
EXPOSE 3000

# Set environment to production
ENV NODE_ENV=production
ENV PORT=3000
ENV HOST=0.0.0.0

# Run the application (Nuxt 4 production server)
CMD ["node", ".output/server/index.mjs"]
