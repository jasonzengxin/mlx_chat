/**
 * Auth utilities
 */

const API_KEY_STORAGE = 'mlx_api_key'

export function getApiKey(): string {
  return localStorage.getItem(API_KEY_STORAGE) || ''
}

export function setApiKey(key: string): void {
  localStorage.setItem(API_KEY_STORAGE, key)
}

export function clearApiKey(): void {
  localStorage.removeItem(API_KEY_STORAGE)
}

export function hasApiKey(): boolean {
  return !!getApiKey()
}

export function getAuthHeaders(): HeadersInit {
  const key = getApiKey()
  if (key) {
    return {
      'Authorization': `Bearer ${key}`,
      'Content-Type': 'application/json'
    }
  }
  return {
    'Content-Type': 'application/json'
  }
}
