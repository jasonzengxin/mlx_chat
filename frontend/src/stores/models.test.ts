import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useModelsStore } from '@/stores/models'

// Mock API
vi.mock('@/api/models', () => ({
  getModels: vi.fn(),
  getCurrentModel: vi.fn(),
  loadModel: vi.fn()
}))

describe('Models Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const store = useModelsStore()

      expect(store.models).toEqual([])
      expect(store.loadedModelId).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('fetchModels', () => {
    it('should fetch and store models', async () => {
      const { getModels } = await import('@/api/models')

      const mockModels = [
        { name: 'Qwen', model_id: 'org/qwen', is_loaded: true, params_count: '7B' },
        { name: 'Llama', model_id: 'org/llama', is_loaded: false, params_count: '13B' }
      ]
      vi.mocked(getModels).mockResolvedValue(mockModels)

      const store = useModelsStore()
      await store.fetchModels()

      expect(store.models).toEqual(mockModels)
      expect(store.loadedModelId).toBe('org/qwen')
    })

    it('should set error on fetch failure', async () => {
      const { getModels } = await import('@/api/models')

      vi.mocked(getModels).mockRejectedValue(new Error('Network error'))

      const store = useModelsStore()
      await store.fetchModels()

      expect(store.error).toBe('Network error')
    })
  })

  describe('loadModel', () => {
    it('should load a model', async () => {
      const { loadModel, getModels } = await import('@/api/models')

      vi.mocked(loadModel).mockResolvedValue(undefined)
      vi.mocked(getModels).mockResolvedValue([
        { name: 'Qwen', model_id: 'org/qwen', is_loaded: true, params_count: '7B' }
      ])

      const store = useModelsStore()
      store.models = [
        { name: 'Qwen', model_id: 'org/qwen', is_loaded: false, params_count: '7B' }
      ]

      await store.loadModel('org/qwen')

      expect(store.loading).toBe(false)
      expect(store.loadedModelId).toBe('org/qwen')
    })

    it('should set loading state during load', async () => {
      const { loadModel } = await import('@/api/models')

      vi.mocked(loadModel).mockImplementation(async () => {
        await new Promise(resolve => setTimeout(resolve, 50))
      })

      const store = useModelsStore()
      store.models = [
        { name: 'Qwen', model_id: 'org/qwen', is_loaded: false, params_count: '7B' }
      ]

      const loadPromise = store.loadModel('org/qwen')

      // Check loading state is true during load
      expect(store.loading).toBe(true)

      await loadPromise

      expect(store.loading).toBe(false)
    })
  })

  describe('computed properties', () => {
    it('should return loaded model', async () => {
      const store = useModelsStore()
      store.models = [
        { name: 'Qwen', model_id: 'org/qwen', is_loaded: true, params_count: '7B' },
        { name: 'Llama', model_id: 'org/llama', is_loaded: false, params_count: '13B' }
      ]
      store.loadedModelId = 'org/qwen'

      expect(store.loadedModel?.name).toBe('Qwen')
    })

    it('should return hasLoadedModel', async () => {
      const store = useModelsStore()

      expect(store.hasLoadedModel).toBe(false)

      store.loadedModelId = 'org/qwen'

      expect(store.hasLoadedModel).toBe(true)
    })
  })
})
