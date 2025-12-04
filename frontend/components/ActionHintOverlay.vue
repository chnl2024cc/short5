<template>
  <Transition name="fade">
    <div
      v-if="show"
      class="action-hint-overlay"
    >
      <div class="action-hint-container">
        <!-- Center Main Message -->
        <div class="action-hint-center">
          <div class="action-hint-main-text">{{ t('actionHint.tryTheseActions') }}</div>
        </div>
        
        <!-- Action Cards with Jumping Arrows -->
        <div class="action-hint-actions">
          <!-- Left Action Card (Not Like) -->
          <div class="action-hint-card action-hint-card-left">
            <div class="card-icon-wrapper">
              <svg class="card-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div class="card-text">{{ t('actionHint.swipeLeft') }}</div>
            <div class="jumping-arrow jumping-arrow-left">
              <svg class="arrow-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" />
              </svg>
            </div>
          </div>
          
          <!-- Center Action Card (Share) -->
          <div class="action-hint-card action-hint-card-center">
            <div class="card-icon-wrapper">
              <svg class="card-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
              </svg>
            </div>
            <div class="card-text">{{ t('actionHint.swipeUp') }}</div>
            <div class="jumping-arrow jumping-arrow-up">
              <svg class="arrow-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 15l7-7 7 7" />
              </svg>
            </div>
          </div>
          
          <!-- Right Action Card (Like) -->
          <div class="action-hint-card action-hint-card-right">
            <div class="card-icon-wrapper">
              <svg class="card-icon" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
              </svg>
            </div>
            <div class="card-text">{{ t('actionHint.swipeRight') }}</div>
            <div class="jumping-arrow jumping-arrow-right">
              <svg class="arrow-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>
        </div>
        
        <!-- Dismiss Button -->
        <button
          @click.stop="handleDismiss"
          class="action-hint-dismiss"
          :aria-label="t('actionHint.dismiss')"
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
import { useI18n } from '~/composables/useI18n'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  dismiss: []
}>()

const { t } = useI18n()

const handleDismiss = () => {
  emit('dismiss')
}
</script>

<style scoped>
.action-hint-overlay {
  position: absolute;
  inset: 0;
  z-index: 45;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  pointer-events: none; /* Allow touches to pass through to swiper */
}

.action-hint-container {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  padding: 1.75rem 1.25rem;
  background: linear-gradient(135deg, 
    rgba(0, 0, 0, 0.92) 0%, 
    rgba(20, 20, 35, 0.95) 50%,
    rgba(0, 0, 0, 0.92) 100%);
  backdrop-filter: blur(24px) saturate(200%);
  -webkit-backdrop-filter: blur(24px) saturate(200%);
  border-radius: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow: 
    0 25px 80px rgba(0, 0, 0, 0.6),
    0 0 0 1px rgba(255, 255, 255, 0.08) inset,
    0 0 60px rgba(59, 130, 246, 0.1);
  animation: fadeInScaleBounce 0.6s cubic-bezier(0.34, 1.56, 0.64, 1), containerFloat 6s ease-in-out infinite;
  pointer-events: auto;
  max-width: 95%;
  width: 100%;
}

@keyframes fadeInScaleBounce {
  0% {
    opacity: 0;
    transform: scale(0.8) translateY(30px) rotate(-2deg);
  }
  60% {
    transform: scale(1.05) translateY(-5px) rotate(1deg);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0) rotate(0deg);
  }
}

@keyframes containerFloat {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-8px) rotate(0.5deg);
  }
}

/* Center Section */
.action-hint-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.25rem;
  width: 100%;
  text-align: center;
}

.action-hint-main-text {
  color: white;
  font-size: 1.125rem;
  font-weight: 600;
  text-align: center;
  letter-spacing: 0.02em;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  animation: textGlow 3s ease-in-out infinite;
}

@keyframes textGlow {
  0%, 100% {
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3), 0 0 20px rgba(255, 255, 255, 0.1);
  }
  50% {
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3), 0 0 30px rgba(255, 255, 255, 0.2);
  }
}

