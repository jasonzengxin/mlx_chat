/**
 * Session Store 测试
 *
 * 测试内容:
 * - 会话列表
 * - 会话创建
 * - 会话切换
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSessionStore } from '@/stores/session'

// Mock API
const mockListSessions = vi.fn()
const mockCreateSession = vi.fn()
const mockDeleteSession = vi.fn()

vi.mock('@/api/sessions', () => ({
  listSessions: () => mockListSessions(),
  createSession: (...args: unknown[]) => mockCreateSession(...args),
  deleteSession: (...args: unknown[]) => mockDeleteSession(...args),
}))

describe('useSessionStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('初始会话列表为空', () => {
      const store = useSessionStore()

      expect(store.sessions).toEqual([])
    })

    it('初始 currentSessionId 为 null', () => {
      const store = useSessionStore()

      expect(store.currentSessionId).toBeNull()
    })
  })

  describe('fetchSessions', () => {
    it('获取会话列表', async () => {
      const store = useSessionStore()

      mockListSessions.mockResolvedValue([
        { id: '1', name: 'Session 1' },
        { id: '2', name: 'Session 2' },
      ])

      await store.fetchSessions()

      expect(store.sessions.length).toBe(2)
      expect(store.sessions[0].name).toBe('Session 1')
    })

    it('获取失败时设置 error', async () => {
      const store = useSessionStore()

      mockListSessions.mockRejectedValue(new Error('Failed'))

      await store.fetchSessions()

      expect(store.error).toBe('Failed')
    })
  })

  describe('createSession', () => {
    it('创建新会话', async () => {
      const store = useSessionStore()

      mockCreateSession.mockResolvedValue({
        id: 'new-id',
        name: 'New Session',
      })

      const result = await store.createSession({ name: 'New Session' })

      expect(result.id).toBe('new-id')
    })

    it('创建后添加到列表', async () => {
      const store = useSessionStore()

      mockCreateSession.mockResolvedValue({
        id: 'new-id',
        name: 'New Session',
      })

      await store.createSession({ name: 'New Session' })

      expect(store.sessions.some(s => s.id === 'new-id')).toBe(true)
    })
  })

  describe('selectSession', () => {
    it('选择会话', () => {
      const store = useSessionStore()

      store.selectSession('session-123')

      expect(store.currentSessionId).toBe('session-123')
    })
  })

  describe('deleteSession', () => {
    it('删除会话', async () => {
      const store = useSessionStore()

      store.sessions = [
        { id: '1', name: 'Session 1' },
        { id: '2', name: 'Session 2' },
      ]

      mockDeleteSession.mockResolvedValue(true)

      await store.deleteSession('1')

      expect(store.sessions.length).toBe(1)
      expect(store.sessions[0].id).toBe('2')
    })

    it('删除当前会话时清除 currentSessionId', async () => {
      const store = useSessionStore()

      store.sessions = [
        { id: '1', name: 'Session 1' },
      ]
      store.currentSessionId = '1'

      mockDeleteSession.mockResolvedValue(true)

      await store.deleteSession('1')

      expect(store.currentSessionId).toBeNull()
    })
  })
})