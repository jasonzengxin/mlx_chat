/**
 * Settings API
 */

import { getAuthHeaders } from './auth'

export interface APIKey {
  id: string
  name: string
  key_prefix: string
  key?: string
  created_at?: string
  last_used_at?: string
}

export interface UsageSummary {
  api_key_id: string
  period: string
  total_requests: number
  total_input_tokens: number
  total_output_tokens: number
  total_time_ms: number
}

export interface Settings {
  cors_allow_origins: string[]
  default_model: string
  default_temperature: number
  default_max_tokens: number
}

// ── Remote Provider types ────────────────────────────────

export interface RemoteProvider {
  id: string
  name: string
  provider_type: string
  base_url: string
  has_api_key: boolean
  is_active: boolean
  created_at: string
}

export interface RemoteValidationResult {
  valid: boolean
  status_code: number | null
  message: string
  models_count: number | null
  base_url: string
  provider_name?: string
  probe_url?: string
}

// ── API Keys ─────────────────────────────────────────────

export async function listApiKeys(): Promise<{ keys: APIKey[] }> {
  const response = await fetch('/api/v1/settings/api-keys', {
    headers: getAuthHeaders()
  })
  if (!response.ok) {
    throw new Error(`Failed to list API keys: ${response.statusText}`)
  }
  return response.json()
}

export async function createApiKey(name: string): Promise<APIKey> {
  const response = await fetch('/api/v1/settings/api-keys', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ name }),
  })
  if (!response.ok) {
    throw new Error(`Failed to create API key: ${response.statusText}`)
  }
  return response.json()
}

export async function deleteApiKey(keyId: string): Promise<void> {
  const response = await fetch(`/api/v1/settings/api-keys/${keyId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  })
  if (!response.ok) {
    throw new Error(`Failed to delete API key: ${response.statusText}`)
  }
}

// ── Usage ────────────────────────────────────────────────

export async function getUsage(period?: string): Promise<UsageSummary> {
  const url = period ? `/api/v1/usage?period=${period}` : '/api/v1/usage'
  const response = await fetch(url, {
    headers: getAuthHeaders()
  })
  if (!response.ok) {
    throw new Error(`Failed to get usage: ${response.statusText}`)
  }
  return response.json()
}

// ── App Settings ─────────────────────────────────────────

export async function getSettings(): Promise<Settings> {
  const response = await fetch('/api/v1/settings', {
    headers: getAuthHeaders()
  })
  if (!response.ok) {
    throw new Error(`Failed to get settings: ${response.statusText}`)
  }
  return response.json()
}

export async function updateSettings(settings: Partial<Settings>): Promise<void> {
  const response = await fetch('/api/v1/settings', {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(settings),
  })
  if (!response.ok) {
    throw new Error(`Failed to update settings: ${response.statusText}`)
  }
}

// ── Remote Providers ─────────────────────────────────────

export async function listProviders(): Promise<RemoteProvider[]> {
  const response = await fetch('/api/v1/settings/remote/providers', {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to list providers: ${response.statusText}`)
  }
  return response.json()
}

export async function createProvider(data: {
  name: string
  provider_type?: string
  base_url?: string
  api_key?: string
}): Promise<RemoteProvider> {
  const response = await fetch('/api/v1/settings/remote/providers', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || response.statusText)
  }
  return response.json()
}

export async function updateProvider(
  providerId: string,
  data: {
    name?: string
    provider_type?: string
    base_url?: string
    api_key?: string
  },
): Promise<RemoteProvider> {
  const response = await fetch(`/api/v1/settings/remote/providers/${providerId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`Failed to update provider: ${response.statusText}`)
  }
  return response.json()
}

export async function deleteProvider(providerId: string): Promise<void> {
  const response = await fetch(`/api/v1/settings/remote/providers/${providerId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to delete provider: ${response.statusText}`)
  }
}

export async function validateProvider(
  providerId: string,
  overrides?: { base_url?: string; api_key?: string },
): Promise<RemoteValidationResult> {
  const response = await fetch(`/api/v1/settings/remote/providers/${providerId}/validate`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(overrides || {}),
  })
  if (!response.ok) {
    throw new Error(`Validation failed: ${response.statusText}`)
  }
  return response.json()
}

export async function validateCredentials(
  data: { base_url: string; api_key: string },
): Promise<RemoteValidationResult> {
  const response = await fetch('/api/v1/settings/remote/validate', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`Validation failed: ${response.statusText}`)
  }
  return response.json()
}
