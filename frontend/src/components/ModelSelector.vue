<template>
  <div class="model-selector" ref="container">
    <button class="selector-trigger" @click="showList = !showList" :class="{ active: showList }">
      <div class="current-info">
        <template v-if="modelsStore.loadedModel">
          <span class="model-type-icon" :class="modelsStore.loadedModel.model_type || 'local'">
            {{ getModelIcon(modelsStore.loadedModel.model_type) }}
          </span>
          <span class="model-name">{{ modelsStore.loadedModel.name }}</span>
          <span class="status-badge" :class="getStatusBadgeClass(modelsStore.loadedModel.model_type)">
            {{ modelsStore.loadedModel.model_type === 'remote' ? 'API' : 'Loaded' }}
          </span>
        </template>
        <template v-else-if="loadingModel">
          <span class="model-name">{{ loadingModel.split('/').pop() }}</span>
          <span class="status-badge loading">
            <span class="spinner"></span>
            {{ formatTime(elapsedTime) }}
          </span>
        </template>
        <template v-else>
          <span class="placeholder">Select Model</span>
        </template>
      </div>
      <svg class="chevron" :class="{ open: showList }" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
    </button>

    <!-- Indeterminate progress bar during model loading -->
    <div v-if="loadingModel" class="progress-bar-track">
      <div class="progress-bar-fill"></div>
    </div>

    <transition name="dropdown">
      <div class="model-dropdown" v-if="showList">
        <div class="dropdown-header">Available Models</div>
        <div class="model-list">
          <!-- Local models -->
          <div
            v-for="model in localModels"
            :key="model.model_id"
            class="model-item"
            :class="{ active: model.is_loaded }"
            @click="startLoad(model.model_id)"
          >
            <div class="model-info">
              <div class="model-title">
                <span class="model-type-icon local">&#x1F5A5;</span>
                {{ model.name }}
              </div>
              <div class="model-meta">{{ model.params_count }} · {{ model.description }}</div>
            </div>
            <div class="load-status loading-time" v-if="loadingModel === model.model_id">
              <span class="spinner"></span>
              <span class="elapsed">{{ formatTime(elapsedTime) }}</span>
            </div>
            <div class="load-status" v-else-if="model.is_loaded">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
            </div>
          </div>

          <!-- Remote models section -->
          <template v-if="remoteModels.length > 0">
            <div class="model-section-divider">
              <span>Remote API Models</span>
            </div>
            <div
              v-for="model in remoteModels"
              :key="model.model_id"
              class="model-item remote"
              :class="{ active: model.is_loaded }"
              @click="selectRemoteModel(model.model_id)"
            >
              <div class="model-info">
                <div class="model-title">
                  <span class="model-type-icon remote">&#x2601;</span>
                  {{ model.name }}
                </div>
                <div class="model-meta">{{ model.remote_provider ? model.remote_provider + '/' : '' }}{{ model.model_id }}</div>
              </div>
              <div class="model-actions">
                <div class="load-status" v-if="model.is_loaded">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                </div>
                <button
                  class="delete-model-btn"
                  @click.stop="removeRemoteModel(model)"
                  title="Remove model"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </transition>

    <div v-if="modelsStore.error" class="error-toast">
      {{ modelsStore.error }}
    </div>

    <Modal
      :show="showDeleteModal"
      title="Remove Model"
      confirmText="Remove"
      cancelText="Cancel"
      confirmVariant="danger"
      size="sm"
      :confirmDisabled="deleting"
      @close="showDeleteModal = false"
      @confirm="confirmRemoveModel"
    >
      <p style="margin: 0; line-height: 1.5;">
        Remove remote model <strong>{{ pendingDeleteModel?.name }}</strong>?
      </p>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useModelsStore } from '@/stores/models'
import { useSessionStore } from '@/stores/session'
import { deleteModel } from '@/api/models'
import type { Model } from '@/api/models'
import Modal from '@/components/Modal.vue'

const modelsStore = useModelsStore()
const sessionStore = useSessionStore()
const showList = ref(false)
const loadingModel = ref<string | null>(null)
const elapsedTime = ref(0)
const container = ref<HTMLElement | null>(null)
let timer: number | null = null

const showDeleteModal = ref(false)
const pendingDeleteModel = ref<Model | null>(null)
const deleting = ref(false)

// Computed: separate local and remote models
const localModels = computed(() =>
  modelsStore.models.filter(m => !m.model_type || m.model_type === 'local')
)

const remoteModels = computed(() =>
  modelsStore.models.filter(m => m.model_type === 'remote')
)

onMounted(() => {
  modelsStore.fetchModels()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  document.removeEventListener('click', handleClickOutside)
})

