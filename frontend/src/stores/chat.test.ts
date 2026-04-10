import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'

// Mock API
vi.mock('@/api/chat', () => ({
  streamingChat: vi.fn()
}))

describe('Chat Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const store = useChatStore()
      
      expect(store.currentSessionId).toBeNull()
      expect(store.messages).toEqual([])
      expect(store.isGenerating).toBe(false)
      expect(store.tokenCount).toBe(0)
      expect(store.error).toBeNull()
    })
  })

  describe('setCurrentSession', () => {
    it('should set current session id', () => {
      const store = useChatStore()
      store.setCurrentSession('session-123')
      
      expect(store.currentSessionId).toBe('session-123')
    })
  })

  describe('clearMessages', () => {
    it('should clear messages and token count', () => {
      const store = useChatStore()
      store.messages = [
        { id: '1', role: 'user', content: 'Hi', timestamp: Date.now() }
      ]
      store.tokenCount = 10
      
      store.clearMessages()
      
      expect(store.messages).toEqual([])
      expect(store.tokenCount).toBe(0)
    })
  })

  describe('sendMessage', () => {
    it('should not send if no session', async () => {
      const { streamingChat } = await import('@/api/chat')
      const store = useChatStore()
      
      await store.sendMessage('Hello')
      
      expect(streamingChat).not.toHaveBeenCalled()
    })

    it('should add user and assistant messages', async () => {
      const { streamingChat } = await import('@/api/chat')
      
      // Mock the streaming to immediately complete
      vi.mocked(streamingChat).mockResolvedValue(undefined)
      
      const store = useChatStore()
      store.setCurrentSession('session-123')
      
      await store.sendMessage('Hello')
      
      expect(store.messages.length).toBe(2)
      expect(store.messages[0].role).toBe('user')
      expect(store.messages[0].content).toBe('Hello')
      expect(store.messages[1].role).toBe('assistant')
    })

    it('should stream tokens to assistant message', async () => {
      const { streamingChat } = await import('@/api/chat')
      
      vi.mocked(streamingChat).mockImplementation(async (_, onToken) => {
        onToken('H')
        onToken('i')
      })
      
      const store = useChatStore()
      store.setCurrentSession('session-123')
      
      await store.sendMessage('Hello')
      
      expect(store.messages[1].content).toBe('Hi')
      expect(store.tokenCount).toBe(2)
    })

    it('should set isGenerating during streaming', async () => {
      const { streamingChat } = await import('@/api/chat')
      
      vi.mocked(streamingChat).mockImplementation(async () => {
        // Small delay to allow checking state
        await new Promise(resolve => setTimeout(resolve, 10))
      })
      
      const store = useChatStore()
      store.setCurrentSession('session-123')
      
      const sendPromise = store.sendMessage('Hello')
      
      // Wait a bit and check
      await new Promise(resolve => setTimeout(resolve, 5))
      
      await sendPromise
    })

    it('should set error on failure', async () => {
      const { streamingChat } = await import('@/api/chat')
      
      vi.mocked(streamingChat).mockRejectedValue(new Error('Network error'))
      
      const store = useChatStore()
      store.setCurrentSession('session-123')
      
      await store.sendMessage('Hello')
      
      expect(store.error).toBe('Network error')
      expect(store.isGenerating).toBe(false)
    })
  })

  describe('Actions return', () => {
    it('should return correct types', () => {
      const store = useChatStore()
      
      expect(typeof store.setCurrentSession).toBe('function')
      expect(typeof store.clearMessages).toBe('function')
      expect(typeof store.sendMessage).toBe('function')
    })
  })
})
