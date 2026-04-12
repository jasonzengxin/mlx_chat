/**
 * Models API
 */

import { getAuthHeaders } from './auth'

export interface Model {
  id?: string
  name: string
  model_id: string
  is_loaded: boolean
  params_count?: string
  description?: string
  model_type?: 'local' | 'remote'
  endpoint?: string
  remote_provider?: string
  remote_base_url?: string
  has_remote_api_key?: boolean
}

export interface AddRemoteModelRequest {
  name: string
  model_id: string
  description?: string
  endpoint?: string
  provider_id?: string
  remote_provider?: string
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

export async function addRemoteModel(payload: AddRemoteModelRequest): Promise<Model> {
  const response = await fetch('/api/v1/model-registry', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      name: payload.name,
      model_id: payload.model_id,
      description: payload.description || '',
      model_type: 'remote',
      endpoint: payload.endpoint || '/chat/completions',
      provider_id: payload.provider_id || '',
      remote_provider: payload.remote_provider || '',
    }),
  })
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Failed to add remote model: ${response.status} ${detail}`)
  }
  return response.json()
}

export async function deleteModel(id: string): Promise<void> {
  const response = await fetch(`/api/v1/model-registry/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to delete model: ${response.statusText}`)
  }
}
