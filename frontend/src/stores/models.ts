/**
 * Models Store
 *
 * 管理模型状态
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getModels, loadModel as loadModelApi } from '@/api/models'
import type { Model } from '@/api/models'

export const useModelsStore = defineStore('models', () => {
  // State
  const models = ref<Model[]>([])
  const loadedModelId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const loadedModel = computed(() =>
    models.value.find(m => m.model_id === loadedModelId.value)
  )

  const hasLoadedModel = computed(() => loadedModelId.value !== null)

  const localModels = computed(() =>
    models.value.filter(m => !m.model_type || m.model_type === 'local')
  )

  const remoteModels = computed(() =>
    models.value.filter(m => m.model_type === 'remote')
  )

  // Actions
  async function fetchModels() {
    loading.value = true
    error.value = null

    try {
      models.value = await getModels()

      // Find currently loaded model
      const loaded = models.value.find(m => m.is_loaded)
      if (loaded) {
        loadedModelId.value = loaded.model_id
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch models'
    } finally {
      loading.value = false
    }
  }

  async function loadModel(modelId: string) {
    loading.value = true
    error.value = null

    try {
      await loadModelApi(modelId)

      // Update local state
      models.value.forEach(m => {
        m.is_loaded = m.model_id === modelId
      })
      loadedModelId.value = modelId
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load model'
    } finally {
      loading.value = false
    }
  }

  function selectModel(modelId: string) {
    // For remote models, just mark as selected without API call
    models.value.forEach(m => {
      m.is_loaded = m.model_id === modelId
    })
    loadedModelId.value = modelId
  }

  return {
    // State
    models,
    loadedModelId,
    loading,
    error,
    // Computed
    loadedModel,
    hasLoadedModel,
    localModels,
    remoteModels,
    // Actions
    fetchModels,
    loadModel,
    selectModel
  }
})
