/**
 * Session Store
 *
 * 管理会话状态
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listSessions, createSession, deleteSession } from '@/api/sessions'
import { useChatStore } from './chat'

export interface Session {
  id: string
  name: string
  model?: string
  temperature?: number
  max_tokens?: number
  system_prompt?: string
  created_at: string
  updated_at: string
}

export const useSessionStore = defineStore('session', () => {
  const sessions = ref<Session[]>([])
  const currentSessionId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchSessions() {
    loading.value = true
    error.value = null

    try {
      sessions.value = await listSessions()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch sessions'
      sessions.value = []
    } finally {
      loading.value = false
    }
  }

  async function createNewSession(params: { name?: string } = {}) {
    loading.value = true
    error.value = null

    try {
      const session = await createSession(params)
      sessions.value.unshift(session)
      selectSession(session.id)
      return session
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create session'
      return null
    } finally {
      loading.value = false
    }
  }

  async function deleteSessionById(id: string) {
    try {
      await deleteSession(id)
      sessions.value = sessions.value.filter(s => s.id !== id)

      if (currentSessionId.value === id) {
        currentSessionId.value = sessions.value[0]?.id || null
        updateChatStore()
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete session'
    }
  }

  function selectSession(id: string) {
    currentSessionId.value = id
    updateChatStore()
  }

  function updateChatStore() {
    const chatStore = useChatStore()
    if (currentSessionId.value) {
      chatStore.setCurrentSession(currentSessionId.value)
      chatStore.clearMessages()
    }
  }

  return {
    sessions,
    currentSessionId,
    loading,
    error,
    fetchSessions,
    createSession: createNewSession,
    deleteSession: deleteSessionById,
    selectSession,
  }
})
