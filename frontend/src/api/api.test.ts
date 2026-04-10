import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('Sessions API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should list sessions', async () => {
    const { listSessions } = await import('@/api/sessions')
    
    const mockSessions = [
      { id: '1', name: 'Chat 1' },
      { id: '2', name: 'Chat 2' }
    ]
    
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockSessions)
    })
    
    const result = await listSessions()
    
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/sessions',
      expect.objectContaining({ headers: expect.any(Object) })
    )
    expect(result).toEqual(mockSessions)
  })

  it('should get session by id', async () => {
    const { getSession } = await import('@/api/sessions')

    const mockSession = { id: '1', name: 'Test Chat' }
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockSession)
    })

    const result = await getSession('1')

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/sessions/1',
      expect.objectContaining({ headers: expect.any(Object) })
    )
    expect(result).toEqual(mockSession)
  })

  it('should create session', async () => {
    const { createSession } = await import('@/api/sessions')
    
    const mockSession = { id: 'new-id', name: 'New Chat' }
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockSession)
    })
    
    const result = await createSession({ name: 'New Chat' })
    
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/sessions',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ name: 'New Chat' })
      })
    )
    expect(result).toEqual(mockSession)
  })

  it('should delete session', async () => {
    const { deleteSession } = await import('@/api/sessions')
    
    mockFetch.mockResolvedValue({
      ok: true
    })
    
    await deleteSession('1')

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/sessions/1',
      expect.objectContaining({ method: 'DELETE' })
    )
  })

  it('should throw error on failure', async () => {
    const { listSessions } = await import('@/api/sessions')
    
    mockFetch.mockResolvedValue({
      ok: false,
      statusText: 'Unauthorized'
    })
    
    await expect(listSessions()).rejects.toThrow('Failed to list sessions: Unauthorized')
  })
})

describe('Chat API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should handle streaming chat response', async () => {
    const { streamingChat } = await import('@/api/chat')

    // Mock ReadableStream - 使用正确的 SSE 格式
    const mockStream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('event: token\ndata: {"token":"Hello"}\n\n'))
        controller.enqueue(new TextEncoder().encode('event: token\ndata: {"token":" World"}\n\n'))
        controller.enqueue(new TextEncoder().encode('event: done\ndata: {"total_tokens":12,"duration_ms":100,"ttft_ms":20,"generation_ms":80,"output_chars_per_second":15}\n\n'))
        controller.close()
      }
    })

    mockFetch.mockResolvedValue({
      ok: true,
      body: mockStream
    })

    const tokens: string[] = []
    const result = await streamingChat(
      { session_id: '1', message: 'Hi' },
      (token) => tokens.push(token)
    )

    expect(tokens).toEqual(['Hello', ' World'])
    expect(result.durationMs).toBe(100)
    expect(result.ttftMs).toBe(20)
  })

  it('should handle streaming chat chunks split across reads', async () => {
    const { streamingChat } = await import('@/api/chat')

    const mockStream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('event: token\ndata: {"token":"Hel'))
        controller.enqueue(new TextEncoder().encode('lo"}\n\nevent: token\ndata: {"token":" world"}\n\n'))
        controller.enqueue(new TextEncoder().encode('event: done\ndata: {"duration_ms":12,"total_tokens":11,"ttft_ms":3,"generation_ms":9,"output_chars_per_second":122.2}\n\n'))
        controller.close()
      }
    })

    mockFetch.mockResolvedValue({
      ok: true,
      body: mockStream
    })

    const tokens: string[] = []
    const result = await streamingChat(
      { session_id: '1', message: 'Hi' },
      (token) => tokens.push(token)
    )

    expect(tokens).toEqual(['Hello', ' world'])
    expect(result).toEqual({
      durationMs: 12,
      totalTokens: 11,
      ttftMs: 3,
      generationMs: 9,
      outputCharsPerSecond: 122.2
    })
  })

  it('should throw error on chat failure', async () => {
    const { streamingChat } = await import('@/api/chat')
    
    mockFetch.mockResolvedValue({
      ok: false,
      statusText: 'Server Error'
    })
    
    await expect(
      streamingChat({ session_id: '1', message: 'Hi' }, () => {})
    ).rejects.toThrow('Chat failed: Server Error')
  })
})

describe('Settings API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should get settings', async () => {
    const { getSettings } = await import('@/api/settings')
    
    const mockSettings = {
      cors_allow_origins: ['http://localhost:3000'],
      default_model: 'test-model',
      default_temperature: 0.7
    }
    
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockSettings)
    })
    
    const result = await getSettings()
    
    expect(result).toEqual(mockSettings)
  })

  it('should list API keys', async () => {
    const { listApiKeys } = await import('@/api/settings')
    
    const mockResponse = {
      keys: [{ id: '1', name: 'test-key', key_prefix: 'sk-1234' }]
    }
    
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse)
    })
    
    const result = await listApiKeys()
    
    expect(result.keys).toHaveLength(1)
  })

  it('should get usage', async () => {
    const { getUsage } = await import('@/api/settings')
    
    const mockUsage = {
      api_key_id: '1',
      period: '2026-04',
      total_requests: 10,
      total_input_tokens: 100,
      total_output_tokens: 200,
      total_time_ms: 5000
    }
    
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockUsage)
    })
    
    const result = await getUsage()
    
    expect(result.total_requests).toBe(10)
  })
})
