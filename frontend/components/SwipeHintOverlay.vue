<template>
  <Transition name="fade">
    <div
      v-if="show"
      class="swipe-hint-overlay"
    >
      <div class="swipe-hint-container">
        <!-- Center Main Message -->
        <div class="swipe-hint-center">
          <div class="swipe-hint-main-text">Swipe to navigate</div>
          <div class="swipe-hint-arrows">
            <div class="swipe-hint-arrow swipe-hint-arrow-left">
              <svg class="arrow-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" />
              </svg>
              <span class="arrow-label">Pass</span>
            </div>
            <div class="swipe-hint-arrow swipe-hint-arrow-right">
              <span class="arrow-label">Like</span>
              <svg class="arrow-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>
        </div>
        
        <!-- Action Cards -->
        <div class="swipe-hint-actions">
          <!-- Left Action Card -->
          <div class="swipe-hint-card swipe-hint-card-left">
            <div class="card-icon-wrapper">
              <svg class="card-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div class="card-text">Swipe Left</div>
          </div>
          
          <!-- Right Action Card -->
          <div class="swipe-hint-card swipe-hint-card-right">
            <div class="card-icon-wrapper">
              <svg class="card-icon" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
              </svg>
            </div>
            <div class="card-text">Swipe Right</div>
          </div>
        </div>
        
        <!-- Dismiss Button -->
        <button
          @click.stop="handleDismiss"
          class="swipe-hint-dismiss"
          aria-label="Dismiss hint"
        >
          <svg class="dismiss-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  dismiss: []
}>()

const handleDismiss = () => {
  emit('dismiss')
}
</script>

<style scoped>
.swipe-hint-overlay {
  position: absolute;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  pointer-events: none; /* Allow touches to pass through to swiper */
}

.swipe-hint-container {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 2rem 1.5rem;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.85) 0%, rgba(20, 20, 30, 0.9) 100%);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-radius: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05) inset;
  animation: fadeInScale 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  pointer-events: auto;
  max-width: 100%;
  width: 100%;
}

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.85) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Center Section */
.swipe-hint-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  width: 100%;
}

.swipe-hint-main-text {
  color: white;
  font-size: 1.125rem;
  font-weight: 600;
  text-align: center;
  letter-spacing: 0.02em;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.swipe-hint-arrows {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  width: 100%;
}

.swipe-hint-arrow {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  max-width: 120px;
}

.swipe-hint-arrow-left {
  animation: slideLeft 2s ease-in-out infinite;
}

.swipe-hint-arrow-right {
  animation: slideRight 2s ease-in-out infinite;
}

@keyframes slideLeft {
  0%, 100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(-8px);
  }
}

@keyframes slideRight {
  0%, 100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(8px);
  }
}

.arrow-icon {
  width: 2rem;
  height: 2rem;
  color: rgba(255, 255, 255, 0.7);
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.arrow-label {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.875rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Action Cards */
.swipe-hint-actions {
  display: flex;
  gap: 1rem;
  width: 100%;
  justify-content: center;
}

.swipe-hint-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 1.25rem 1rem;
  border-radius: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  animation: cardPulse 2.5s ease-in-out infinite;
  max-width: 140px;
}

.swipe-hint-card-left {
  animation-delay: 0s;
}

.swipe-hint-card-left:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.3);
  transform: scale(1.05);
}

.swipe-hint-card-right {
  animation-delay: 0.3s;
}

.swipe-hint-card-right:hover {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.3);
  transform: scale(1.05);
}

@keyframes cardPulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.03);
    opacity: 0.9;
  }
}

.card-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.swipe-hint-card-left .card-icon-wrapper {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.15) 100%);
}

.swipe-hint-card-right .card-icon-wrapper {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.15) 100%);
}

.card-icon {
  width: 2rem;
  height: 2rem;
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.3));
}

.swipe-hint-card-left .card-icon {
  color: #f87171; /* Lighter red */
}

.swipe-hint-card-right .card-icon {
  color: #60a5fa; /* Lighter blue */
}

.card-text {
  color: white;
  font-size: 0.875rem;
  font-weight: 600;
  text-align: center;
  letter-spacing: 0.03em;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

/* Dismiss Button */
.swipe-hint-dismiss {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  width: 2.75rem;
  height: 2.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  transition: all 0.2s ease;
  pointer-events: auto;
  backdrop-filter: blur(10px);
}

.swipe-hint-dismiss:active {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(0.95);
}

.dismiss-icon {
  width: 1.25rem;
  height: 1.25rem;
}

/* Mobile Optimizations */
@media (max-width: 480px) {
  .swipe-hint-overlay {
    padding: 1rem;
  }

  .swipe-hint-container {
    padding: 1.75rem 1.25rem;
    gap: 1.25rem;
    border-radius: 1.5rem;
  }

  .swipe-hint-main-text {
    font-size: 1rem;
  }

  .swipe-hint-arrows {
    gap: 1.5rem;
  }

  .arrow-icon {
    width: 1.75rem;
    height: 1.75rem;
  }

  .arrow-label {
    font-size: 0.8125rem;
  }

  .swipe-hint-actions {
    gap: 0.75rem;
  }

  .swipe-hint-card {
    padding: 1rem 0.75rem;
    gap: 0.625rem;
    max-width: 120px;
  }

  .card-icon-wrapper {
    width: 3rem;
    height: 3rem;
  }

  .card-icon {
    width: 1.75rem;
    height: 1.75rem;
  }

  .card-text {
    font-size: 0.8125rem;
  }

  .swipe-hint-dismiss {
    width: 2.5rem;
    height: 2.5rem;
    top: 0.625rem;
    right: 0.625rem;
  }

  .dismiss-icon {
    width: 1.125rem;
    height: 1.125rem;
  }
}

/* Very small screens */
@media (max-width: 360px) {
  .swipe-hint-container {
    padding: 1.5rem 1rem;
  }

  .swipe-hint-card {
    max-width: 100px;
    padding: 0.875rem 0.5rem;
  }

  .card-icon-wrapper {
    width: 2.5rem;
    height: 2.5rem;
  }

  .card-icon {
    width: 1.5rem;
    height: 1.5rem;
  }
}

/* Transition animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease, transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(10px);
}
</style>
