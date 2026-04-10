<template>
  <div class="chat-view">
    <!-- API Key Setup Modal -->
    <transition name="fade">
      <div v-if="!hasApiKey" class="modal-overlay">
        <div class="modal">
          <h2>Welcome to MLX Chat</h2>
          <p>Enter your API key to continue</p>
          
          <div class="input-group">
            <input
              v-model="apiKeyInput"
              type="password"
              placeholder="sk-..."
              @keydown.enter="setupApiKey"
              autofocus
            />
            <span v-if="error" class="error-msg">{{ error }}</span>
          </div>

          <button @click="setupApiKey" class="submit-btn">
            Continue
          </button>

          <div class="help">
            <p>Don't have an API key?</p>
            <code>python backend/init_db.py</code>
          </div>
        </div>
      </div>
    </transition>

    <!-- Main Chat UI -->
    <div v-if="hasApiKey" class="main-ui-wrapper">
      <aside class="sidebar">
        <div class="sidebar-header">
          <h1 class="logo">MLX Chat</h1>
          <router-link to="/settings" class="settings-link" title="Settings">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1-1-1.72v-.51a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
          </router-link>
        </div>
        <ModelSelector />
        <div class="sidebar-content">
          <SessionList />
        </div>
        <div class="sidebar-footer">
          <div class="user-info">
            <div class="avatar">U</div>
            <span>User</span>
          </div>
        </div>
      </aside>

      <main class="main-container">
        <header class="chat-header" v-if="currentSessionName">
          <div class="session-info">
            <span class="session-name">{{ currentSessionName }}</span>
          </div>
          <div class="header-actions">
            <div class="context-control">
              <label class="context-label" title="Number of historical messages sent to the model per request (0 = no history, -1 = all)">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                <span>Context</span>
              </label>
              <select
                class="context-select"
                :value="currentContextMessages"
                @change="onContextChange"
              >
                <option :value="0">None</option>
                <option :value="4">4</option>
                <option :value="10">10</option>
                <option :value="20">20</option>
                <option :value="40">40</option>
                <option :value="-1">All</option>
              </select>
            </div>
            <button
              class="toggle-panel-btn"
              :class="{ active: showParams }"
              @click="showParams = !showParams"
              title="Parameters"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1-1-1.72v-.51a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
          </div>
        </header>
        <div class="chat-content" :class="{ 'with-panel': showParams }">
          <ChatArea />
        </div>
        <footer class="chat-footer">
          <InputArea />
        </footer>
        <ParameterPanel
          :show="showParams"
          :temperature="paramTemperature"
          :maxTokens="paramMaxTokens"
          :systemPrompt="paramSystemPrompt"
          @close="showParams = false"
          @update:temperature="onTemperatureChange"
          @update:maxTokens="onMaxTokensChange"
          @update:systemPrompt="onSystemPromptChange"
        />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { hasApiKey as checkApiKey, setApiKey } from '@/api/auth'
import { useSessionStore } from '@/stores/session'
import ModelSelector from '@/components/ModelSelector.vue'
import SessionList from '@/components/SessionList.vue'
import ChatArea from '@/components/ChatArea.vue'
import InputArea from '@/components/InputArea.vue'
import ParameterPanel from '@/components/ParameterPanel.vue'

const sessionStore = useSessionStore()
const apiKeyInput = ref('')
const error = ref('')
const hasApiKey = ref(false)
const showParams = ref(false)

// Parameters state - synced with current session
const paramTemperature = ref(0.7)
const paramMaxTokens = ref(4096)
const paramSystemPrompt = ref('')

let saveDebounceTimer: ReturnType<typeof setTimeout> | null = null

const currentSessionName = computed(() => {
  const session = sessionStore.getCurrentSession()
  return session ? session.name : null
})

const currentContextMessages = computed(() => {
  const session = sessionStore.getCurrentSession()
  return session?.context_messages ?? 20
})

