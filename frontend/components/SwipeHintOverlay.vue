<template>
  <Transition name="fade">
    <div
      v-if="show"
      class="swipe-hint-overlay"
      @click="handleDismiss"
    >
      <div class="swipe-hint-container">
        <!-- Left Swipe Hint -->
        <div class="swipe-hint-left">
          <div class="swipe-hint-icon">
            <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <div class="swipe-hint-text">Swipe Left</div>
          <div class="swipe-hint-label">Not Like</div>
        </div>
        
        <!-- Center Instructions -->
        <div class="swipe-hint-center">
          <div class="swipe-hint-arrow-left">←</div>
          <div class="swipe-hint-main-text">Swipe to navigate</div>
          <div class="swipe-hint-arrow-right">→</div>
        </div>
        
        <!-- Right Swipe Hint -->
        <div class="swipe-hint-right">
          <div class="swipe-hint-icon">
            <svg class="w-12 h-12" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
            </svg>
          </div>
          <div class="swipe-hint-text">Swipe Right</div>
          <div class="swipe-hint-label">Like</div>
        </div>
        
        <!-- Dismiss Button -->
        <button
          @click.stop="handleDismiss"
          class="swipe-hint-dismiss"
          aria-label="Dismiss hint"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
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
}

.swipe-hint-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3rem;
  padding: 2rem;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(10px);
  border-radius: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  animation: fadeInScale 0.4s ease-out;
  pointer-events: auto;
  max-width: 90%;
}

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.swipe-hint-left,
.swipe-hint-right {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  animation: pulse 2s ease-in-out infinite;
}

.swipe-hint-left {
  animation-delay: 0s;
}

.swipe-hint-right {
  animation-delay: 0.5s;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
}

.swipe-hint-icon {
  color: white;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.3));
}

.swipe-hint-left .swipe-hint-icon {
  color: #ef4444; /* Red for not like */
}

.swipe-hint-right .swipe-hint-icon {
  color: #3b82f6; /* Blue for like */
}

.swipe-hint-text {
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.swipe-hint-label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.swipe-hint-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  min-width: 200px;
}

.swipe-hint-arrow-left,
.swipe-hint-arrow-right {
  font-size: 2rem;
  color: rgba(255, 255, 255, 0.6);
  animation: slideHorizontal 1.5s ease-in-out infinite;
}

.swipe-hint-arrow-left {
  animation-name: slideLeft;
}

.swipe-hint-arrow-right {
  animation-name: slideRight;
}

@keyframes slideLeft {
  0%, 100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(-10px);
  }
}

@keyframes slideRight {
  0%, 100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(10px);
  }
}

.swipe-hint-main-text {
  color: white;
  font-size: 1rem;
  font-weight: 500;
  text-align: center;
}

.swipe-hint-dismiss {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  pointer-events: auto;
}

.swipe-hint-dismiss:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}

/* Responsive design for mobile */
@media (max-width: 768px) {
  .swipe-hint-container {
    flex-direction: column;
    gap: 1.5rem;
    padding: 1.5rem;
    max-width: 95%;
  }
  
  .swipe-hint-center {
    order: -1;
    min-width: auto;
  }
  
  .swipe-hint-left,
  .swipe-hint-right {
    flex-direction: row;
    gap: 1rem;
  }
  
  .swipe-hint-icon {
    width: 2rem;
    height: 2rem;
  }
  
  .swipe-hint-arrow-left,
  .swipe-hint-arrow-right {
    font-size: 1.5rem;
  }
}

/* Transition animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
