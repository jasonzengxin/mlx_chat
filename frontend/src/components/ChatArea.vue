<template>
  <div class="chat-area">
    <div v-if="messages.length === 0" class="empty">
      开始对话吧
    </div>
    <div v-else class="messages">
      <MessageBubble
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import MessageBubble from './MessageBubble.vue'

const store = useChatStore()

const messages = computed(() => store.messages)
</script>

<style scoped>
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
}
</style>