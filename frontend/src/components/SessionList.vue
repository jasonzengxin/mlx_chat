<template>
  <div class="session-list">
    <div class="list-header">
      <button class="new-chat-btn" @click="createNewSession">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
        <span>New Chat</span>
      </button>
    </div>
    
    <div class="sessions-container">
      <div 
        v-for="session in sessions" 
        :key="session.id"
        class="session-item"
        :class="{ active: session.id === currentSessionId }"
        @click="selectSession(session.id)"
      >
        <div class="session-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        </div>
        <div class="session-name" v-if="editingId !== session.id">
          {{ session.name }}
        </div>
        <input 
          v-else
          ref="editInput"
          v-model="editName"
          class="session-edit-input"
          @blur="saveName(session.id)"
          @keydown.enter="saveName(session.id)"
          @click.stop
        />
        
        <div class="actions" v-if="editingId !== session.id">
          <button class="action-btn" @click.stop="startEdit(session)" title="Rename">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>
          </button>
          <button class="action-btn delete" @click.stop="confirmDelete(session.id)" title="Delete">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>
          </button>
        </div>
      </div>
    </div>

    <Modal 
      :show="showDeleteModal" 
      title="Delete Session" 
      confirmText="Delete"
      @close="showDeleteModal = false"
      @confirm="handleDelete"
    >
      <p>Are you sure you want to delete this chat session?</p>
    </Modal>

    <div v-if="error" class="error-msg">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useSessionStore } from '@/stores/session'
import Modal from './Modal.vue'

const store = useSessionStore()

const sessions = computed(() => store.sessions)
const currentSessionId = computed(() => store.currentSessionId)
const error = computed(() => store.error)

const editingId = ref<string | null>(null)
const editName = ref('')
const editInput = ref<HTMLInputElement | null>(null)
const showDeleteModal = ref(false)
const sessionToDelete = ref<string | null>(null)

onMounted(async () => {
  await store.fetchSessions()
  if (!store.currentSessionId && store.sessions.length > 0) {
    store.selectSession(store.sessions[0].id)
  }
})

async function createNewSession() {
  await store.createSession({ name: 'New Chat' })
}

function selectSession(id: string) {
  store.selectSession(id)
}

function confirmDelete(id: string) {
  sessionToDelete.value = id
  showDeleteModal.value = true
}

async function handleDelete() {
  if (sessionToDelete.value) {
    await store.deleteSession(sessionToDelete.value)
    showDeleteModal.value = false
    sessionToDelete.value = null
  }
}

function startEdit(session: any) {
  editingId.value = session.id
  editName.value = session.name
  nextTick(() => {
    editInput.value?.[0]?.focus() || editInput.value?.focus()
  })
}

async function saveName(id: string) {
  if (!editingId.value) return
  
  const name = editName.value.trim()
  if (name && name !== sessions.value.find(s => s.id === id)?.name) {
    await store.updateSession(id, { name })
  }
  
  editingId.value = null
}
</script>

<style scoped>
.session-list {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.list-header {
  padding: 0 1.5rem 1rem;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: transparent;
  border: 1px dashed var(--border);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  border-style: solid;
  border-color: var(--accent);
  background: rgba(99, 102, 241, 0.05);
}

.sessions-container {
  flex: 1;
  overflow-y: auto;
  padding: 0 0.75rem;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  margin-bottom: 2px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.session-item:hover {
  background: var(--bg-tertiary);
}

.session-item.active {
  background: var(--bg-tertiary);
  color: var(--accent);
}

.session-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.625rem;
  bottom: 0.625rem;
  width: 3px;
  background: var(--accent);
  border-radius: 0 4px 4px 0;
}

.session-icon {
  flex-shrink: 0;
  color: var(--text-secondary);
}

.session-item.active .session-icon {
  color: var(--accent);
}

.session-name {
  flex: 1;
  font-size: 0.875rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-edit-input {
  flex: 1;
  background: var(--bg-primary);
  border: 1px solid var(--accent);
  border-radius: 4px;
  color: var(--text-primary);
  font-size: 0.875rem;
  padding: 2px 4px;
  width: 100%;
}

.actions {
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .actions {
  opacity: 1;
}

.action-btn {
  padding: 4px;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 4px;
  display: flex;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.action-btn.delete:hover {
  color: var(--error);
}

.error-msg {
  padding: 1rem 1.5rem;
  color: var(--error);
  font-size: 0.75rem;
}
</style>
