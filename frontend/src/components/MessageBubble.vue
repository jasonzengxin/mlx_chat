<template>
  <div class="message-wrapper" :class="message.role">
    <div class="message-avatar">
      <template v-if="message.role === 'user'">U</template>
      <template v-else>
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
      </template>
    </div>
    <div class="message-container">
      <div class="message-bubble" :class="message.role">
        <!-- Thinking Process Block -->
        <div v-if="parsed.thought" class="thought-container">
          <div class="thought-header" @click="showThought = !showThought">
            <svg 
              :style="{ transform: showThought ? 'rotate(90deg)' : 'rotate(0deg)' }"
              style="transition: transform 0.2s"
              xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            >
              <path d="m9 18 6-6-6-6"/>
            </svg>
            <span>Thinking Process</span>
          </div>
          <transition name="expand">
            <div v-if="showThought" class="thought-content">
              {{ parsed.thought }}
            </div>
          </transition>
        </div>

        <!-- Waiting / Thinking State (no content yet) -->
        <div v-if="isStreaming && !parsed.content" class="thinking-state">
          <div class="thinking-dots">
            <span></span><span></span><span></span>
          </div>
          <div class="thinking-label">Thinking...</div>
        </div>

        <!-- Main Answer Content -->
        <div
          v-else-if="message.role === 'assistant'"
          class="content markdown-body"
          v-html="renderedContent"
        ></div>
        <div v-else class="content content-plain">{{ parsed.content }}</div>

        <!-- Streaming cursor -->
        <span v-if="isStreaming && parsed.content" class="streaming-cursor"></span>
      </div>
      <div class="message-meta">
        <span>{{ message.role === 'user' ? 'You' : 'Assistant' }}</span>
        <span v-if="isStreaming" class="gen-badge">
          {{ formatElapsed(elapsedMs) }}
          <template v-if="tokenCount > 0">
            &middot; {{ tokenCount }} tokens
          </template>
          <template v-if="tokPerSec > 0">
            &middot; {{ tokPerSec }} tok/s
          </template>
        </span>
        <span v-else-if="message.duration_ms" class="duration-badge">
          {{ formatDuration(message.duration_ms) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'

marked.setOptions({
  breaks: true,
  gfm: true,
})

const props = withDefaults(defineProps<{
  message: {
    id: string
    role: string
    content: string
    duration_ms?: number
  }
  isStreaming?: boolean
  elapsedMs?: number
  tokenCount?: number
  tokPerSec?: number
}>(), {
  isStreaming: false,
  elapsedMs: 0,
  tokenCount: 0,
  tokPerSec: 0,
})

const showThought = ref(false)

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  const seconds = ms / 1000
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const mins = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return `${mins}m ${secs}s`
}

function formatElapsed(ms: number): string {
  const totalSec = Math.floor(ms / 1000)
  const mins = Math.floor(totalSec / 60)
  const secs = totalSec % 60
  if (mins > 0) return `${mins}:${secs.toString().padStart(2, '0')}`
  return `${secs}s`
}

const parsed = computed(() => {
  let text = props.message.content || ''
  let thought = null
  let content = text

  const endTagIndex = text.toLowerCase().lastIndexOf('</think>')
  const startTagIndex = text.toLowerCase().indexOf('<thought>')
  
  if (endTagIndex !== -1) {
    const startOffset = startTagIndex !== -1 ? startTagIndex + 9 : 0
    thought = text.substring(startOffset, endTagIndex).trim()
    content = text.substring(endTagIndex + 8).trim()
  } 
  else if (text.startsWith('Thinking Process:')) {
    const lastGapIndex = text.lastIndexOf('\n\n')
    if (lastGapIndex !== -1 && lastGapIndex > 20) {
      thought = text.substring(0, lastGapIndex).replace(/^Thinking Process:\s*/i, '').trim()
      content = text.substring(lastGapIndex).trim()
    } else {
      const lines = text.split('\n')
      if (lines.length > 2) {
        content = lines.pop() || ''
        thought = lines.join('\n').replace(/^Thinking Process:\s*/i, '').trim()
      }
    }
  }

  if (content.startsWith('Thinking Process:') && !thought) {
    return { thought: null, content: text }
  }

  return { 
    thought: thought || null, 
    content: content || text 
  }
})

const renderedContent = computed(() => {
  const raw = parsed.value.content
  if (!raw) return ''
  try {
    return marked.parse(raw) as string
  } catch {
    return raw
  }
})
</script>

<style scoped>
.message-wrapper {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  max-width: 85%;
}

.message-wrapper.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.875rem;
  font-weight: 600;
}

.user .message-avatar {
  background: var(--accent);
  color: white;
}