// Load params when session changes
watch(currentSessionName, () => {
  const session = sessionStore.getCurrentSession()
  if (session) {
    paramTemperature.value = session.temperature ?? 0.7
    paramMaxTokens.value = session.max_tokens ?? 4096
    paramSystemPrompt.value = session.system_prompt ?? ''
  }
}, { immediate: true })

function onContextChange(e: Event) {
  const val = Number((e.target as HTMLSelectElement).value)
  const session = sessionStore.getCurrentSession()
  if (session) {
    sessionStore.updateSession(session.id, { context_messages: val } as any)
  }
}

// Debounced save to session
function scheduleSave() {
  if (saveDebounceTimer) clearTimeout(saveDebounceTimer)
  saveDebounceTimer = setTimeout(() => {
    const session = sessionStore.getCurrentSession()
    if (session) {
      sessionStore.updateSession(session.id, {
        temperature: paramTemperature.value,
        max_tokens: paramMaxTokens.value,
        system_prompt: paramSystemPrompt.value
      } as any)
    }
  }, 500)
}

function onTemperatureChange(val: number) {
  paramTemperature.value = val
  scheduleSave()
}

function onMaxTokensChange(val: number) {
  paramMaxTokens.value = val
  scheduleSave()
}

function onSystemPromptChange(val: string) {
  paramSystemPrompt.value = val
  scheduleSave()
}

onMounted(() => {
  hasApiKey.value = checkApiKey()
})

function setupApiKey() {
  if (!apiKeyInput.value.trim()) {
    error.value = 'Please enter an API key'
    return
  }
  setApiKey(apiKeyInput.value.trim())
  hasApiKey.value = true
  error.value = ''
}
</script>

<style scoped>
.chat-view {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: var(--bg-primary);
}

.main-ui-wrapper {
  display: flex;
  width: 100%;
  height: 100%;
}

/* Modal Styling */
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background-color: var(--bg-secondary);
  padding: 2.5rem;
  border-radius: var(--radius-xl);
  max-width: 440px;
  width: 90%;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border);
}

.modal h2 {
  margin-bottom: 0.5rem;
  font-size: 1.5rem;
  font-weight: 600;
}

.modal p {
  margin-bottom: 2rem;
  color: var(--text-secondary);
}

.input-group {
  margin-bottom: 1.5rem;
}

.input-group input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 1rem;
  transition: border-color 0.2s;
}

.input-group input:focus {
  outline: none;
  border-color: var(--accent);
}

.error-msg {
  color: var(--error);
  font-size: 0.875rem;
  margin-top: 0.5rem;
  display: block;
}

.submit-btn {
  width: 100%;
  padding: 0.875rem;
  background-color: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}

.submit-btn:hover {
  background-color: var(--accent-hover);
}

.help {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
  text-align: center;
}

.help p {
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
}

.help code {
  background-color: var(--bg-tertiary);
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-sm);
  font-family: monospace;
  font-size: 0.875rem;
  color: var(--accent);
}

/* Sidebar Styling */
.sidebar {
  width: 300px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  z-index: 10;
}

.sidebar-header {
  padding: 1.25rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent), #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.settings-link {
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.settings-link:hover {
  color: var(--text-primary);
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
}

.sidebar-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: 600;
  color: white;
}

/* Main Container Styling */
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  background: var(--bg-primary);
}

.chat-header {
  height: 64px;
  padding: 0 1.5rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  background: var(--bg-secondary);
  backdrop-filter: blur(8px);
  position: sticky;
  top: 0;
  z-index: 5;
}

.session-name {
  font-weight: 600;
  font-size: 1rem;
  color: var(--text-primary);
}

.chat-header {
  justify-content: space-between;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.context-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.context-label {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  cursor: help;
}

.context-select {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 0.75rem;
  padding: 0.3rem 0.5rem;
  cursor: pointer;
  outline: none;
  transition: border-color 0.15s;
}

.context-select:hover,
.context-select:focus {
  border-color: var(--accent);
}

.toggle-panel-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-panel-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.toggle-panel-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.chat-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
}

.chat-footer {
  padding: 0 1.5rem 1.5rem;
}
</style>
