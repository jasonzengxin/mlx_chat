<template>
  <div class="template-editor">
    <div class="form-group">
      <label>Template Name</label>
      <input
        v-model="name"
        type="text"
        class="settings-input"
        placeholder="e.g. My Study Notes"
        @input="emitUpdate"
      />
    </div>

    <div class="form-group">
      <label>Description</label>
      <input
        v-model="description"
        type="text"
        class="settings-input"
        placeholder="Brief description of this template"
        @input="emitUpdate"
      />
    </div>

    <div class="form-group">
      <label>Language Support</label>
      <select v-model="language" class="settings-select" @change="emitUpdate">
        <option value="both">Chinese / English</option>
        <option value="zh">Chinese Only</option>
        <option value="en">English Only</option>
      </select>
    </div>

    <div class="form-group">
      <div class="label-row">
        <label>System Prompt</label>
        <span class="label-hint">Instructions for the AI</span>
      </div>
      <textarea
        v-model="systemPrompt"
        class="settings-textarea"
        rows="5"
        placeholder="指导 AI 如何填充模板的提示词，例如：&#10;请根据提供的对话内容，整理成一份学习笔记..."
        @input="emitUpdate"
      ></textarea>
    </div>

    <div class="form-group">
      <div class="label-row">
        <label>Template Content</label>
        <span class="label-hint">Markdown template with placeholders</span>
      </div>
      <textarea
        v-model="templateContent"
        class="settings-textarea template-textarea"
        rows="18"
        placeholder="# {{session_name}} - 学习笔记&#10;&#10;## 概述&#10;{{核心要点总结}}&#10;&#10;## 详细内容&#10;{{按主题整理的内容}}"
        @input="emitUpdate"
      ></textarea>
    </div>

    <!-- Placeholder Reference -->
    <div class="placeholder-ref">
      <div class="ref-header" @click="showRef = !showRef">
        <span>Available Placeholders</span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          :style="{ transform: showRef ? 'rotate(180deg)' : 'none' }"
        >
          <path d="m6 9 6 6 6-6"/>
        </svg>
      </div>
      <div v-if="showRef" class="ref-content">
        <div class="ref-item" @click="insertPlaceholder('{{session_name}}')">
          <code>{{session_name}}</code>
          <span>Session name</span>
        </div>
        <div class="ref-item" @click="insertPlaceholder('{{export_date}}')">
          <code>{{export_date}}</code>
          <span>Export date</span>
        </div>
        <div class="ref-item" @click="insertPlaceholder('{{message_count}}')">
          <code>{{message_count}}</code>
          <span>Number of messages</span>
        </div>
        <div class="ref-item" @click="insertPlaceholder('{{content}}')">
          <code>{{content}}</code>
          <span>AI-generated summary content</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue: {
    name: string
    description: string
    language: string
    system_prompt: string
    template_content: string
  }
}>()

const emit = defineEmits<{
  'update:modelValue': [value: typeof props.modelValue]
}>()

const name = ref(props.modelValue.name || '')
const description = ref(props.modelValue.description || '')
const language = ref(props.modelValue.language || 'both')
const systemPrompt = ref(props.modelValue.system_prompt || '')
const templateContent = ref(props.modelValue.template_content || '')
const showRef = ref(false)

watch(() => props.modelValue, (val) => {
  name.value = val.name
  description.value = val.description
  language.value = val.language
  systemPrompt.value = val.system_prompt
  templateContent.value = val.template_content
}, { immediate: true })

function emitUpdate() {
  emit('update:modelValue', {
    name: name.value,
    description: description.value,
    language: language.value,
    system_prompt: systemPrompt.value,
    template_content: templateContent.value,
  })
}

function insertPlaceholder(placeholder: string) {
  templateContent.value += placeholder
  emitUpdate()
}
</script>

<style scoped>
.template-editor {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group > label,
.label-row > label {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.label-hint {
  font-size: 0.75rem;
  color: var(--text-secondary);
  opacity: 0.7;
  font-weight: 400;
}

.settings-input,
.settings-select,
.settings-textarea {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 0.625rem 0.875rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.2s;
  width: 100%;
  box-sizing: border-box;
  font-family: inherit;
}
.settings-input:focus,
.settings-select:focus,
.settings-textarea:focus {
  border-color: var(--accent);
}
.settings-input::placeholder,
.settings-textarea::placeholder {
  color: var(--text-secondary);
  opacity: 0.6;
}

.settings-textarea {
  resize: vertical;
  min-height: 100px;
  line-height: 1.6;
}

.template-textarea {
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 0.8125rem;
  min-height: 280px;
}

/* Placeholder Reference */
.placeholder-ref {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.ref-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.625rem 0.875rem;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
  transition: color 0.2s;
}
.ref-header:hover { color: var(--text-primary); }
.ref-header svg { transition: transform 0.2s; }

.ref-content {
  border-top: 1px solid var(--border);
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.ref-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.375rem 0.5rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.15s;
}
.ref-item:hover { background: var(--bg-primary); }

.ref-item code {
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 0.75rem;
  background: var(--bg-primary);
  padding: 2px 6px;
  border-radius: 3px;
  color: var(--accent);
  min-width: 140px;
}

.ref-item span {
  font-size: 0.75rem;
  color: var(--text-secondary);
}
</style>
