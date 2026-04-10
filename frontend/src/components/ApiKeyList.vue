<template>
  <div class="api-key-list">
    <div class="keys-container">
      <div v-for="key in apiKeys" :key="key.id" class="key-card">
        <div class="key-info">
          <div class="key-name-row">
            <span class="name">{{ key.name }}</span>
            <span class="badge">Active</span>
          </div>
          <div class="key-value-row">
            <code>{{ key.key_prefix }}••••••••••••••••</code>
          </div>
        </div>
        <button class="delete-btn" @click="confirmDelete(key.id)" title="Delete key">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
        </button>
      </div>
    </div>
    
    <button class="create-btn" @click="showCreateModal = true">
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
      <span>Create New API Key</span>
    </button>

    <!-- Create Key Modal -->
    <Modal 
      :show="showCreateModal" 
      title="Create API Key" 
      confirmText="Create"
      :confirmDisabled="!newKeyName.trim()"
      @close="closeCreateModal"
      @confirm="handleCreateKey"
    >
      <div class="form-group">
        <label>Key Name</label>
        <input 
          v-model="newKeyName" 
          type="text" 
          placeholder="e.g. My Development Key"
          @keydown.enter="handleCreateKey"
          class="settings-input"
          ref="createInput"
        />
      </div>
    </Modal>

    <!-- Delete Confirm Modal -->
    <Modal 
      :show="showDeleteModal" 
      title="Delete API Key" 
      confirmText="Delete"
      cancelText="Cancel"
      @close="showDeleteModal = false"
      @confirm="handleDeleteKey"
    >
      <p>Are you sure you want to delete this API key? This action cannot be undone.</p>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import Modal from './Modal.vue'

const store = useSettingsStore()
const apiKeys = computed(() => store.apiKeys)

const showCreateModal = ref(false)
const showDeleteModal = ref(false)
const newKeyName = ref('')
const keyToDelete = ref<string | null>(null)

function closeCreateModal() {
  showCreateModal.value = false
  newKeyName.value = ''
}

function handleCreateKey() {
  if (newKeyName.value.trim()) {
    store.createApiKey(newKeyName.value.trim())
    closeCreateModal()
  }
}

function confirmDelete(id: string) {
  keyToDelete.value = id
  showDeleteModal.value = true
}

function handleDeleteKey() {
  if (keyToDelete.value) {
    store.deleteApiKey(keyToDelete.value)
    showDeleteModal.value = false
    keyToDelete.value = null
  }
}
</script>

<style scoped>
.api-key-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.keys-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.key-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  transition: all 0.2s;
}

.key-card:hover {
  border-color: var(--accent);
}

.key-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.key-name-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.name {
  font-weight: 600;
  font-size: 1rem;
}

.badge {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 6px;
  background: rgba(16, 185, 129, 0.1);
  color: var(--success);
  border-radius: 4px;
}

.key-value-row code {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  color: var(--text-secondary);
  font-size: 0.875rem;
  background: var(--bg-tertiary);
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-sm);
}

.delete-btn {
  padding: 0.5rem;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all 0.2s;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: var(--error);
}

.create-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  width: 100%;
  padding: 1rem;
  background: transparent;
  border: 1px dashed var(--border);
  border-radius: var(--radius-lg);
  color: var(--text-primary);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.create-btn:hover {
  border-style: solid;
  border-color: var(--accent);
  background: rgba(99, 102, 241, 0.05);
  color: var(--accent);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.settings-input {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  outline: none;
}

.settings-input:focus {
  border-color: var(--accent);
}
</style>
