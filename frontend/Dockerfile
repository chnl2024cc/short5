FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci && npm cache clean --force

COPY . .

ARG NUXT_PUBLIC_API_BASE_URL
ARG NUXT_PUBLIC_BACKEND_BASE_URL

ENV NUXT_PUBLIC_API_BASE_URL=${NUXT_PUBLIC_API_BASE_URL}
ENV NUXT_PUBLIC_BACKEND_BASE_URL=${NUXT_PUBLIC_BACKEND_BASE_URL}
ENV NODE_ENV=production

RUN npm run build

FROM node:20-alpine

RUN addgroup -g 1001 -S nodejs && \
    adduser -S nuxt -u 1001

WORKDIR /app

COPY --from=builder --chown=nuxt:nodejs /app/.output ./.output

USER nuxt

EXPOSE 3000

ENV NODE_ENV=production
ENV HOST=0.0.0.0

CMD ["node", ".output/server/index.mjs"]