function handleClickOutside(event: MouseEvent) {
  if (container.value && !container.value.contains(event.target as Node)) {
    showList.value = false
  }
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function getModelIcon(modelType?: string): string {
  return modelType === 'remote' ? '\u2601' : '\u1F5A5' // cloud vs computer
}

function getStatusBadgeClass(modelType?: string): string {
  return modelType === 'remote' ? 'api' : 'loaded'
}

async function syncSessionModel(modelId: string): Promise<boolean> {
  const sessionId = sessionStore.currentSessionId
  if (!sessionId) {
    modelsStore.error = 'Please create or select a session first'
    return false
  }

  const updated = await sessionStore.updateSession(sessionId, { model: modelId })
  if (!updated) {
    modelsStore.error = 'Failed to update session model'
    return false
  }
  return true
}

async function startLoad(modelId: string) {
  const model = modelsStore.models.find(m => m.model_id === modelId)
  if (!model) return

  // Remote models don't need loading
  if (model.model_type === 'remote') {
    await selectRemoteModel(modelId)
    return
  }

  if (loadingModel.value || model.is_loaded) {
    if (model.is_loaded) {
       showList.value = false
    }
    return
  }

  loadingModel.value = modelId
  elapsedTime.value = 0

  timer = window.setInterval(() => {
    elapsedTime.value++
  }, 1000)

  try {
    await modelsStore.loadModel(modelId)
    if (!modelsStore.error) {
      await syncSessionModel(modelId)
      showList.value = false
    }
  } finally {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
    loadingModel.value = null
    elapsedTime.value = 0
  }
}

async function selectRemoteModel(modelId: string) {
  const ok = await syncSessionModel(modelId)
  if (!ok) return
  modelsStore.selectModel(modelId)
  showList.value = false
}

function removeRemoteModel(model: Model) {
  pendingDeleteModel.value = model
  showDeleteModal.value = true
}

async function confirmRemoveModel() {
  const model = pendingDeleteModel.value
  if (!model?.id) return
  deleting.value = true
  try {
    await deleteModel(model.id)
    await modelsStore.fetchModels()
    showDeleteModal.value = false
  } catch (e) {
    modelsStore.error = e instanceof Error ? e.message : 'Failed to remove model'
  } finally {
    deleting.value = false
    pendingDeleteModel.value = null
  }
}
</script>

<style scoped>
.model-selector {
  padding: 1rem 1.5rem;
  position: relative;
}

.selector-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
}

.selector-trigger:hover {
  border-color: var(--accent);
}

.selector-trigger.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.current-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.model-name {
  font-weight: 600;
  font-size: 0.875rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.model-type-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.model-type-icon.local {
  color: var(--accent);
}

.model-type-icon.remote {
  color: var(--success);
}

.placeholder {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.status-badge {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-badge.loaded {
  background: rgba(16, 185, 129, 0.2);
  color: var(--success);
}

.status-badge.api {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.status-badge.loading {
  background: rgba(99, 102, 241, 0.2);
  color: var(--accent);
}

.spinner {
  width: 10px;
  height: 10px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.chevron {
  flex-shrink: 0;
  transition: transform 0.2s;
  color: var(--text-secondary);
}

.chevron.open {
  transform: rotate(180deg);
}

.model-dropdown {
  position: absolute;
  top: calc(100% - 0.5rem);
  left: 1.5rem;
  right: 1.5rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  z-index: 100;
  margin-top: 1rem;
  overflow: hidden;
}

.dropdown-header {
  padding: 0.75rem 1rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border);
}

.model-list {
  max-height: 300px;
  overflow-y: auto;
}

.model-item {
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: background 0.2s;
}

.model-item:hover {
  background: var(--bg-tertiary);
}

.model-item.active {
  background: rgba(99, 102, 241, 0.1);
}

.model-item.remote:hover {
  background: rgba(59, 130, 246, 0.1);
}

.model-section-divider {
  padding: 0.5rem 1rem;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  background: var(--bg-tertiary);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

.model-info {
  flex: 1;
  min-width: 0;
}

.model-title {
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 2px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.model-meta {
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.model-actions {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  flex-shrink: 0;
}

.delete-model-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--text-secondary);
  cursor: pointer;
  opacity: 0;
  transition: all 0.15s;
}

.model-item:hover .delete-model-btn {
  opacity: 1;
}

.delete-model-btn:hover {
  color: var(--error, #ef4444);
  background: rgba(239, 68, 68, 0.1);
}

.load-status {
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.load-status.loading-time .elapsed {
  font-size: 0.75rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.progress-bar-track {
  height: 3px;
  background: var(--bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 0.5rem;
}

.progress-bar-fill {
  height: 100%;
  width: 40%;
  background: linear-gradient(90deg, var(--accent), var(--accent-hover));
  border-radius: 2px;
  animation: indeterminate 1.4s ease-in-out infinite;
}

@keyframes indeterminate {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}

.error-toast {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(239, 68, 68, 0.1);
  color: var(--error);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

/* Transitions */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease-out;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
