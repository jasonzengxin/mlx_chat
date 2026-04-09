<template>
  <div class="message-bubble" :class="message.role">
    <div class="role">{{ message.role }}</div>
    <div class="content">{{ message.content }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  message: {
    id: string
    role: string
    content: string
  }
}>()
</script>

<style scoped>
.message-bubble {
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  max-width: 80%;
}

.message-bubble.user {
  margin-left: auto;
  background: var(--accent);
  color: white;
}

.message-bubble.assistant {
  margin-right: auto;
  background: var(--bg-tertiary);
}

.role {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
}

.content {
  white-space: pre-wrap;
}
</style>