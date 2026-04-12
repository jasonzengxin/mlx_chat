<template>
  <div class="settings-view">
    <header class="settings-header">
      <router-link to="/" class="back-link">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        <span>Back to Chat</span>
      </router-link>
      <h1>Settings</h1>
    </header>

    <div class="settings-content">
      <!-- API Keys -->
      <section class="settings-section">
        <div class="section-header">
          <div class="section-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
          </div>
          <div class="section-title">
            <h2>API Keys</h2>
            <p>Manage your API keys for accessing the MLX Chat backend.</p>
          </div>
        </div>
        <ApiKeyList />
      </section>

      <!-- Remote Providers -->
      <section class="settings-section">
        <div class="section-header">
          <div class="section-icon cloud-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>
          </div>
          <div class="section-title">
            <h2>Remote Providers</h2>
            <p>Configure external API providers and add remote models. Models are independent — deleting a provider won't affect existing models.</p>
          </div>
        </div>

        <div class="providers-list">
          <div
            v-for="p in providers"
            :key="p.id"
            class="provider-card"
            :class="{ expanded: expandedId === p.id }"
          >
            <!-- Card Header -->
            <div class="provider-header" @click="toggleProvider(p.id)">
              <div class="provider-info">
                <span class="provider-name">{{ p.name }}</span>
                <span class="provider-badge" :class="p.provider_type">{{ p.provider_type }}</span>
                <span class="provider-url">{{ truncateUrl(p.base_url) }}</span>
              </div>
              <div class="header-right">
                <span v-if="p.has_api_key" class="key-status has-key" title="API key configured">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/></svg>
                </span>
                <span class="model-count">{{ countModels(p.name) }} models</span>
                <svg class="chevron" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
              </div>
            </div>

            <!-- Expanded Body -->
            <div v-if="expandedId === p.id" class="provider-body">
              <!-- Edit Form -->
              <div class="provider-form">
                <div class="form-row">
                  <div class="form-field">
                    <label>Provider Name</label>
                    <input v-model="editName" type="text" class="settings-input" placeholder="e.g. SiliconFlow" />
                  </div>
                  <div class="form-field form-field-sm">
                    <label>Type</label>
                    <select v-model="editType" class="settings-select" @change="onTypeChange">
                      <option value="custom">Custom</option>
                      <option value="openai">OpenAI</option>
                      <option value="openrouter">OpenRouter</option>
                      <option value="siliconflow">SiliconFlow</option>
                    </select>
                  </div>
                </div>
                <div class="form-field">
                  <label>Base URL</label>
                  <input v-model="editBaseUrl" type="url" class="settings-input" placeholder="https://api.openai.com/v1" />
                </div>
                <div class="form-field">
                  <label>API Key</label>
                  <div class="api-key-input">
                    <input
                      v-model="editApiKey"
                      :type="showApiKey ? 'text' : 'password'"
                      class="settings-input"
                      placeholder="sk-..."
                    />
                    <button class="toggle-visibility" @click="showApiKey = !showApiKey">
                      <svg v-if="showApiKey" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" x2="22" y1="2" y2="22"/></svg>
                      <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                    </button>
                  </div>
                </div>

                <div class="form-actions">
                  <button class="btn btn-outline" @click="runValidation(p.id)" :disabled="validating">
                    {{ validating ? 'Validating...' : 'Validate' }}
                  </button>
                  <button class="btn btn-primary" @click="saveProvider(p.id)" :disabled="saving">
                    {{ saving ? 'Saving...' : 'Save' }}
                  </button>
                  <button class="btn btn-danger-outline" @click="confirmDeleteProvider(p)">
                    Delete Provider
                  </button>
                  <span v-if="saveSuccess" class="success-msg">Saved!</span>
                </div>

                <div v-if="validationResult" class="validation-result" :class="{ ok: validationResult.valid, fail: !validationResult.valid }">
                  <span v-if="validationResult.valid">
                    Validation passed
                    <template v-if="validationResult.models_count !== null && validationResult.models_count !== undefined">
                      &middot; {{ validationResult.models_count }} models reachable
                    </template>
                  </span>
                  <span v-else>{{ validationResult.message }}</span>
                </div>
              </div>

              <!-- Models Section -->
              <div class="provider-models">
                <h4>
                  Models
                  <span class="model-count-inline">{{ providerModels.length }}</span>
                </h4>

                <div v-if="providerModels.length" class="models-list">
                  <div v-for="m in providerModels" :key="m.model_id" class="model-row">
                    <div class="model-info">
                      <span class="model-name">{{ m.name }}</span>
                      <code class="model-id">{{ m.model_id }}</code>
                    </div>
                    <button class="btn-icon btn-icon-danger" @click="confirmDeleteModel(m)" title="Remove model">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                    </button>
                  </div>
                </div>
                <p v-else class="no-models">No models added yet.</p>

                <!-- Add Model inline form -->
                <div class="add-model-section">
                  <div class="add-model-toggle" v-if="!showAddModel" @click="showAddModel = true">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
                    Add Model
                  </div>
                  <div v-if="showAddModel" class="add-model-form">
                    <div class="form-row">
                      <div class="form-field">
                        <label>Display Name</label>
                        <input v-model="newModelName" type="text" class="settings-input" placeholder="e.g. GPT-4o Mini" />
                      </div>
                      <div class="form-field">
                        <label>Model ID</label>
                        <input v-model="newModelId" type="text" class="settings-input" placeholder="e.g. openai/gpt-4o-mini" />
                      </div>
                    </div>
                    <div class="form-row">
                      <div class="form-field form-field-sm">
                        <label>Endpoint</label>
                        <input v-model="newModelEndpoint" type="text" class="settings-input" placeholder="/chat/completions" />
                      </div>
                      <div class="form-field">
                        <label>Description (optional)</label>
                        <input v-model="newModelDesc" type="text" class="settings-input" placeholder="Short note" />
                      </div>
                    </div>
                    <div class="form-actions">
                      <button class="btn btn-primary" @click="addModel(p)" :disabled="addingModel || !newModelName.trim() || !newModelId.trim()">
                        {{ addingModel ? 'Adding...' : 'Add Model' }}
                      </button>
                      <button class="btn btn-outline" @click="showAddModel = false">Cancel</button>
                      <span v-if="addModelSuccess" class="success-msg">Added!</span>
                    </div>
                    <div v-if="addModelError" class="validation-result fail">{{ addModelError }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Add Provider Button -->
          <button class="add-provider-btn" @click="openNewProviderModal">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
            <span>Add Provider</span>
          </button>
        </div>
      </section>

      <!-- Export Templates -->
      <section class="settings-section">
        <div class="section-header">
          <div class="section-icon template-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          </div>
          <div class="section-title">
            <h2>Export Templates</h2>
            <p>Manage custom templates for exporting chat sessions as knowledge base files.</p>
          </div>
        </div>

        <div class="templates-list">
          <div
            v-for="tpl in templates"
            :key="tpl.id"
            class="template-card"
            :class="{ expanded: expandedTemplateId === tpl.id }"
          >
            <div class="template-card-header" @click="toggleTemplate(tpl)">
              <div class="template-info">
                <span class="template-name">
                  {{ tpl.name }}
                  <span v-if="tpl.is_builtin" class="builtin-badge">Built-in</span>
                </span>
                <span class="template-desc">{{ tpl.description || 'No description' }}</span>
              </div>
              <div class="header-right">
                <span class="template-lang">{{ formatTemplateLang(tpl.language) }}</span>
                <svg class="chevron" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
              </div>
            </div>

            <div v-if="expandedTemplateId === tpl.id" class="template-card-body">
              <TemplateEditor v-model="editTemplateData" />

              <div class="form-actions">
                <button class="btn btn-primary" @click="saveTemplate(tpl)" :disabled="savingTemplate">
                  {{ savingTemplate ? 'Saving...' : 'Save' }}
                </button>
                <button
                  v-if="!tpl.is_builtin"
                  class="btn btn-danger-outline"
                  @click="confirmDeleteTemplate(tpl)"
                >
                  Delete
                </button>
                <span v-if="saveTemplateSuccess" class="success-msg">Saved!</span>
              </div>
              <div v-if="saveTemplateError" class="validation-result fail">{{ saveTemplateError }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Usage Statistics -->
      <section class="settings-section">
        <div class="section-header">
          <div class="section-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
          </div>
          <div class="section-title">
            <h2>Usage Statistics</h2>
            <p>Track your API usage across all sessions.</p>
          </div>
        </div>
        <UsageStats />
      </section>

      <!-- CORS Configuration -->
      <section class="settings-section">
        <div class="section-header">
          <div class="section-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/></svg>
          </div>
          <div class="section-title">
            <h2>CORS Configuration</h2>
            <p>Allowed origins for cross-origin requests. Changes require backend restart to take full effect.</p>
          </div>
        </div>

        <div class="cors-config">
          <div class="cors-origins-list">
            <div v-for="(origin, idx) in corsOrigins" :key="idx" class="cors-origin-item">
              <code>{{ origin }}</code>
              <button class="btn-icon-sm" @click="removeCorsOrigin(idx)" title="Remove">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
              </button>
            </div>
            <div v-if="corsOrigins.length === 0" class="empty-hint">No origins configured</div>
          </div>
          <div class="cors-add-row">
            <input
              v-model="newCorsOrigin"
              type="text"
              class="settings-input"
              placeholder="https://example.com"
              @keydown.enter="addCorsOrigin"
            />
            <button class="btn btn-secondary" @click="addCorsOrigin" :disabled="!newCorsOrigin.trim()">Add</button>
            <button class="btn btn-primary" @click="saveCorsOrigins" :disabled="corsSaving">
              {{ corsSaving ? 'Saving...' : 'Save' }}
            </button>
            <span v-if="corsSaveSuccess" class="success-msg">Saved!</span>
          </div>
        </div>
      </section>

      <!-- Appearance -->
      <section class="settings-section">
        <div class="section-header">
          <div class="section-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
          </div>
          <div class="section-title">
            <h2>Appearance</h2>
            <p>Customize how MLX Chat looks on your device.</p>
          </div>
        </div>
        <div class="appearance-options">
          <div class="option-item">
            <span>Theme</span>
            <select v-model="theme" class="settings-select">
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </select>
          </div>
        </div>
      </section>
    </div>

    <!-- New Provider Modal -->
    <Modal
      :show="showNewProvider"
      title="Add Remote Provider"
      @close="showNewProvider = false"
      @confirm="createNewProvider"
    >
      <div class="modal-form">
        <div class="form-field">
          <label>Provider Name</label>
          <input v-model="newProviderName" type="text" class="settings-input" placeholder="e.g. SiliconFlow" @keydown.enter="createNewProvider" />
        </div>
        <div class="form-field">
          <label>Type</label>
          <select v-model="newProviderType" class="settings-select" @change="onNewProviderTypeChange">
            <option value="custom">Custom</option>
            <option value="openai">OpenAI</option>
            <option value="openrouter">OpenRouter</option>
            <option value="siliconflow">SiliconFlow</option>
          </select>
        </div>
        <div class="form-field">
          <label>Base URL</label>
          <input v-model="newProviderBaseUrl" type="url" class="settings-input" placeholder="https://api.openai.com/v1" />
        </div>
        <div class="form-field">
          <label>API Key</label>
          <input v-model="newProviderApiKey" type="password" class="settings-input" placeholder="sk-..." />
        </div>
      </div>
      <div
        v-if="newProviderValidation"
        class="validation-result"
        :class="{ ok: newProviderValidation.valid, fail: !newProviderValidation.valid }"
        style="margin-top: 0.75rem;"
      >
        <span v-if="newProviderValidation.valid">
          Validation passed
          <template v-if="newProviderValidation.models_count != null">
            &middot; {{ newProviderValidation.models_count }} models reachable
          </template>
        </span>
        <span v-else>{{ newProviderValidation.message }}</span>
      </div>
      <div v-if="createProviderError" class="validation-result fail" style="margin-top: 0.75rem;">{{ createProviderError }}</div>
      <template #footer>
        <button class="secondary-btn" @click="showNewProvider = false">Cancel</button>
        <button class="secondary-btn" @click="validateNewProvider" :disabled="validatingNewProvider || !newProviderBaseUrl.trim() || !newProviderApiKey.trim()">
          {{ validatingNewProvider ? 'Validating...' : 'Validate' }}
        </button>
        <button class="primary-btn" @click="createNewProvider" :disabled="!newProviderName.trim() || creatingProvider">
          {{ creatingProvider ? 'Creating...' : 'Create' }}
        </button>
      </template>
    </Modal>

    <!-- Delete Provider Confirm Modal -->
    <Modal
      :show="showDeleteProviderModal"
      title="Delete Provider"
      confirmText="Delete"
      cancelText="Cancel"
      @close="showDeleteProviderModal = false"
      @confirm="doDeleteProvider"
    >
      <p>Delete provider <strong>{{ deleteTarget?.name }}</strong>?</p>
      <p class="modal-hint">Existing models added from this provider will continue to work.</p>
    </Modal>

    <!-- Delete Model Confirm Modal -->
    <Modal
      :show="showDeleteModelModal"
      title="Remove Model"
      confirmText="Remove"
      cancelText="Cancel"
      @close="showDeleteModelModal = false"
      @confirm="doDeleteModel"
    >
      <p>Remove model <strong>{{ deleteModelTarget?.name }}</strong> (<code>{{ deleteModelTarget?.model_id }}</code>)?</p>
    </Modal>

    <!-- Delete Template Confirm Modal -->
    <Modal
      :show="showDeleteTemplateModal"
      title="Delete Template"
      confirmText="Delete"
      cancelText="Cancel"
      @close="showDeleteTemplateModal = false"
      @confirm="doDeleteTemplate"
    >
      <p>Delete template <strong>{{ deleteTemplateTarget?.name }}</strong>?</p>
      <p class="modal-hint">This action cannot be undone.</p>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import ApiKeyList from '@/components/ApiKeyList.vue'
import Modal from '@/components/Modal.vue'
import UsageStats from '@/components/UsageStats.vue'
import TemplateEditor from '@/components/TemplateEditor.vue'
import {
  listProviders,
  createProvider,
  updateProvider,
  deleteProvider,
  validateProvider,
  validateCredentials,
  getSettings,
  updateSettings,
  type RemoteProvider,
  type RemoteValidationResult,
} from '@/api/settings'
import { addRemoteModel, deleteModel } from '@/api/models'
import {
  getExportTemplates,
  createExportTemplate,
  deleteExportTemplate,
  type ExportTemplate,
} from '@/api/export'
import { useModelsStore } from '@/stores/models'
import { getAuthHeaders } from '@/api/auth'

type ProviderType = 'custom' | 'openai' | 'openrouter' | 'siliconflow'

const PROVIDER_BASE_URLS: Record<Exclude<ProviderType, 'custom'>, string> = {
  openai: 'https://api.openai.com/v1',
  openrouter: 'https://openrouter.ai/api/v1',
  siliconflow: 'https://api.siliconflow.cn/v1',
}

const modelsStore = useModelsStore()
const theme = ref(localStorage.getItem('theme') || 'dark')

// ── Provider list state ──
const providers = ref<RemoteProvider[]>([])
const expandedId = ref<string | null>(null)

// ── Edit form (for expanded provider) ──
const editName = ref('')
const editType = ref<ProviderType>('custom')
const editBaseUrl = ref('')
const editApiKey = ref('')
const showApiKey = ref(false)
const saving = ref(false)
const saveSuccess = ref(false)
const validating = ref(false)
const validationResult = ref<RemoteValidationResult | null>(null)

// ── Add model form (inside expanded provider) ──
const showAddModel = ref(false)
const newModelName = ref('')
const newModelId = ref('')
const newModelEndpoint = ref('/chat/completions')
const newModelDesc = ref('')
const addingModel = ref(false)
const addModelSuccess = ref(false)
const addModelError = ref('')

// ── New provider modal ──
const showNewProvider = ref(false)
const newProviderName = ref('')
const newProviderType = ref<ProviderType>('custom')
const newProviderBaseUrl = ref('')
const newProviderApiKey = ref('')
const createProviderError = ref('')
const creatingProvider = ref(false)
const validatingNewProvider = ref(false)
const newProviderValidation = ref<RemoteValidationResult | null>(null)

// ── Delete modals ──
const showDeleteProviderModal = ref(false)
const deleteTarget = ref<RemoteProvider | null>(null)
const showDeleteModelModal = ref(false)
const deleteModelTarget = ref<{ name: string; model_id: string } | null>(null)

// ── Computed ──
const providerModels = computed(() => {
  if (!expandedId.value) return []
  const p = providers.value.find(x => x.id === expandedId.value)
  if (!p) return []
  return modelsStore.remoteModels.filter(m => m.remote_provider === p.name)
})

function countModels(providerName: string): number {
  return modelsStore.remoteModels.filter(m => m.remote_provider === providerName).length
}

function truncateUrl(url: string): string {
  if (!url) return ''
  try {
    const u = new URL(url)
    return u.hostname
  } catch {
    return url.length > 40 ? url.slice(0, 40) + '...' : url
  }
}

function inferType(baseUrl: string): ProviderType {
  const u = (baseUrl || '').toLowerCase()
  if (u.includes('openrouter.ai')) return 'openrouter'
  if (u.includes('siliconflow.cn')) return 'siliconflow'
  if (u.includes('api.openai.com')) return 'openai'
  return 'custom'
}

// ── Provider list ──
async function loadProviders() {
  try {
    providers.value = await listProviders()
  } catch (e) {
    console.error('Failed to load providers:', e)
  }
}

// ── Toggle / Expand ──
function toggleProvider(id: string) {
  if (expandedId.value === id) {
    expandedId.value = null
    return
  }
  expandedId.value = id
  const p = providers.value.find(x => x.id === id)
  if (!p) return
  editName.value = p.name
  editType.value = (p.provider_type as ProviderType) || inferType(p.base_url)
  editBaseUrl.value = p.base_url
  editApiKey.value = p.has_api_key ? '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022' : ''
  showApiKey.value = false
  validationResult.value = null
  saveSuccess.value = false

  showAddModel.value = false
  resetModelForm()
}

function onTypeChange() {
  if (editType.value !== 'custom') {
    editBaseUrl.value = PROVIDER_BASE_URLS[editType.value]
  }
}

// ── Save provider ──
async function saveProvider(id: string) {
  saving.value = true
  try {
    const data: Record<string, string> = {}
    data.name = editName.value.trim()
    data.provider_type = editType.value
    data.base_url = editBaseUrl.value.trim()
    if (editApiKey.value && !editApiKey.value.startsWith('\u2022')) {
      data.api_key = editApiKey.value
    }
    const updated = await updateProvider(id, data)
    // Refresh list
    const idx = providers.value.findIndex(p => p.id === id)
    if (idx >= 0) providers.value[idx] = updated
    saveSuccess.value = true
    setTimeout(() => { saveSuccess.value = false }, 2000)
  } catch (e) {
    console.error('Save failed:', e)
  } finally {
    saving.value = false
  }
}

// ── Validate provider ──
async function runValidation(id: string) {
  validating.value = true
  validationResult.value = null
  try {
    const overrides: Record<string, string> = {}
    if (editBaseUrl.value) overrides.base_url = editBaseUrl.value.trim()
    if (editApiKey.value && !editApiKey.value.startsWith('\u2022')) {
      overrides.api_key = editApiKey.value
    }
    validationResult.value = await validateProvider(id, overrides)
  } catch (e) {
    validationResult.value = {
      valid: false,
      status_code: null,
      message: e instanceof Error ? e.message : 'Validation failed',
      models_count: null,
      base_url: editBaseUrl.value,
    }
  } finally {
    validating.value = false
  }
}

// ── Delete provider ──
function confirmDeleteProvider(p: RemoteProvider) {
  deleteTarget.value = p
  showDeleteProviderModal.value = true
}

async function doDeleteProvider() {
  if (!deleteTarget.value) return
  try {
    await deleteProvider(deleteTarget.value.id)
    providers.value = providers.value.filter(p => p.id !== deleteTarget.value!.id)
    if (expandedId.value === deleteTarget.value.id) expandedId.value = null
  } catch (e) {
    console.error('Delete failed:', e)
  }
  showDeleteProviderModal.value = false
  deleteTarget.value = null
}

// ── Add model ──
function resetModelForm() {
  newModelName.value = ''
  newModelId.value = ''
  newModelEndpoint.value = '/chat/completions'
  newModelDesc.value = ''
  addModelError.value = ''
  addModelSuccess.value = false
}

async function addModel(provider: RemoteProvider) {
  addingModel.value = true
  addModelError.value = ''
  try {
    await addRemoteModel({
      name: newModelName.value.trim(),
      model_id: newModelId.value.trim(),
      endpoint: newModelEndpoint.value.trim() || '/chat/completions',
      description: newModelDesc.value.trim(),
      provider_id: provider.id,
      remote_provider: provider.name,
    })
    await modelsStore.fetchModels()
    addModelSuccess.value = true
    setTimeout(() => { addModelSuccess.value = false }, 2000)
    resetModelForm()
    showAddModel.value = false
  } catch (e) {
    addModelError.value = e instanceof Error ? e.message : 'Failed to add model'
  } finally {
    addingModel.value = false
  }
}

// ── Delete model ──
function confirmDeleteModel(m: { name: string; model_id: string }) {
  deleteModelTarget.value = m
  showDeleteModelModal.value = true
}

async function doDeleteModel() {
  if (!deleteModelTarget.value) return
  try {
    await deleteModel(deleteModelTarget.value.model_id)
    await modelsStore.fetchModels()
  } catch (e) {
    console.error('Delete model failed:', e)
  }
  showDeleteModelModal.value = false
  deleteModelTarget.value = null
}

// ── New provider modal ──
function openNewProviderModal() {
  newProviderName.value = ''
  newProviderType.value = 'custom'
  newProviderBaseUrl.value = ''
  newProviderApiKey.value = ''
  createProviderError.value = ''
  newProviderValidation.value = null
  creatingProvider.value = false
  validatingNewProvider.value = false
  showNewProvider.value = true
}

function onNewProviderTypeChange() {
  if (newProviderType.value !== 'custom') {
    newProviderBaseUrl.value = PROVIDER_BASE_URLS[newProviderType.value]
    if (!newProviderName.value.trim()) {
      const labels: Record<string, string> = {
        openai: 'OpenAI',
        openrouter: 'OpenRouter',
        siliconflow: 'SiliconFlow',
      }
      newProviderName.value = labels[newProviderType.value] || ''
    }
  }
}

async function validateNewProvider() {
  validatingNewProvider.value = true
  newProviderValidation.value = null
  createProviderError.value = ''
  try {
    newProviderValidation.value = await validateCredentials({
      base_url: newProviderBaseUrl.value.trim(),
      api_key: newProviderApiKey.value,
    })
  } catch (e) {
    newProviderValidation.value = {
      valid: false,
      status_code: null,
      message: e instanceof Error ? e.message : 'Validation failed',
      models_count: null,
      base_url: newProviderBaseUrl.value,
    }
  } finally {
    validatingNewProvider.value = false
  }
}

async function createNewProvider() {
  const name = newProviderName.value.trim()
  if (!name) return
  createProviderError.value = ''
  creatingProvider.value = true
  try {
    const created = await createProvider({
      name,
      provider_type: newProviderType.value,
      base_url: newProviderBaseUrl.value.trim(),
      api_key: newProviderApiKey.value,
    })
    providers.value.push(created)
    showNewProvider.value = false
    expandedId.value = created.id
    toggleProvider(created.id)
  } catch (e) {
    const raw = e instanceof Error ? e.message : 'Failed to create provider'
    try {
      const parsed = JSON.parse(raw)
      createProviderError.value = parsed.detail || raw
    } catch {
      createProviderError.value = raw
    }
  } finally {
    creatingProvider.value = false
  }
}

// ── Export Templates state ──
const templates = ref<ExportTemplate[]>([])
const expandedTemplateId = ref<string | null>(null)
const editTemplateData = ref({
  name: '',
  description: '',
  language: 'both',
  system_prompt: '',
  template_content: '',
})
const savingTemplate = ref(false)
const saveTemplateSuccess = ref(false)
const saveTemplateError = ref('')
const showDeleteTemplateModal = ref(false)
const deleteTemplateTarget = ref<ExportTemplate | null>(null)

function formatTemplateLang(lang: string): string {
  if (lang === 'both') return 'CN / EN'
  if (lang === 'zh') return 'CN'
  return 'EN'
}

async function loadTemplates() {
  try {
    templates.value = await getExportTemplates()
  } catch (e) {
    console.error('Failed to load templates:', e)
  }
}

function toggleTemplate(tpl: ExportTemplate) {
  if (expandedTemplateId.value === tpl.id) {
    expandedTemplateId.value = null
    return
  }
  expandedTemplateId.value = tpl.id
  editTemplateData.value = {
    name: tpl.name,
    description: tpl.description,
    language: tpl.language,
    system_prompt: tpl.system_prompt,
    template_content: tpl.template_content,
  }
  saveTemplateSuccess.value = false
  saveTemplateError.value = ''
}

async function saveTemplate(tpl: ExportTemplate) {
  savingTemplate.value = true
  saveTemplateError.value = ''
  try {
    if (tpl.is_builtin) {
      // Built-in templates can't be saved via API, but we allow editing UI to view them
      saveTemplateError.value = 'Built-in templates cannot be modified'
      return
    }

    // Use createExportTemplate for new, but since we only have editing here,
    // we call the PATCH endpoint via the export API
    const response = await fetch(`/api/v1/export/templates/${tpl.id}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        name: editTemplateData.value.name,
        description: editTemplateData.value.description,
        language: editTemplateData.value.language,
        system_prompt: editTemplateData.value.system_prompt,
        template_content: editTemplateData.value.template_content,
      }),
    })
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Failed to save template')
    }

    await loadTemplates()
    saveTemplateSuccess.value = true
    setTimeout(() => { saveTemplateSuccess.value = false }, 2000)
  } catch (e) {
    saveTemplateError.value = e instanceof Error ? e.message : 'Failed to save'
  } finally {
    savingTemplate.value = false
  }
}

function confirmDeleteTemplate(tpl: ExportTemplate) {
  deleteTemplateTarget.value = tpl
  showDeleteTemplateModal.value = true
}

async function doDeleteTemplate() {
  if (!deleteTemplateTarget.value) return
  try {
    await deleteExportTemplate(deleteTemplateTarget.value.id)
    await loadTemplates()
    if (expandedTemplateId.value === deleteTemplateTarget.value.id) {
      expandedTemplateId.value = null
    }
  } catch (e) {
    console.error('Delete template failed:', e)
  }
  showDeleteTemplateModal.value = false
  deleteTemplateTarget.value = null
}

// ── CORS state ──
const corsOrigins = ref<string[]>([])
const newCorsOrigin = ref('')
const corsSaving = ref(false)
const corsSaveSuccess = ref(false)

async function loadCorsOrigins() {
  try {
    const settings = await getSettings()
    corsOrigins.value = settings.cors_allow_origins || []
  } catch { /* ignore */ }
}

function addCorsOrigin() {
  const origin = newCorsOrigin.value.trim().replace(/\/+$/, '')
  if (!origin) return
  if (corsOrigins.value.includes(origin)) { newCorsOrigin.value = ''; return }
  corsOrigins.value = [...corsOrigins.value, origin]
  newCorsOrigin.value = ''
}

function removeCorsOrigin(index: number) {
  corsOrigins.value = corsOrigins.value.filter((_, i) => i !== index)
}

async function saveCorsOrigins() {
  corsSaving.value = true
  corsSaveSuccess.value = false
  try {
    await updateSettings({ cors_allow_origins: corsOrigins.value })
    corsSaveSuccess.value = true
    setTimeout(() => { corsSaveSuccess.value = false }, 2000)
  } catch { /* ignore */ }
  finally { corsSaving.value = false }
}

// ── Lifecycle ──
onMounted(async () => {
  document.documentElement.setAttribute('data-theme', theme.value)
  await Promise.all([loadProviders(), modelsStore.fetchModels(), loadTemplates(), loadCorsOrigins()])
})

watch(theme, (v) => {
  localStorage.setItem('theme', v)
  document.documentElement.setAttribute('data-theme', v)
})
</script>

<style scoped>
.settings-view {
  min-height: 100vh;
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.settings-header {
  max-width: 800px;
  margin: 0 auto;
  padding: 3rem 1.5rem 2rem;
}

.back-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
  margin-bottom: 1rem;
  transition: color 0.2s;
}
.back-link:hover { color: var(--accent); }

.settings-header h1 {
  font-size: 2rem;
  font-weight: 700;
}

.settings-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 1.5rem 4rem;
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section-header {
  display: flex;
  gap: 1rem;
}

.section-icon {
  width: 40px;
  height: 40px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  flex-shrink: 0;
}
.section-icon.cloud-icon { color: #3b82f6; }
.section-icon.template-icon { color: #f59e0b; }

.section-title h2 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}
.section-title p {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

/* ── Providers ── */
.providers-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.provider-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color 0.2s;
}
.provider-card:hover { border-color: color-mix(in srgb, var(--border) 60%, var(--accent)); }
.provider-card.expanded { border-color: var(--accent); }

.provider-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  cursor: pointer;
  user-select: none;
}

.provider-info {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  min-width: 0;
}

.provider-name {
  font-weight: 600;
  font-size: 0.95rem;
  white-space: nowrap;
}

.provider-badge {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  white-space: nowrap;
}
.provider-badge.openai { background: rgba(16, 163, 127, 0.12); color: #10a37f; }
.provider-badge.openrouter { background: rgba(99, 102, 241, 0.12); color: #6366f1; }
.provider-badge.siliconflow { background: rgba(59, 130, 246, 0.12); color: #3b82f6; }

.provider-url {
  color: var(--text-secondary);
  font-size: 0.8rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.key-status.has-key { color: var(--success, #10b981); }

.model-count {
  font-size: 0.8rem;
  color: var(--text-secondary);
  white-space: nowrap;
}

.chevron {
  transition: transform 0.2s;
  color: var(--text-secondary);
}
.provider-card.expanded .chevron { transform: rotate(180deg); }

/* ── Provider Body (expanded) ── */
.provider-body {
  border-top: 1px solid var(--border);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.provider-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  flex: 1;
}
.form-field-sm { flex: 0 0 160px; }

.form-field label {
  font-weight: 600;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.settings-input {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.2s;
  width: 100%;
  box-sizing: border-box;
}
.settings-input:focus { border-color: var(--accent); }
.settings-input::placeholder { color: var(--text-secondary); }

.settings-select {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  outline: none;
  cursor: pointer;
  width: 100%;
  box-sizing: border-box;
}
.settings-select:focus { border-color: var(--accent); }

.api-key-input {
  display: flex;
  gap: 0.5rem;
}
.api-key-input .settings-input { flex: 1; }

.toggle-visibility {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 0.5rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.toggle-visibility:hover { color: var(--text-primary); }

/* ── Buttons ── */
.form-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
}
.btn-primary:hover:not(:disabled) { filter: brightness(1.1); }

.btn-outline {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border);
}
.btn-outline:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }

.btn-danger-outline {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
}
.btn-danger-outline:hover:not(:disabled) {
  border-color: var(--error, #ef4444);
  color: var(--error, #ef4444);
  background: rgba(239, 68, 68, 0.06);
}

.btn-icon {
  padding: 0.375rem;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-icon-danger:hover { color: var(--error, #ef4444); background: rgba(239, 68, 68, 0.08); }

.success-msg {
  color: var(--success, #10b981);
  font-size: 0.8rem;
  font-weight: 500;
}

.validation-result {
  font-size: 0.82rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-md);
}
.validation-result.ok { color: var(--success, #10b981); background: rgba(16, 185, 129, 0.06); }
.validation-result.fail { color: var(--error, #ef4444); background: rgba(239, 68, 68, 0.06); }

/* ── Models inside provider ── */
.provider-models {
  border-top: 1px dashed var(--border);
  padding-top: 1rem;
}

.provider-models h4 {
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0 0 0.75rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.model-count-inline {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 1px 6px;
  background: var(--bg-tertiary);
  border-radius: 10px;
  color: var(--text-secondary);
}

.models-list {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-bottom: 0.75rem;
}

.model-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.model-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.model-name {
  font-weight: 500;
  font-size: 0.85rem;
  white-space: nowrap;
}

.model-id {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.75rem;
  color: var(--text-secondary);
  background: var(--bg-primary);
  padding: 1px 6px;
  border-radius: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.no-models {
  color: var(--text-secondary);
  font-size: 0.82rem;
  margin: 0 0 0.75rem 0;
}

/* ── Add model toggle / form ── */
.add-model-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s;
}
.add-model-toggle:hover { color: var(--accent); }

.add-model-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

/* ── Add provider button ── */
.add-provider-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.875rem;
  background: transparent;
  border: 1px dashed var(--border);
  border-radius: var(--radius-lg);
  color: var(--text-primary);
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}
.add-provider-btn:hover {
  border-style: solid;
  border-color: var(--accent);
  background: rgba(99, 102, 241, 0.05);
  color: var(--accent);
}

/* ── CORS Configuration ── */
.cors-config {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.cors-origins-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.cors-origin-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}

.cors-origin-item code {
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 0.8125rem;
  color: var(--accent);
}

.btn-icon-sm {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  transition: color 0.15s, background 0.15s;
}
.btn-icon-sm:hover {
  color: var(--error);
  background: var(--bg-primary);
}

.empty-hint {
  font-size: 0.8rem;
  color: var(--text-secondary);
  opacity: 0.6;
  padding: 0.5rem 0;
}

.cors-add-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.cors-add-row .settings-input {
  flex: 1;
  min-width: 0;
}
.cors-add-row .btn {
  white-space: nowrap;
}

.success-msg {
  font-size: 0.8rem;
  color: var(--success, #22c55e);
  font-weight: 500;
}

/* ── Appearance ── */
.appearance-options {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
}
.option-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.option-item .settings-select { width: auto; }

/* ── Modal ── */
.modal-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.modal-hint {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.82rem;
}

/* ── Export Templates ── */
.templates-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.template-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color 0.2s;
}
.template-card:hover { border-color: color-mix(in srgb, var(--border) 60%, var(--accent)); }
.template-card.expanded { border-color: var(--accent); }

.template-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  cursor: pointer;
  user-select: none;
}

.template-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.template-name {
  font-weight: 600;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.builtin-badge {
  font-size: 0.625rem;
  padding: 1px 6px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  color: var(--text-secondary);
  font-weight: 500;
}

.template-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.template-lang {
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
}

.template-card-body {
  border-top: 1px solid var(--border);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
