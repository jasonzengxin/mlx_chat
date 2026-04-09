/**
 * Chat Store
 *
 * 管理聊天状态
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { streamingChat } from '@/api/chat'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
}

export const useChatStore = defineStore('chat', () => {
  // State
  const currentSessionId = ref<string | null>(null)
  const messages = ref<Message[]>([])
  const isGenerating = ref(false)
  const tokenCount = ref(0)
  const error = ref<string | null>(null)

  // Actions
  async function sendMessage(content: string) {
    if (!currentSessionId.value) return

    // 添加用户消息
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: Date.now(),
    }
    messages.value.push(userMessage)

    // 准备助手消息
    const assistantMessage: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    }
    messages.value.push(assistantMessage)

    // 开始生成
    isGenerating.value = true
    tokenCount.value = 0
    error.value = null

    try {
      await streamingChat(
        {
          session_id: currentSessionId.value,
          message: content,
        },
        (token: string) => {
          assistantMessage.content += token
          tokenCount.value++
        }
      )
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
    } finally {
      isGenerating.value = false
    }
  }

  function clearMessages() {
    messages.value = []
    tokenCount.value = 0
  }

  function setCurrentSession(sessionId: string) {
    currentSessionId.value = sessionId
  }

  return {
    // State
    currentSessionId,
    messages,
    isGenerating,
    tokenCount,
    error,
    // Actions
    sendMessage,
    clearMessages,
    setCurrentSession,
  }
})