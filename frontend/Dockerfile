FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy application code
COPY . .

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
