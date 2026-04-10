/**
 * Chat Store
 *
 * 管理聊天状态
 */

import { defineStore } from 'pinia'
import { ref, watch, onUnmounted } from 'vue'
import { streamingChat } from '@/api/chat'
import type { ChatParams } from '@/api/chat'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  duration_ms?: number
}

export interface SendMessageOptions {
  temperature?: number
  max_tokens?: number
  system_prompt?: string
  context_messages?: number
}

export const useChatStore = defineStore('chat', () => {
  const currentSessionId = ref<string | null>(null)
  const messages = ref<Message[]>([])
  const isGenerating = ref(false)
  const tokenCount = ref(0)
  const error = ref<string | null>(null)
  const generatingElapsedMs = ref(0)

  let _genTimer: number | null = null
  let _genStartTime = 0

  function scheduleUiFlush(flush: () => void): Promise<void> {
    return new Promise((resolve) => {
      const requestFrame = globalThis.requestAnimationFrame
        ? globalThis.requestAnimationFrame.bind(globalThis)
        : (cb: FrameRequestCallback) => window.setTimeout(cb, 16)

      requestFrame(() => {
        flush()
        resolve()
      })
    })
  }

  watch(isGenerating, (val) => {
    if (val) {
      _genStartTime = Date.now()
      generatingElapsedMs.value = 0
      _genTimer = window.setInterval(() => {
        generatingElapsedMs.value = Date.now() - _genStartTime
      }, 100)
    } else {
      if (_genTimer) {
        clearInterval(_genTimer)
        _genTimer = null
      }
    }
  })

  async function sendMessage(content: string, options?: SendMessageOptions) {
    if (!currentSessionId.value) {
      error.value = '请先创建或选择一个会话'
      return
    }

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: Date.now()
    }

    const assistantMessage: Message = {
      id: `msg-${Date.now()}-reply`,
      role: 'assistant',
      content: '',
      timestamp: Date.now()
    }

    // Add both messages at once
    messages.value = [...messages.value, userMessage, assistantMessage]

    isGenerating.value = true
    tokenCount.value = 0
    error.value = null

    try {
      const params: ChatParams = {
        session_id: currentSessionId.value,
        message: content,
        ...options
      }

      let accumulatedContent = ''
      const assistantIndex = messages.value.length - 1
      let flushScheduled = false
      let pendingFlush: Promise<void> | null = null

      const flushAssistantContent = () => {
        const assistant = messages.value[assistantIndex]
        if (assistant) {
          assistant.content = accumulatedContent
        }
      }

      const ensureFlushScheduled = () => {
        if (flushScheduled) {
          return
        }

        flushScheduled = true
        pendingFlush = scheduleUiFlush(() => {
          flushScheduled = false
          flushAssistantContent()
        })
      }

      const result = await streamingChat(params, (token) => {
        accumulatedContent += token
        tokenCount.value++
        ensureFlushScheduled()
      })

      if (pendingFlush) {
        await pendingFlush
      } else {
        flushAssistantContent()
      }

      const durationMs = result?.durationMs || generatingElapsedMs.value
      const assistant = messages.value[assistantIndex]
      if (assistant) {
        assistant.duration_ms = durationMs
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      // Remove the empty assistant message on error
      messages.value = messages.value.filter(m => m.id !== assistantMessage.id)
    } finally {
      isGenerating.value = false
    }
  }

  function clearMessages() {
    messages.value = []
    tokenCount.value = 0
  }

  function setMessages(msgs: Message[]) {
    messages.value = msgs
  }

  function setCurrentSession(sessionId: string) {
    currentSessionId.value = sessionId
  }

  return {
    currentSessionId,
    messages,
    isGenerating,
    tokenCount,
    generatingElapsedMs,
    error,
    sendMessage,
    clearMessages,
    setMessages,
    setCurrentSession,
  }
})
