/**
 * Chat Store 测试
 *
 * 测试内容:
 * - 状态初始化
 * - 消息发送
 * - 流式输出
 * - 错误处理
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'

// Mock API
const mockStreamingChat = vi.fn()

vi.mock('@/api/chat', () => ({
  streamingChat: (...args: unknown[]) => mockStreamingChat(...args),
}))

describe('useChatStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('初始消息为空', () => {
      const store = useChatStore()

      expect(store.messages).toEqual([])
    })

    it('初始 isGenerating 为 false', () => {
      const store = useChatStore()

      expect(store.isGenerating).toBe(false)
    })

    it('初始 tokenCount 为 0', () => {
      const store = useChatStore()

      expect(store.tokenCount).toBe(0)
    })

    it('初始 error 为 null', () => {
      const store = useChatStore()

      expect(store.error).toBeNull()
    })
  })

  describe('sendMessage', () => {
    it('发送消息后添加用户消息', async () => {
      const store = useChatStore()
      store.currentSessionId = 'test-session'

      mockStreamingChat.mockImplementation(async (params, onToken) => {
        onToken('你')
        onToken('好')
      })

      await store.sendMessage('你好')

      const userMessages = store.messages.filter(m => m.role === 'user')
      expect(userMessages.length).toBe(1)
      expect(userMessages[0].content).toBe('你好')
    })

    it('发送消息后 isGenerating 变为 true', async () => {
      const store = useChatStore()
      store.currentSessionId = 'test-session'

      mockStreamingChat.mockImplementation(async () => {
        // 模拟延迟
        await new Promise(resolve => setTimeout(resolve, 100))
      })

      const promise = store.sendMessage('test')

      expect(store.isGenerating).toBe(true)

      await promise

      expect(store.isGenerating).toBe(false)
    })

    it('添加助手响应消息', async () => {
      const store = useChatStore()
      store.currentSessionId = 'test-session'

      mockStreamingChat.mockImplementation(async (params, onToken) => {
        onToken('你')
        onToken('好')
      })

      await store.sendMessage('你好')

      const assistantMessages = store.messages.filter(m => m.role === 'assistant')
      expect(assistantMessages.length).toBe(1)
      expect(assistantMessages[0].content).toBe('你好')
    })

    it('正确计数生成的 token', async () => {
      const store = useChatStore()
      store.currentSessionId = 'test-session'

      mockStreamingChat.mockImplementation(async (params, onToken) => {
        onToken('你')
        onToken('好')
        onToken('！')
      })

      await store.sendMessage('test')

      expect(store.tokenCount).toBe(3)
    })

    it('错误时设置 error 状态', async () => {
      const store = useChatStore()
      store.currentSessionId = 'test-session'

      mockStreamingChat.mockRejectedValue(new Error('网络错误'))

      await store.sendMessage('test')

      expect(store.error).toBe('网络错误')
      expect(store.isGenerating).toBe(false)
    })
  })

  describe('clearMessages', () => {
    it('清空消息列表', () => {
      const store = useChatStore()

      // 添加一些消息
      store.messages = [
        { id: '1', role: 'user', content: 'hello', timestamp: Date.now() },
        { id: '2', role: 'assistant', content: 'hi', timestamp: Date.now() },
      ]

      store.clearMessages()

      expect(store.messages).toHaveLength(0)
    })
  })

  describe('setCurrentSession', () => {
    it('设置当前会话 ID', () => {
      const store = useChatStore()

      store.setCurrentSession('session-123')

      expect(store.currentSessionId).toBe('session-123')
    })
  })
})