<template>
  <div class="input-area-container">
    <div v-if="!hasSession" class="no-session-overlay">
      <p>Select or create a session to start chatting</p>
    </div>
    
    <div class="input-wrapper" :class="{ focused: isFocused, disabled: !canSend && !isGenerating }">
      <textarea
        ref="inputRef"
        v-model="inputText"
        :disabled="disabled || isGenerating || !hasSession"
        placeholder="Type a message..."
        @keydown.enter.prevent="handleEnter"
        @focus="isFocused = true"
        @blur="isFocused = false"
        rows="1"
        @input="autoResize"
      />
      
      <button 
        class="send-btn" 
        :disabled="!canSend || isGenerating" 
        @click="send"
        :title="isGenerating ? 'Generating...' : 'Send message'"
      >
        <template v-if="isGenerating">
          <div class="stop-icon"></div>
        </template>
        <template v-else>
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </template>
      </button>
    </div>
    <div class="input-meta">
      Press Enter to send, Shift + Enter for new line
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useSessionStore } from '@/stores/session'

const props = defineProps<{
  disabled?: boolean
}>()

const chatStore = useChatStore()
const sessionStore = useSessionStore()
const inputText = ref('')
const isFocused = ref(false)
const inputRef = ref<HTMLTextAreaElement | null>(null)

const isGenerating = computed(() => chatStore.isGenerating)
const hasSession = computed(() => sessionStore.currentSessionId !== null)
const canSend = computed(() => inputText.value.trim() !== '' && !props.disabled && !isGenerating.value && hasSession.value)

function autoResize() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = (el.scrollHeight) + 'px'
}

watch(inputText, () => {
  if (inputText.value === '') {
    if (inputRef.value) inputRef.value.style.height = 'auto'
  }
})

function handleEnter(e: KeyboardEvent) {
  if (e.shiftKey) {
    // Let default behavior (new line) happen
    return
  }
  send()
}

function send() {
  if (!canSend.value) return

  const text = inputText.value.trim()
  inputText.value = ''
  if (inputRef.value) inputRef.value.style.height = 'auto'

  // Get session parameters
  const session = sessionStore.getCurrentSession()
  const options = session ? {
    temperature: session.temperature,
    max_tokens: session.max_tokens,
    system_prompt: session.system_prompt,
    context_messages: session.context_messages
  } : undefined

  chatStore.sendMessage(text, options)
}

onMounted(() => {
  if (hasSession.value) {
    inputRef.value?.focus()
  }
})

watch(hasSession, (newVal) => {
  if (newVal) {
    setTimeout(() => inputRef.value?.focus(), 100)
  }
})
</script>

<style scoped>
.input-area-container {
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
  position: relative;
}

.no-session-overlay {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  transition: all 0.2s;
  box-shadow: var(--shadow-sm);
}

.input-wrapper.focused {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
  background: var(--bg-primary);
}

textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 1rem;
  line-height: 1.5;
  padding: 4px 0;
  resize: none;
  max-height: 200px;
  outline: none;
}

textarea::placeholder {
  color: var(--text-secondary);
}

.send-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s;
  margin-bottom: 2px;
}

.send-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

.send-btn:active:not(:disabled) {
  transform: translateY(0);
}

.send-btn:disabled {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: not-allowed;
}

.stop-icon {
  width: 12px;
  height: 12px;
  background: currentColor;
  border-radius: 2px;
}

.input-meta {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-align: center;
  margin-top: 0.75rem;
}
</style>