.assistant .message-avatar {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.message-container {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  min-width: 0;
}

.user .message-container {
  align-items: flex-end;
}

.message-bubble {
  padding: 0.875rem 1.125rem;
  border-radius: var(--radius-lg);
  font-size: 0.9375rem;
  line-height: 1.6;
  box-shadow: var(--shadow-sm);
}

.message-bubble.user {
  background: var(--accent);
  color: white;
  border-bottom-right-radius: 2px;
}

.message-bubble.assistant {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-bottom-left-radius: 2px;
  border: 1px solid var(--border);
}

/* Thinking Process */
.thought-container {
  margin-bottom: 0.75rem;
  border-bottom: 1px dashed var(--border);
  padding-bottom: 0.75rem;
}

.thought-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.thought-header:hover {
  color: var(--accent);
}

.thought-content {
  margin-top: 0.75rem;
  padding: 0.75rem 1rem;
  background: rgba(0, 0, 0, 0.15);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-style: italic;
  font-size: 0.85rem;
  line-height: 1.6;
  white-space: pre-wrap;
}

[data-theme="light"] .thought-content {
  background: rgba(0, 0, 0, 0.04);
  border-left-color: var(--border);
}

/* Thinking / Waiting State */
.thinking-state {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.25rem 0;
}

.thinking-dots {
  display: flex;
  gap: 4px;
}

.thinking-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  opacity: 0.4;
  animation: thinking-bounce 1.4s ease-in-out infinite;
}

.thinking-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes thinking-bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.3;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.thinking-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  animation: thinking-pulse 2s ease-in-out infinite;
}

@keyframes thinking-pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

/* Streaming cursor */
.streaming-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--accent);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: cursor-blink 0.8s step-end infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.content-plain {
  white-space: pre-wrap;
  word-break: break-word;
}

.message-meta {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.duration-badge,
.gen-badge {
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-variant-numeric: tabular-nums;
}

.gen-badge {
  background: rgba(99, 102, 241, 0.12);
  color: var(--accent);
}

:root[data-theme="light"] .message-meta {
  color: #475569;
}

/* Expand/Collapse Animation */
.expand-enter-active, .expand-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  max-height: 2000px;
}

.expand-enter-from, .expand-leave-to {
  max-height: 0;
  opacity: 0;
  margin-top: 0;
  padding-top: 0;
  padding-bottom: 0;
}
</style>

<!-- Unscoped styles for v-html markdown content -->
<style>
.markdown-body {
  word-break: break-word;
  overflow-wrap: break-word;
}

.markdown-body > *:first-child {
  margin-top: 0;
}

.markdown-body > *:last-child {
  margin-bottom: 0;
}

.markdown-body p {
  margin: 0.5em 0;
  line-height: 1.6;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin: 1em 0 0.5em;
  font-weight: 600;
  line-height: 1.3;
}

.markdown-body h1 { font-size: 1.4em; }
.markdown-body h2 { font-size: 1.25em; }
.markdown-body h3 { font-size: 1.1em; }

.markdown-body ul,
.markdown-body ol {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.markdown-body li {
  margin: 0.25em 0;
}

.markdown-body li > p {
  margin: 0.25em 0;
}

.markdown-body blockquote {
  margin: 0.75em 0;
  padding: 0.5em 1em;
  border-left: 3px solid var(--accent);
  background: rgba(99, 102, 241, 0.06);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  color: var(--text-secondary);
}

.markdown-body blockquote p {
  margin: 0.25em 0;
}

.markdown-body code {
  font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', 'Cascadia Code', Consolas, monospace;
  font-size: 0.85em;
  padding: 0.15em 0.4em;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 4px;
}

:root[data-theme="light"] .markdown-body code {
  background: rgba(0, 0, 0, 0.06);
}

.markdown-body pre {
  margin: 0.75em 0;
  padding: 1em;
  background: #1e1e2e;
  border-radius: var(--radius-md);
  overflow-x: auto;
  border: 1px solid var(--border);
}

:root[data-theme="light"] .markdown-body pre {
  background: #f6f8fa;
}

.markdown-body pre code {
  padding: 0;
  background: transparent;
  font-size: 0.85em;
  line-height: 1.6;
  color: #e2e8f0;
}

:root[data-theme="light"] .markdown-body pre code {
  color: #24292e;
}

.markdown-body hr {
  margin: 1em 0;
  border: none;
  border-top: 1px solid var(--border);
}

.markdown-body a {
  color: var(--accent);
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body strong {
  font-weight: 700;
}

.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.75em 0;
  font-size: 0.9em;
}

.markdown-body th,
.markdown-body td {
  padding: 0.5em 0.75em;
  border: 1px solid var(--border);
  text-align: left;
}

.markdown-body th {
  background: var(--bg-tertiary);
  font-weight: 600;
}

.markdown-body tr:nth-child(even) {
  background: rgba(0, 0, 0, 0.03);
}

.markdown-body img {
  max-width: 100%;
  border-radius: var(--radius-md);
}
</style>
