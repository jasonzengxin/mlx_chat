<template>
  <transition name="slide">
    <div v-if="show" class="parameter-panel">
      <div class="panel-header">
        <h3>Parameters</h3>
        <button class="close-btn" @click="$emit('close')" title="Close">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
      </div>

      <div class="panel-content">
        <!-- Temperature -->
        <div class="param-group">
          <label class="param-label">
            <span>Temperature</span>
            <span class="param-value">{{ temperature.toFixed(1) }}</span>
          </label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            :value="temperature"
            @input="onTemperatureChange"
            class="slider"
          />
          <div class="param-hint">Controls randomness. Lower = more focused, Higher = more creative.</div>
        </div>

        <!-- Max Tokens -->
        <div class="param-group">
          <label class="param-label">
            <span>Max Tokens</span>
            <span class="param-value">{{ maxTokens }}</span>
          </label>
          <input
            type="number"
            min="1"
            max="8192"
            :value="maxTokens"
            @input="onMaxTokensChange"
            class="input-field"
          />
          <div class="param-hint">Maximum number of tokens to generate.</div>
        </div>

        <!-- System Prompt -->
        <div class="param-group">
          <label class="param-label">
            <span>System Prompt</span>
            <button
              v-if="systemPrompt"
              class="clear-btn"
              @click="onClearSystemPrompt"
              title="Clear"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </button>
          </label>
          <textarea
            :value="systemPrompt"
            @input="onSystemPromptChange"
            placeholder="Enter a system prompt to customize the assistant's behavior..."
            class="textarea-field"
            rows="4"
          />
          <div class="param-hint">Optional instructions to guide the model's responses.</div>
        </div>
      </div>

      <div class="panel-footer">
        <button class="reset-btn" @click="onReset" title="Reset to defaults">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
          <span>Reset</span>
        </button>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'

const props = defineProps<{
  show: boolean
  temperature: number
  maxTokens: number
  systemPrompt: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update:temperature', value: number): void
  (e: 'update:maxTokens', value: number): void
  (e: 'update:systemPrompt', value: string): void
}>()

function onTemperatureChange(e: Event) {
  const value = parseFloat((e.target as HTMLInputElement).value)
  emit('update:temperature', value)
}

function onMaxTokensChange(e: Event) {
  const value = parseInt((e.target as HTMLInputElement).value) || 1
  const clamped = Math.min(8192, Math.max(1, value))
  emit('update:maxTokens', clamped)
}

function onSystemPromptChange(e: Event) {
  emit('update:systemPrompt', (e.target as HTMLTextAreaElement).value)
}

function onClearSystemPrompt() {
  emit('update:systemPrompt', '')
}

function onReset() {
  emit('update:temperature', 0.7)
  emit('update:maxTokens', 4096)
  emit('update:systemPrompt', '')
}
</script>

<style scoped>
.parameter-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 320px;
  height: 100%;
  background: var(--bg-secondary);
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  z-index: 20;
  box-shadow: var(--shadow);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
}

.panel-header h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  display: flex;
  border-radius: var(--radius-sm);
  transition: all 0.15s;
}

.close-btn:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.param-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.param-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.param-value {
  font-family: monospace;
  color: var(--accent);
  font-size: 0.875rem;
  font-weight: 600;
}

.slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: var(--bg-tertiary);
  appearance: none;
  cursor: pointer;
}

.slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  transition: transform 0.15s;
}

.slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  border: none;
}

.input-field {
  width: 100%;
  padding: 0.625rem 0.875rem;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 0.875rem;
  font-family: monospace;
  outline: none;
  transition: border-color 0.15s;
}

.input-field:focus {
  border-color: var(--accent);
}

.textarea-field {
  width: 100%;
  padding: 0.625rem 0.875rem;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 0.875rem;
  font-family: inherit;
  line-height: 1.5;
  resize: vertical;
  min-height: 80px;
  max-height: 200px;
  outline: none;
  transition: border-color 0.15s;
}

.textarea-field:focus {
  border-color: var(--accent);
}

.textarea-field::placeholder {
  color: var(--text-secondary);
}

.param-hint {
  font-size: 0.7rem;
  color: var(--text-secondary);
  line-height: 1.4;
  opacity: 0.8;
}

.clear-btn {
  background: var(--bg-tertiary);
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 3px;
  display: flex;
  border-radius: 4px;
  transition: all 0.15s;
}

.clear-btn:hover {
  color: var(--error);
  background: rgba(239, 68, 68, 0.1);
}

.panel-footer {
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border);
}

.reset-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.625rem;
  background: transparent;
  border: 1px dashed var(--border);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(99, 102, 241, 0.05);
}

/* Transitions */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s ease-out, opacity 0.25s ease-out;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
