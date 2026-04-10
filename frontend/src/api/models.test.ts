import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('Models API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should get list of models', async () => {
    const { getModels } = await import('@/api/models')

    const mockModels = [
      { name: 'Model A', model_id: 'org/model-a', is_loaded: false, params_count: '7B' },
      { name: 'Model B', model_id: 'org/model-b', is_loaded: true, params_count: '3B' }
    ]

    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockModels)
    })

    const result = await getModels()

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/models',
      expect.objectContaining({ headers: expect.any(Object) })
    )
    expect(result).toEqual(mockModels)
    expect(result).toHaveLength(2)
  })

  it('should get loaded model info', async () => {
    const { getCurrentModel } = await import('@/api/models')

    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ is_loaded: true, model_id: 'org/test' })
    })

    const result = await getCurrentModel()

    expect(result.is_loaded).toBe(true)
  })

  it('should load a model', async () => {
    const { loadModel } = await import('@/api/models')

    mockFetch.mockResolvedValue({
      ok: true
    })

    await loadModel('org/test-model')

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/models/load',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ model: 'org/test-model' })
      })
    )
  })

  it('should throw error when getting models fails', async () => {
    const { getModels } = await import('@/api/models')

    mockFetch.mockResolvedValue({
      ok: false,
      statusText: 'Unauthorized'
    })

    await expect(getModels()).rejects.toThrow()
  })

  it('should throw error when loading model fails', async () => {
    const { loadModel } = await import('@/api/models')

    mockFetch.mockResolvedValue({
      ok: false,
      statusText: 'Internal Server Error'
    })

    await expect(loadModel('org/test')).rejects.toThrow()
  })
})
