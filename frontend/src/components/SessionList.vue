<template>
  <div class="session-list">
    <div class="header">
      <button @click="createSession">新建会话</button>
    </div>
    <div class="sessions">
      <div
        v-for="session in sessions"
        :key="session.id"
        class="session-item"
        :class="{ active: session.id === currentId }"
        @click="selectSession(session.id)"
      >
        <span>{{ session.name }}</span>
        <button class="delete-btn" @click.stop="deleteSession(session.id)">删除</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSessionStore } from '@/stores/session'

const store = useSessionStore()

const sessions = computed(() => store.sessions)
const currentId = computed(() => store.currentSessionId)

function createSession() {
  store.createSession()
}

function selectSession(id: string) {
  store.selectSession(id)
}

function deleteSession(id: string) {
  store.deleteSession(id)
}
</script>