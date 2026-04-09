<template>
  <div class="api-key-list">
    <div v-for="key in apiKeys" :key="key.id" class="key-item">
      <div class="key-info">
        <span class="name">{{ key.name }}</span>
        <span class="prefix">{{ key.key_prefix }}</span>
      </div>
      <button @click="deleteKey(key.id)">删除</button>
    </div>
    <button class="create-btn" @click="createKey">创建新 Key</button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'

const store = useSettingsStore()

const apiKeys = computed(() => store.apiKeys)

function createKey() {
  const name = prompt('输入 Key 名称:')
  if (name) {
    store.createApiKey(name)
  }
}

function deleteKey(id: string) {
  if (confirm('确定要删除这个 Key 吗？')) {
    store.deleteApiKey(id)
  }
}
</script>

<style scoped>
.api-key-list {
  margin-top: 1rem;
}

.key-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.key-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.name {
  font-weight: 500;
}

.prefix {
  font-family: monospace;
  color: var(--text-secondary);
}

.create-btn {
  width: 100%;
  padding: 0.75rem;
  margin-top: 1rem;
  border-radius: 8px;
  border: 1px dashed var(--border);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}

.create-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}
</style>