/**
 * Vitest 测试设置
 *
 * 配置:
 * - 全局 mock
 * - 测试环境
 */

import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// Mock fetch
global.fetch = vi.fn()

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(global, 'localStorage', { value: localStorageMock })

// Mock IntersectionObserver
class IntersectionObserverMock {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}
Object.defineProperty(global, 'IntersectionObserver', {
  value: IntersectionObserverMock,
})

// Mock ResizeObserver
class ResizeObserverMock {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}
Object.defineProperty(global, 'ResizeObserver', {
  value: ResizeObserverMock,
})

// API Mock 工厂函数
export const createMockApi = () => ({
  chat: {
    sendMessage: vi.fn(),
    streamingChat: vi.fn(),
  },
  sessions: {
    list: vi.fn().mockResolvedValue([]),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  models: {
    list: vi.fn().mockResolvedValue([]),
    load: vi.fn(),
    getCurrent: vi.fn(),
  },
  usage: {
    get: vi.fn(),
  },
  settings: {
    get: vi.fn(),
    update: vi.fn(),
    listApiKeys: vi.fn().mockResolvedValue({ keys: [] }),
    createApiKey: vi.fn(),
    deleteApiKey: vi.fn(),
  },
})

// 重置所有 mock
beforeEach(() => {
  vi.clearAllMocks()
  localStorageMock.getItem.mockReset()
  localStorageMock.setItem.mockReset()
  localStorageMock.removeItem.mockReset()
  localStorageMock.clear.mockReset()
})