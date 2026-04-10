<template>
  <div class="chat-area" ref="scrollContainer">
    <div v-if="store.error" class="error-banner">
      <div class="error-content">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
        <span>{{ store.error }}</span>
      </div>
      <button @click="clearError" class="close-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
      </button>
    </div>

    <div v-if="messages.length === 0" class="empty-state">
      <div class="welcome-box">
        <div class="welcome-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
        </div>
        <h2>Welcome to MLX Chat</h2>
        <p>Your local AI companion powered by MLX. How can I help you today?</p>
        <div class="quick-tips">
          <div class="tip">Try asking for code examples</div>
          <div class="tip">Ask for a summary of a topic</div>
        </div>
      </div>
    </div>
    
    <div v-else class="messages-list">
      <MessageBubble
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
        :isStreaming="store.isGenerating && msg.id === lastAssistantId"
        :elapsedMs="store.generatingElapsedMs"
        :tokenCount="store.tokenCount"
        :tokPerSec="tokensPerSec"
      />
      <div ref="bottom"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import MessageBubble from './MessageBubble.vue'

const store = useChatStore()
const messages = computed(() => store.messages)
const scrollContainer = ref<HTMLElement | null>(null)
const bottom = ref<HTMLElement | null>(null)

const lastAssistantId = computed(() => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === 'assistant') return messages.value[i].id
  }
  return null
})

const tokensPerSec = computed(() => {
  const elapsed = store.generatingElapsedMs
  if (elapsed < 1000 || store.tokenCount < 2) return 0
  return Math.round(store.tokenCount / (elapsed / 1000) * 10) / 10
})

function clearError() {
  store.error = null
}

function scrollToBottom(behavior: ScrollBehavior = 'auto') {
  nextTick(() => {
    bottom.value?.scrollIntoView({ behavior, block: 'end' })
  })
}

watch(() => messages.value.length, (_, previousLength) => {
  scrollToBottom(previousLength > 0 ? 'smooth' : 'auto')
})

watch(() => store.tokenCount, () => {
  if (store.isGenerating) {
    scrollToBottom('auto')
  }
})

watch(() => store.isGenerating, (val) => {
  scrollToBottom(val ? 'auto' : 'smooth')
})

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
}

.messages-list {
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.welcome-box {
  max-width: 400px;
}

.welcome-icon {
  width: 80px;
  height: 80px;
  background: var(--bg-tertiary);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  color: var(--accent);
}

.welcome-box h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
}

.welcome-box p {
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 2rem;
}

.quick-tips {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.tip {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.tip:hover {
  border-color: var(--accent);
  color: var(--text-primary);
  background: rgba(99, 102, 241, 0.05);
}

.error-banner {
  position: sticky;
  top: 0;
  background: var(--error);
  color: white;
  padding: 0.75rem 1.25rem;
  border-radius: var(--radius-md);
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  box-shadow: var(--shadow-md);
  z-index: 10;
}

.error-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 500;
}

.close-btn {
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
  padding: 4px;
  display: flex;
  opacity: 0.8;
}

.close-btn:hover {
  opacity: 1;
}

</style>
