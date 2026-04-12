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
            <button
              class="copy-btn"
              @click="copyKey(key.id, key.key_prefix)"
              :title="copiedKeyId === key.id ? 'Copied!' : 'Copy key'"
            >
              <svg v-if="copiedKeyId !== key.id" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
            </button>
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

    <!-- Created Key Modal -->
    <Modal
      :show="showCreatedKeyModal"
      title="API Key Created"
      confirmText="Done"
      cancelText=""
      @close="closeCreatedKeyModal"
      @confirm="closeCreatedKeyModal"
    >
      <div class="created-key-box">
        <p class="created-tip">Copy now. For security reasons, this full key is only shown once.</p>
        <code class="created-key-value">{{ createdKeyValue }}</code>
        <button class="copy-created-btn" @click="copyCreatedKey">
          {{ copiedCreatedKey ? 'Copied!' : 'Copy key' }}
        </button>
      </div>
    </Modal>
    <p v-if="copyHint" class="copy-hint">{{ copyHint }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { getApiKey } from '@/api/auth'
import type { APIKey } from '@/stores/settings'
import Modal from './Modal.vue'

const store = useSettingsStore()
const apiKeys = computed(() => store.apiKeys)

const showCreateModal = ref(false)
const showDeleteModal = ref(false)
const showCreatedKeyModal = ref(false)
const newKeyName = ref('')
const keyToDelete = ref<string | null>(null)
const createdKeyValue = ref('')
const copiedCreatedKey = ref(false)
const copiedKeyId = ref<string | null>(null)
const copyHint = ref('')
const ephemeralKeyMap = ref<Record<string, string>>({})

function setCopyHint(text: string) {
  copyHint.value = text
  setTimeout(() => {
    if (copyHint.value === text) {
      copyHint.value = ''
    }
  }, 2500)
}

function closeCreatedKeyModal() {
  showCreatedKeyModal.value = false
  createdKeyValue.value = ''
  copiedCreatedKey.value = false
}

async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(textarea)
    return ok
  }
}

function resolveFullKey(keyId: string, keyPrefix: string): string | null {
  if (ephemeralKeyMap.value[keyId]) {
    return ephemeralKeyMap.value[keyId]
  }
  const localKey = getApiKey()
  if (localKey && localKey.startsWith(keyPrefix)) {
    return localKey
  }
  return null
}

function closeCreateModal() {
  showCreateModal.value = false
  newKeyName.value = ''
}

async function handleCreateKey() {
  if (newKeyName.value.trim()) {
    const created = await store.createApiKey(newKeyName.value.trim())
    if (created?.id && created?.key) {
      ephemeralKeyMap.value[created.id] = created.key
      createdKeyValue.value = created.key
      showCreatedKeyModal.value = true
    }
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

async function copyCreatedKey() {
  if (!createdKeyValue.value) return
  const ok = await copyText(createdKeyValue.value)
  if (ok) {
    copiedCreatedKey.value = true
  }
}

async function copyKey(keyId: string, keyPrefix: string) {
  const fullKey = resolveFullKey(keyId, keyPrefix)
  if (!fullKey) {
    setCopyHint('This key cannot be recovered from server. Create a new key to copy full value.')
    return
  }
  const ok = await copyText(fullKey)
  if (!ok) return
  copiedKeyId.value = keyId
  setTimeout(() => {
    if (copiedKeyId.value === keyId) {
      copiedKeyId.value = null
    }
  }, 1800)
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

.key-value-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.copy-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
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

.created-key-box {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.created-tip {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.created-key-value {
  word-break: break-all;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  background: var(--bg-tertiary);
  padding: 0.625rem 0.75rem;
  border-radius: var(--radius-sm);
}

.copy-created-btn {
  align-self: flex-start;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-primary);
  border-radius: var(--radius-md);
  padding: 0.4rem 0.75rem;
  cursor: pointer;
}

.copy-created-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.copy-hint {
  margin: 0;
  font-size: 0.82rem;
  color: var(--text-secondary);
}
</style>
