/**
 * 设置 Store 测试
 *
 * 测试内容:
 * - API Key 管理
 * - 主题切换
 * - 设置持久化
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSettingsStore } from '@/stores/settings'

// Mock API
const mockListApiKeys = vi.fn()
const mockCreateApiKey = vi.fn()
const mockDeleteApiKey = vi.fn()

vi.mock('@/api/settings', () => ({
  listApiKeys: () => mockListApiKeys(),
  createApiKey: (...args: unknown[]) => mockCreateApiKey(...args),
  deleteApiKey: (...args: unknown[]) => mockDeleteApiKey(...args),
}))

describe('useSettingsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('初始主题为 dark', () => {
      const store = useSettingsStore()

      expect(store.theme).toBe('dark')
    })

    it('初始 apiKeys 为空', () => {
      const store = useSettingsStore()

      expect(store.apiKeys).toEqual([])
    })
  })

  describe('fetchApiKeys', () => {
    it('获取 API Keys', async () => {
      const store = useSettingsStore()

      mockListApiKeys.mockResolvedValue({
        keys: [
          { id: '1', name: 'Key 1', key_prefix: 'sk-abc123' },
          { id: '2', name: 'Key 2', key_prefix: 'sk-def456' },
        ]
      })

      await store.fetchApiKeys()

      expect(store.apiKeys.length).toBe(2)
    })
  })

  describe('createApiKey', () => {
    it('创建 API Key', async () => {
      const store = useSettingsStore()

      mockCreateApiKey.mockResolvedValue({
        id: 'new-id',
        name: 'New Key',
        key: 'sk-full-key-here',
      })

      const result = await store.createApiKey('New Key')

      expect(result.key).toBe('sk-full-key-here')
    })

    it('创建后添加到列表', async () => {
      const store = useSettingsStore()

      mockCreateApiKey.mockResolvedValue({
        id: 'new-id',
        name: 'New Key',
        key_prefix: 'sk-xxx',
      })

      await store.createApiKey('New Key')

      expect(store.apiKeys.some(k => k.id === 'new-id')).toBe(true)
    })
  })

  describe('deleteApiKey', () => {
    it('删除 API Key', async () => {
      const store = useSettingsStore()

      store.apiKeys = [
        { id: '1', name: 'Key 1' },
        { id: '2', name: 'Key 2' },
      ]

      mockDeleteApiKey.mockResolvedValue(true)

      await store.deleteApiKey('1')

      expect(store.apiKeys.length).toBe(1)
    })
  })

  describe('toggleTheme', () => {
    it('切换主题', () => {
      const store = useSettingsStore()

      expect(store.theme).toBe('dark')

      store.toggleTheme()

      expect(store.theme).toBe('light')

      store.toggleTheme()

      expect(store.theme).toBe('dark')
    })
  })
})