/**
 * Session Store
 *
 * 管理会话状态
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listSessions, createSession, deleteSession } from '@/api/sessions'

export interface Session {
  id: string
  name: string
  model?: string
  created_at?: string
  updated_at?: string
}

export const useSessionStore = defineStore('session', () => {
  // State
  const sessions = ref<Session[]>([])
  const currentSessionId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function fetchSessions() {
    loading.value = true
    error.value = null

    try {
      sessions.value = await listSessions()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch sessions'
    } finally {
      loading.value = false
    }
  }

  async function createNewSession(params: { name?: string } = {}) {
    try {
      const session = await createSession(params)
      sessions.value.unshift(session)
      return session
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create session'
      throw e
    }
  }

  function selectSession(sessionId: string) {
    currentSessionId.value = sessionId
  }

  async function removeSession(sessionId: string) {
    try {
      await deleteSession(sessionId)
      sessions.value = sessions.value.filter(s => s.id !== sessionId)

      if (currentSessionId.value === sessionId) {
        currentSessionId.value = null
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete session'
    }
  }

  return {
    sessions,
    currentSessionId,
    loading,
    error,
    fetchSessions,
    createSession: createNewSession,
    selectSession,
    deleteSession: removeSession,
  }
})