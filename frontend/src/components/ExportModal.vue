<template>
  <Modal :show="show" :title="ui.title" size="lg" @close="handleClose">
    <div class="export-modal">
      <!-- Step 1: Select template -->
      <div v-if="step === 'select'" class="step-content">
        <div class="form-group">
          <label>{{ ui.template }}</label>
          <div v-if="loadingTemplates" class="loading-text">
            <span class="spinner"></span>
            {{ ui.loadingTemplates }}
          </div>
          <div v-else-if="templates.length === 0" class="empty-state">
            <p>{{ ui.noTemplates }}</p>
            <p class="hint">{{ ui.noTemplatesHint }}</p>
          </div>
          <div v-else class="template-list">
            <div
              v-for="tpl in templates"
              :key="tpl.id"
              class="template-card"
              :class="{ selected: selectedTemplateId === tpl.id }"
              @click="selectedTemplateId = tpl.id"
            >
              <div class="template-name">
                <span class="builtin-badge" v-if="tpl.is_builtin">{{ ui.builtin }}</span>
                {{ tpl.name }}
              </div>
              <div class="template-desc">{{ tpl.description }}</div>
              <div class="template-lang">{{ formatLanguage(tpl.language) }}</div>
            </div>
          </div>
        </div>

        <div class="form-group" v-if="templates.length > 0">
          <label>{{ ui.outputLanguage }}</label>
          <div class="radio-group">
            <label class="radio-label" :class="{ active: language === 'zh' }">
              <input type="radio" v-model="language" value="zh" />
              {{ ui.langChinese }}
            </label>
            <label class="radio-label" :class="{ active: language === 'en' }">
              <input type="radio" v-model="language" value="en" />
              {{ ui.langEnglish }}
            </label>
          </div>
        </div>
      </div>

      <!-- Step 2: Confirm -->
      <div v-if="step === 'confirm'" class="step-content">
        <div v-if="estimate" class="estimate-info">
          <div class="info-row">
            <span class="info-label">{{ ui.messages }}</span>
            <span class="info-value">{{ estimate.message_count }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">{{ ui.estimatedTokens }}</span>
            <span class="info-value">~{{ estimate.estimated_tokens.toLocaleString() }}</span>
          </div>
          <div class="warning-box" v-if="estimate.is_remote && estimate.warning">
            {{ estimate.warning }}
          </div>
        </div>
        <div v-else class="loading-text">
          <span class="spinner"></span>
          {{ ui.estimating }}
        </div>
      </div>

      <!-- Step 3: Generating -->
      <div v-if="step === 'generating'" class="step-content">
        <div class="progress-section">
          <div class="progress-header">
            <span class="progress-label">{{ ui.generating }}</span>
            <span class="progress-stats">
              {{ generatedChars.toLocaleString() }}{{ ui.charsShort }}
              <template v-if="estimatedTotalChars > 0">
                {{ ui.charsSlashApprox }}{{ estimatedTotalChars.toLocaleString() }}
              </template>
            </span>
          </div>
          <div class="progress-track">
            <div
              class="progress-fill"
              :class="{ indeterminate: progressPercent <= 0 }"
              :style="progressPercent > 0 ? { width: Math.min(progressPercent, 100) + '%' } : {}"
            ></div>
          </div>
          <div class="progress-footer">
            <span class="elapsed-time">{{ formatDuration(elapsedMs) }}</span>
            <span v-if="charsPerSec > 0" class="speed">{{ charsPerSec }}{{ ui.charsPerSec }}</span>
          </div>
        </div>

        <div class="preview-wrap">
          <div class="preview-caption">
            <span>{{ ui.livePreview }}</span>
            <span class="preview-hint">{{ ui.previewHint }}</span>
          </div>
          <div class="preview-area" aria-live="polite">
            <pre v-if="previewContent.length > 0" class="preview-content">{{ previewTail }}<span class="cursor-blink">|</span></pre>
            <div v-else class="preview-placeholder">
              <p>{{ ui.previewWait }}</p>
              <p class="preview-placeholder-sub">{{ ui.previewExplain }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 4: Done -->
      <div v-if="step === 'done'" class="step-content">
        <div class="done-banner">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>
          <div class="done-text">
            <strong>{{ ui.exportComplete }}</strong>
            <span class="done-stats">
              {{ previewContent.length.toLocaleString() }}{{ ui.doneStatsMid }}{{ formatDuration(finalDurationMs) }}
            </span>
          </div>
        </div>

        <div class="action-buttons">
          <button class="action-btn-primary" @click="downloadContent(previewContent)">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
            {{ ui.downloadMd }}
          </button>
          <button class="action-btn-secondary" @click="copyToClipboard">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
            {{ copied ? ui.copied : ui.copy }}
          </button>
        </div>

        <div class="preview-area">
          <pre class="preview-content">{{ previewContent }}</pre>
        </div>
      </div>

      <!-- Error -->
      <div v-if="step === 'error'" class="step-content">
        <div class="error-msg">{{ errorMessage }}</div>
      </div>
    </div>

    <template #footer>
      <button
        v-if="step === 'generating'"
        class="danger-btn"
        @click="cancelGeneration"
      >
        {{ ui.cancelExport }}
      </button>
      <button
        v-else
        class="secondary-btn"
        @click="handleClose"
      >
        {{ ui.close }}
      </button>

      <button
        v-if="step === 'select'"
        class="primary-btn"
        :disabled="!selectedTemplateId"
        @click="handleEstimate"
      >
        {{ ui.next }}
      </button>
      <button
        v-if="step === 'confirm'"
        class="secondary-btn"
        @click="step = 'select'"
      >
        {{ ui.back }}
      </button>
      <button
        v-if="step === 'confirm'"
        class="primary-btn"
        :disabled="!estimate"
        @click="handleGenerate"
      >
        {{ ui.startExport }}
      </button>
      <button
        v-if="step === 'error'"
        class="primary-btn"
        @click="retryGeneration"
      >
        {{ ui.retry }}
      </button>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import Modal from './Modal.vue'
import {
  getExportTemplates,
  estimateExport,
  streamingExport,
  type ExportTemplate,
  type ExportEstimate,
} from '@/api/export'

const props = defineProps<{
  show: boolean
  sessionId: string
  sessionName: string
}>()

const emit = defineEmits<{
  close: []
}>()

/** Modal chrome + labels follow the selected output language (zh / en). */
const UI_TEXT = {
  zh: {
    title: '导出为知识库',
    template: '模板',
    loadingTemplates: '正在加载模板…',
    noTemplates: '尚未配置导出模板。',
    noTemplatesHint: '请到「设置」中添加导出模板。',
    builtin: '内置',
    outputLanguage: '输出语言',
    langChinese: '中文',
    langEnglish: '英文',
    messages: '消息条数',
    estimatedTokens: '预估 Tokens',
    estimating: '正在估算…',
    generating: '正在生成…',
    charsShort: ' 字符',
    charsSlashApprox: ' / 约 ',
    charsPerSec: ' 字符/秒',
    livePreview: '实时预览',
    previewHint: '只读，随模型输出流式刷新',
    previewWait: '正在等待模型输出首段文字…',
    previewExplain: '此处展示生成的 Markdown，不是输入框，无需在此输入。',
    exportComplete: '导出完成！',
    doneStatsMid: ' 字符，用时 ',
    downloadMd: '下载 .md',
    copy: '复制',
    copied: '已复制！',
    cancelExport: '取消导出',
    close: '关闭',
    next: '下一步',
    back: '上一步',
    startExport: '开始导出',
    retry: '重试',
    errLoadTemplates: '加载模板失败',
    errEstimate: '估算失败',
    errExport: '导出失败',
  },
  en: {
    title: 'Export as Knowledge Base',
    template: 'Template',
    loadingTemplates: 'Loading templates…',
    noTemplates: 'No export templates configured.',
    noTemplatesHint: 'Go to Settings to add export templates.',
    builtin: 'Built-in',
    outputLanguage: 'Output language',
    langChinese: 'Chinese',
    langEnglish: 'English',
    messages: 'Messages',
    estimatedTokens: 'Estimated tokens',
    estimating: 'Estimating…',
    generating: 'Generating…',
    charsShort: ' chars',
    charsSlashApprox: ' / ~',
    charsPerSec: ' chars/s',
    livePreview: 'Live preview',
    previewHint: 'read-only, streams as the model writes',
    previewWait: 'Waiting for the first characters from the model…',
    previewExplain: 'This area shows the Markdown as it is generated. It is not a text field — you do not type here.',
    exportComplete: 'Export complete!',
    doneStatsMid: ' chars in ',
    downloadMd: 'Download .md',
    copy: 'Copy',
    copied: 'Copied!',
    cancelExport: 'Cancel export',
    close: 'Close',
    next: 'Next',
    back: 'Back',
    startExport: 'Start export',
    retry: 'Retry',
    errLoadTemplates: 'Failed to load templates',
    errEstimate: 'Failed to estimate',
    errExport: 'Export failed',
  },
} as const

type Step = 'select' | 'confirm' | 'generating' | 'done' | 'error'

const step = ref<Step>('select')
const templates = ref<ExportTemplate[]>([])
const loadingTemplates = ref(false)
const selectedTemplateId = ref<string | null>(null)
const language = ref('zh')

const ui = computed(() => UI_TEXT[language.value === 'zh' ? 'zh' : 'en'])
const estimate = ref<ExportEstimate | null>(null)
const previewContent = ref('')
const errorMessage = ref('')
const copied = ref(false)
const generatedChars = ref(0)
const elapsedMs = ref(0)
const finalDurationMs = ref(0)
let abortController: AbortController | null = null
let elapsedTimer: number | null = null
let elapsedStart = 0

const estimatedTotalChars = computed(() => {
  if (!estimate.value) return 0
  return estimate.value.estimated_tokens * 3
})

const progressPercent = computed(() => {
  if (estimatedTotalChars.value <= 0) return 0
  return Math.round((generatedChars.value / estimatedTotalChars.value) * 100)
})

const charsPerSec = computed(() => {
  if (elapsedMs.value < 1000 || generatedChars.value < 10) return 0
  return Math.round(generatedChars.value / (elapsedMs.value / 1000))
})

const PREVIEW_TAIL_LIMIT = 2000
const previewTail = computed(() => {
  const content = previewContent.value
  if (content.length <= PREVIEW_TAIL_LIMIT) return content
  return '...\n' + content.slice(-PREVIEW_TAIL_LIMIT)
})

watch(() => props.show, async (val) => {
  if (val) {
    resetState()
    await loadTemplates()
  }
})

onUnmounted(() => stopElapsedTimer())

function resetState() {
  step.value = 'select'
  selectedTemplateId.value = null
  language.value = 'zh'
  estimate.value = null
  previewContent.value = ''
  errorMessage.value = ''
  generatedChars.value = 0
  elapsedMs.value = 0
  finalDurationMs.value = 0
  copied.value = false
}

function startElapsedTimer() {
  elapsedStart = Date.now()
  elapsedMs.value = 0
  elapsedTimer = window.setInterval(() => {
    elapsedMs.value = Date.now() - elapsedStart
  }, 200)
}

function stopElapsedTimer() {
  if (elapsedTimer) {
    clearInterval(elapsedTimer)
    elapsedTimer = null
  }
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  const secs = Math.floor(ms / 1000)
  const mins = Math.floor(secs / 60)
  const remainSecs = secs % 60
  if (mins > 0) return `${mins}m ${remainSecs}s`
  return `${secs}s`
}

async function loadTemplates() {
  loadingTemplates.value = true
  try {
    templates.value = await getExportTemplates()
    if (templates.value.length === 1) {
      selectedTemplateId.value = templates.value[0].id
    }
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : ui.value.errLoadTemplates
    step.value = 'error'
  } finally {
    loadingTemplates.value = false
  }
}

function formatLanguage(lang: string): string {
  const zhUi = language.value === 'zh'
  if (lang === 'both') return zhUi ? '中英' : 'CN / EN'
  if (lang === 'zh') return zhUi ? '中文' : 'Chinese'
  return zhUi ? '英文' : 'English'
}

async function handleEstimate() {
  if (!selectedTemplateId.value) return
  step.value = 'confirm'

  try {
    estimate.value = await estimateExport(
      props.sessionId,
      selectedTemplateId.value,
      language.value
    )
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : ui.value.errEstimate
    step.value = 'error'
  }
}

async function handleGenerate() {
  if (!selectedTemplateId.value) return
  step.value = 'generating'
  previewContent.value = ''
  generatedChars.value = 0

  abortController = new AbortController()
  startElapsedTimer()

  try {
    const result = await streamingExport(
      props.sessionId,
      selectedTemplateId.value,
      language.value,
      (token) => {
        previewContent.value += token
        generatedChars.value += token.length
      },
      abortController.signal
    )

    if (result.content) {
      previewContent.value = result.content
      generatedChars.value = result.content.length
    }

    finalDurationMs.value = result.duration_ms || elapsedMs.value
    step.value = 'done'
  } catch (e) {
    if ((e as Error).name === 'AbortError') {
      step.value = 'select'
      return
    }
    errorMessage.value = e instanceof Error ? e.message : ui.value.errExport
    step.value = 'error'
  } finally {
    stopElapsedTimer()
    abortController = null
  }
}

function cancelGeneration() {
  abortController?.abort()
  stopElapsedTimer()
  step.value = 'select'
  previewContent.value = ''
}

function retryGeneration() {
  step.value = 'confirm'
  errorMessage.value = ''
}

function downloadContent(content: string) {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.sessionName || 'export'}-knowledge-base.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(previewContent.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    downloadContent(previewContent.value)
  }
}

function handleClose() {
  if (step.value === 'generating') return
  abortController?.abort()
  stopElapsedTimer()
  emit('close')
}
</script>

<style scoped>
.export-modal {
  min-height: 200px;
}

.step-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group > label {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.template-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.template-card {
  padding: 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.template-card:hover {
  border-color: var(--accent);
}

.template-card.selected {
  border-color: var(--accent);
  background: rgba(99, 102, 241, 0.08);
}

.template-name {
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
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
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
}

.template-lang {
  font-size: 0.6875rem;
  color: var(--text-secondary);
  opacity: 0.7;
}

.radio-group {
  display: flex;
  gap: 1rem;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.radio-label:hover {
  border-color: var(--accent);
}

.radio-label.active {
  border-color: var(--accent);
  background: rgba(99, 102, 241, 0.08);
}

.radio-label input {
  accent-color: var(--accent);
}

/* Estimate info */
.estimate-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);
}

.info-label {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.info-value {
  font-weight: 600;
  font-size: 0.875rem;
}

.warning-box {
  padding: 0.75rem;
  background: rgba(234, 179, 8, 0.1);
  border: 1px solid rgba(234, 179, 8, 0.3);
  border-radius: var(--radius-md);
  color: #ca8a04;
  font-size: 0.8125rem;
}

/* Loading & empty */
.loading-text {
  color: var(--text-secondary);
  font-size: 0.875rem;
  text-align: center;
  padding: 2rem 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.empty-state {
  text-align: center;
  padding: 2rem 0;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.empty-state .hint {
  font-size: 0.75rem;
  margin-top: 0.5rem;
  opacity: 0.7;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Progress */
.progress-section {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-label {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.progress-label::before {
  content: '';
  width: 10px;
  height: 10px;
  border: 2px solid var(--accent);
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.progress-stats {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.progress-track {
  height: 6px;
  background: var(--bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #818cf8);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-fill.indeterminate {
  width: 40%;
  animation: indeterminate 1.4s ease-in-out infinite;
}

@keyframes indeterminate {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}

.progress-footer {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.elapsed-time {
  font-variant-numeric: tabular-nums;
}

.speed {
  font-variant-numeric: tabular-nums;
}

/* Done banner */
.done-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: var(--radius-md);
  color: #22c55e;
}

.done-text {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.done-text strong {
  font-size: 0.9375rem;
}

.done-stats {
  font-size: 0.75rem;
  opacity: 0.8;
}

/* Action buttons */
.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.action-btn-primary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s;
}

.action-btn-primary:hover {
  background: var(--accent-hover, #5153d4);
}

.action-btn-secondary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn-secondary:hover {
  border-color: var(--accent);
}

/* Preview (read-only stream, not an input) */
.preview-wrap {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.preview-caption {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.preview-hint {
  font-weight: 500;
  text-transform: none;
  letter-spacing: normal;
  color: var(--text-secondary);
  opacity: 0.75;
  font-size: 0.6875rem;
}

.preview-area {
  max-height: 280px;
  min-height: 120px;
  overflow-y: auto;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1rem;
  cursor: default;
  user-select: text;
}

.preview-placeholder {
  margin: 0;
  padding: 0.5rem 0;
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.5;
}

.preview-placeholder p {
  margin: 0 0 0.5rem 0;
}

.preview-placeholder-sub {
  font-size: 0.8125rem !important;
  opacity: 0.85;
}

.preview-content {
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 0.8125rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  color: var(--text-primary);
}

.cursor-blink {
  animation: blink 1s step-end infinite;
  color: var(--accent);
}

@keyframes blink {
  50% { opacity: 0; }
}

/* Error */
.error-msg {
  color: var(--error);
  font-size: 0.875rem;
  padding: 0.75rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius-md);
}

/* Footer buttons */
.primary-btn {
  background-color: var(--accent);
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
}

.primary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.secondary-btn {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border);
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
}

.danger-btn {
  background-color: var(--error, #ef4444);
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
}

.danger-btn:hover {
  background-color: #dc2626;
}
</style>