/* Action Cards */
.action-hint-actions {
  display: flex;
  gap: 0.75rem;
  width: 100%;
  justify-content: center;
  align-items: flex-end;
  position: relative;
}

.action-hint-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  gap: 0.75rem;
  padding: 1.25rem 1rem;
  border-radius: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  animation: cardFloat 3s ease-in-out infinite;
  max-width: 120px;
  min-width: 0;
  position: relative;
  overflow: visible;
  min-height: 140px;
}

@keyframes cardFloat {
  0%, 100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-6px) scale(1.02);
  }
}

.action-hint-card-left {
  animation-delay: 0s;
}

.action-hint-card-left:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.4);
  transform: translateY(-8px) scale(1.08);
  box-shadow: 0 10px 30px rgba(239, 68, 68, 0.3);
}

.action-hint-card-center {
  animation-delay: 0.2s;
  margin-bottom: 1.5rem; /* Lower position for share card */
}

.action-hint-card-center:hover {
  background: rgba(168, 85, 247, 0.2);
  border-color: rgba(168, 85, 247, 0.4);
  transform: translateY(-8px) scale(1.08);
  box-shadow: 0 10px 30px rgba(168, 85, 247, 0.3);
}

.action-hint-card-right {
  animation-delay: 0.4s;
}

.action-hint-card-right:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.4);
  transform: translateY(-8px) scale(1.08);
  box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
}

.card-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3.5rem;
  height: 3.5rem;
  min-width: 3.5rem;
  min-height: 3.5rem;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  flex-shrink: 0;
}

.action-hint-card-left .card-icon-wrapper {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.15) 100%);
}

.action-hint-card-center .card-icon-wrapper {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(147, 51, 234, 0.15) 100%);
}

.action-hint-card-right .card-icon-wrapper {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.15) 100%);
}

.card-icon {
  width: 2rem;
  height: 2rem;
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.3));
  animation: iconMicroMove 2.5s ease-in-out infinite;
  transform-origin: center;
}

@keyframes iconMicroMove {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(1px, -1px) scale(1.05);
  }
  50% {
    transform: translate(0, 0) scale(1);
  }
  75% {
    transform: translate(-1px, 1px) scale(1.05);
  }
}

.action-hint-card-left .card-icon {
  color: #f87171; /* Lighter red */
}

.action-hint-card-center .card-icon {
  color: #a78bfa; /* Lighter purple */
}

.action-hint-card-right .card-icon {
  color: #60a5fa; /* Lighter blue */
}

.card-text {
  color: white;
  font-size: 0.875rem;
  font-weight: 600;
  text-align: center;
  letter-spacing: 0.03em;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  width: 100%;
  line-height: 1.3;
  flex-shrink: 0;
}

/* Jumping Arrows */
.jumping-arrow {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  min-width: 2rem;
  min-height: 2rem;
  color: rgba(255, 255, 255, 0.7);
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  flex-shrink: 0;
}

.jumping-arrow-left {
  left: -1.5rem;
  top: 50%;
  transform: translateY(-50%);
  animation: jumpLeft 1.5s ease-in-out infinite;
}

.jumping-arrow-right {
  right: -1.5rem;
  top: 50%;
  transform: translateY(-50%);
  animation: jumpRight 1.5s ease-in-out infinite;
}

.jumping-arrow-up {
  bottom: -1.5rem;
  left: 50%;
  transform: translateX(-50%);
  animation: jumpUp 1.5s ease-in-out infinite;
}

@keyframes jumpLeft {
  0%, 100% {
    transform: translateY(-50%) translateX(0) scale(1);
    opacity: 0.8;
  }
  25% {
    transform: translateY(-50%) translateX(-8px) scale(1.1);
    opacity: 1;
  }
  50% {
    transform: translateY(-50%) translateX(-14px) scale(1.15);
    opacity: 1;
  }
  75% {
    transform: translateY(-50%) translateX(-8px) scale(1.1);
    opacity: 1;
  }
}

