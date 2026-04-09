/**
 * Settings API
 *
 * 设置管理 API 调用
 */

export interface APIKey {
  id: string
  name: string
  key_prefix: string
  key?: string // 只在创建时返回
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

// API Keys
export async function listApiKeys(): Promise<{ keys: APIKey[] }> {
  const response = await fetch('/api/v1/settings/api-keys')

  if (!response.ok) {
    throw new Error(`Failed to list API keys: ${response.statusText}`)
  }

  return response.json()
}

export async function createApiKey(name: string): Promise<APIKey> {
  const response = await fetch('/api/v1/settings/api-keys', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
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
  })

  if (!response.ok) {
    throw new Error(`Failed to delete API key: ${response.statusText}`)
  }
}

// Usage
export async function getUsage(period?: string): Promise<UsageSummary> {
  const url = period ? `/api/v1/usage?period=${period}` : '/api/v1/usage'

  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(`Failed to get usage: ${response.statusText}`)
  }

  return response.json()
}

// Settings
export async function getSettings(): Promise<Settings> {
  const response = await fetch('/api/v1/settings')

  if (!response.ok) {
    throw new Error(`Failed to get settings: ${response.statusText}`)
  }

  return response.json()
}

export async function updateSettings(settings: Partial<Settings>): Promise<void> {
  const response = await fetch('/api/v1/settings', {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(settings),
  })

  if (!response.ok) {
    throw new Error(`Failed to update settings: ${response.statusText}`)
  }
}