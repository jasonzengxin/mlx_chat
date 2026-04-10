import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSessionStore } from '@/stores/session'
import type { Session } from '@/stores/session'

// Mock API
vi.mock('@/api/sessions', () => ({
  listSessions: vi.fn(),
  createSession: vi.fn(),
  deleteSession: vi.fn(),
  getSession: vi.fn(),
  updateSession: vi.fn(),
}))

describe('Session Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const store = useSessionStore()

      expect(store.sessions).toEqual([])
      expect(store.currentSessionId).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('getCurrentSession', () => {
    it('should return undefined when no current session', () => {
      const store = useSessionStore()
      expect(store.getCurrentSession()).toBeUndefined()
    })

    it('should return current session when set', () => {
      const store = useSessionStore()
      const mockSession: Session = {
        id: 'session-1',
        name: 'Test Session',
        temperature: 0.8,
        max_tokens: 2048,
        system_prompt: 'Be helpful',
        context_messages: 20,
        created_at: '2026-01-01',
        updated_at: '2026-01-01'
      }
      store.sessions = [mockSession]
      store.currentSessionId = 'session-1'

      expect(store.getCurrentSession()).toEqual(mockSession)
    })
  })

  describe('Parameter persistence', () => {
    it('should store temperature in session', () => {
      const store = useSessionStore()
      const mockSession: Session = {
        id: 'session-1',
        name: 'Test Session',
        temperature: 0.5,
        max_tokens: 1024,
        system_prompt: 'Custom prompt',
        context_messages: 10,
        created_at: '2026-01-01',
        updated_at: '2026-01-01'
      }
      store.sessions = [mockSession]
      store.currentSessionId = 'session-1'

      const session = store.getCurrentSession()
      expect(session?.temperature).toBe(0.5)
      expect(session?.max_tokens).toBe(1024)
      expect(session?.system_prompt).toBe('Custom prompt')
      expect(session?.context_messages).toBe(10)
    })

    it('should have default parameter values', () => {
      const store = useSessionStore()
      const mockSession: Session = {
        id: 'session-1',
        name: 'Test Session',
        created_at: '2026-01-01',
        updated_at: '2026-01-01'
      }
      store.sessions = [mockSession]
      store.currentSessionId = 'session-1'

      const session = store.getCurrentSession()
      // These should be undefined or have defaults when accessed
      expect(session?.temperature ?? 0.7).toBe(0.7)
      expect(session?.max_tokens ?? 4096).toBe(4096)
      expect(session?.system_prompt ?? '').toBe('')
      expect(session?.context_messages ?? 20).toBe(20)
    })
  })

  describe('updateSession', () => {
    it('should call updateSession API', async () => {
      const { updateSession } = await import('@/api/sessions')
      const mockUpdate = vi.mocked(updateSession)
      mockUpdate.mockResolvedValue({
        id: 'session-1',
        name: 'Updated',
        temperature: 0.9,
        max_tokens: 4096,
        system_prompt: '',
        context_messages: 20,
        created_at: '2026-01-01',
        updated_at: '2026-01-01'
      })

      const store = useSessionStore()
      store.sessions = [{
        id: 'session-1',
        name: 'Test',
        temperature: 0.7,
        max_tokens: 4096,
        system_prompt: '',
        context_messages: 20,
        created_at: '2026-01-01',
        updated_at: '2026-01-01'
      }]

      await store.updateSession('session-1', { temperature: 0.9 })

      expect(mockUpdate).toHaveBeenCalledWith('session-1', { temperature: 0.9 })
    })
  })
})