@keyframes jumpRight {
  0%, 100% {
    transform: translateY(-50%) translateX(0) scale(1);
    opacity: 0.8;
  }
  25% {
    transform: translateY(-50%) translateX(8px) scale(1.1);
    opacity: 1;
  }
  50% {
    transform: translateY(-50%) translateX(14px) scale(1.15);
    opacity: 1;
  }
  75% {
    transform: translateY(-50%) translateX(8px) scale(1.1);
    opacity: 1;
  }
}

@keyframes jumpUp {
  0%, 100% {
    transform: translateX(-50%) translateY(0) scale(1);
    opacity: 0.8;
  }
  25% {
    transform: translateX(-50%) translateY(-8px) scale(1.1);
    opacity: 1;
  }
  50% {
    transform: translateX(-50%) translateY(-14px) scale(1.15);
    opacity: 1;
  }
  75% {
    transform: translateX(-50%) translateY(-8px) scale(1.1);
    opacity: 1;
  }
}

.arrow-icon {
  width: 2rem;
  height: 2rem;
}

/* Dismiss Button */
.action-hint-dismiss {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  width: 2.75rem;
  height: 2.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  pointer-events: auto;
  backdrop-filter: blur(10px);
  animation: dismissPulse 2s ease-in-out infinite;
}

@keyframes dismissPulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.2);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(255, 255, 255, 0);
  }
}

.action-hint-dismiss:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1) rotate(90deg);
  border-color: rgba(255, 255, 255, 0.3);
}

.action-hint-dismiss:active {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(0.9) rotate(90deg);
}

.dismiss-icon {
  width: 1.25rem;
  height: 1.25rem;
}

/* Mobile Optimizations */
@media (max-width: 480px) {
  .action-hint-overlay {
    padding: 0.75rem;
    align-items: center;
    justify-content: center;
  }

  .action-hint-container {
    padding: 1.5rem 1rem;
    gap: 1rem;
    border-radius: 1.75rem;
    max-width: 98%;
    width: 100%;
  }

  .action-hint-main-text {
    font-size: 0.9375rem;
    font-weight: 700;
  }

  .action-hint-actions {
    gap: 0.5rem;
    width: 100%;
  }

  .action-hint-card {
    padding: 1rem 0.5rem;
    gap: 0.5rem;
    max-width: 100px;
    border-radius: 1.25rem;
  }

  .action-hint-card-center {
    margin-bottom: 1rem;
  }

  .card-icon-wrapper {
    width: 2.75rem;
    height: 2.75rem;
  }

  .card-icon {
    width: 1.5rem;
    height: 1.5rem;
  }

  .card-text {
    font-size: 0.75rem;
    font-weight: 700;
    line-height: 1.2;
  }

  .jumping-arrow {
    width: 1.5rem;
    height: 1.5rem;
  }

  .arrow-icon {
    width: 1.5rem;
    height: 1.5rem;
  }

  .jumping-arrow-left {
    left: -1rem;
  }

  .jumping-arrow-right {
    right: -1rem;
  }

  .jumping-arrow-up {
    bottom: -1rem;
  }

  .action-hint-dismiss {
    width: 2.25rem;
    height: 2.25rem;
    top: 0.5rem;
    right: 0.5rem;
  }

  .dismiss-icon {
    width: 1rem;
    height: 1rem;
  }
}

/* Very small screens */
@media (max-width: 360px) {
  .action-hint-container {
    padding: 1.5rem 1rem;
  }

  .action-hint-card {
    max-width: 85px;
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

  .jumping-arrow {
    width: 1.5rem;
    height: 1.5rem;
  }

  .arrow-icon {
    width: 1.5rem;
    height: 1.5rem;
  }
}

/* Transition animations */
.fade-enter-active {
  transition: opacity 0.5s cubic-bezier(0.34, 1.56, 0.64, 1), 
              transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.fade-leave-active {
  transition: opacity 0.3s ease-out, 
              transform 0.3s ease-out;
}

.fade-enter-from {
  opacity: 0;
  transform: scale(0.85) translateY(20px) rotate(-3deg);
}

.fade-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-10px);
}
</style>
