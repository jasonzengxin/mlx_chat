/**
 * Session Store
 *
 * 管理会话状态
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listSessions, createSession, deleteSession, deleteAllSessions as deleteAllSessionsApi, getSession, updateSession } from '@/api/sessions'
import { useChatStore } from './chat'
import { useModelsStore } from './models'

export interface Session {
  id: string
  name: string
  model?: string
  temperature?: number
  max_tokens?: number
  system_prompt?: string
  context_messages?: number
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

  async function createNewSession(params: { name?: string; model?: string } = {}) {
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

  async function deleteAllSessions() {
    loading.value = true
    error.value = null

    try {
      const result = await deleteAllSessionsApi()
      sessions.value = []
      currentSessionId.value = null

      // Clear chat store
      const chatStore = useChatStore()
      chatStore.clearMessages()
      chatStore.setCurrentSession('')

      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete all sessions'
      return null
    } finally {
      loading.value = false
    }
  }

  async function selectSession(id: string) {
    currentSessionId.value = id
    await loadSessionMessages(id)
  }

  async function loadSessionMessages(sessionId: string) {
    const chatStore = useChatStore()
    chatStore.setCurrentSession(sessionId)
    chatStore.clearMessages()

    try {
      const sessionData = await getSession(sessionId)
      if (sessionData && sessionData.messages) {
        const messages = sessionData.messages.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          timestamp: new Date(m.created_at).getTime(),
          duration_ms: m.duration_ms
        }))
        chatStore.setMessages(messages)
      }

      // Restore model selection from session
      if (sessionData?.model && sessionData.model !== 'default') {
        const modelsStore = useModelsStore()
        const model = modelsStore.models.find(m => m.model_id === sessionData.model)
        if (model) {
          modelsStore.selectModel(model.model_id)
        }
      }
    } catch (e) {
      console.error('Failed to load session messages:', e)
    }
  }

  async function updateSessionById(id: string, params: Partial<Session>) {
    try {
      const updated = await updateSession(id, params)
      const idx = sessions.value.findIndex(s => s.id === id)
      if (idx !== -1) {
        sessions.value[idx] = { ...sessions.value[idx], ...updated }
      }
      return updated
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update session'
      return null
    }
  }

  function updateChatStore() {
    const chatStore = useChatStore()
    if (currentSessionId.value) {
      chatStore.setCurrentSession(currentSessionId.value)
      chatStore.clearMessages()
    }
  }

  function getCurrentSession(): Session | undefined {
    return sessions.value.find(s => s.id === currentSessionId.value)
  }

  return {
    sessions,
    currentSessionId,
    loading,
    error,
    fetchSessions,
    createSession: createNewSession,
    deleteSession: deleteSessionById,
    deleteAllSessions,
    selectSession,
    updateSession: updateSessionById,
    getCurrentSession,
  }
})
