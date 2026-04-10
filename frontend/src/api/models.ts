/**
 * Models API
 */

import { getAuthHeaders } from './auth'

export interface Model {
  name: string
  model_id: string
  is_loaded: boolean
  params_count?: string
  description?: string
}

export async function getModels(): Promise<Model[]> {
  const response = await fetch('/api/v1/models', {
    headers: getAuthHeaders()
  })

  if (!response.ok) {
    throw new Error(`Failed to get models: ${response.statusText}`)
  }

  return response.json()
}

export async function getCurrentModel(): Promise<{ is_loaded: boolean; model_id: string | null }> {
  const response = await fetch('/api/v1/models/current', {
    headers: getAuthHeaders()
  })

  if (!response.ok) {
    throw new Error(`Failed to get current model: ${response.statusText}`)
  }

  return response.json()
}

export async function loadModel(modelId: string): Promise<void> {
  const response = await fetch('/api/v1/models/load', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ model: modelId })
  })

  if (!response.ok) {
    throw new Error(`Failed to load model: ${response.statusText}`)
  }
}

export async function unloadModel(): Promise<void> {
  const response = await fetch('/api/v1/models/unload', {
    method: 'POST',
    headers: getAuthHeaders()
  })

  if (!response.ok) {
    throw new Error(`Failed to unload model: ${response.statusText}`)
  }
}
