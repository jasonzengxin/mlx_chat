<template>
  <div class="input-area">
    <textarea
      v-model="inputText"
      :disabled="disabled || isGenerating"
      placeholder="输入消息..."
      @keydown.enter.exact="send"
    />
    <button :disabled="!canSend" @click="send">
      {{ isGenerating ? '生成中...' : '发送' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useChatStore } from '@/stores/chat'

const props = defineProps<{
  disabled?: boolean
}>()

const store = useChatStore()
const inputText = ref('')

const isGenerating = computed(() => store.isGenerating)
const canSend = computed(() => inputText.value.trim() && !props.disabled && !isGenerating.value)

function send() {
  if (!canSend.value) return

  const text = inputText.value.trim()
  inputText.value = ''

  store.sendMessage(text)
}
</script>

<style scoped>
.input-area {
  display: flex;
  gap: 0.5rem;
  padding: 1rem;
  border-top: 1px solid var(--border);
}

textarea {
  flex: 1;
  padding: 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text-primary);
  resize: none;
  min-height: 60px;
}

textarea:focus {
  outline: none;
  border-color: var(--accent);
}

button {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  border: none;
  background: var(--accent);
  color: white;
  cursor: pointer;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>