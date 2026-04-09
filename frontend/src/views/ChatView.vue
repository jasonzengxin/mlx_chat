<template>
  <div class="chat-view">
    <div class="sidebar">
      <SessionList />
    </div>
    <div class="main">
      <ChatArea />
      <InputArea />
    </div>
  </div>
</template>

<script setup lang="ts">
import SessionList from '@/components/SessionList.vue'
import ChatArea from '@/components/ChatArea.vue'
import InputArea from '@/components/InputArea.vue'
</script>

<style scoped>
.chat-view {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 280px;
  background: var(--bg-secondary);
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>