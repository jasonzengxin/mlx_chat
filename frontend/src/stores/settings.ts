/**
 * Settings Store
 *
 * 管理应用设置
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listApiKeys, createApiKey, deleteApiKey } from '@/api/settings'

export interface APIKey {
  id: string
  name: string
  key_prefix: string
  created_at?: string
  last_used_at?: string
}

export const useSettingsStore = defineStore('settings', () => {
  // State
  const theme = ref<'dark' | 'light'>('dark')
  const apiKeys = ref<APIKey[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function fetchApiKeys() {
    loading.value = true
    error.value = null

    try {
      const result = await listApiKeys()
      apiKeys.value = result.keys || []
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch API keys'
    } finally {
      loading.value = false
    }
  }

  async function createNewApiKey(name: string) {
    try {
      const result = await createApiKey(name)
      apiKeys.value.push({
        id: result.id,
        name: result.name,
        key_prefix: result.key_prefix,
      })
      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create API key'
      throw e
    }
  }

  async function removeApiKey(keyId: string) {
    try {
      await deleteApiKey(keyId)
      apiKeys.value = apiKeys.value.filter(k => k.id !== keyId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete API key'
    }
  }

  function toggleTheme() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  return {
    theme,
    apiKeys,
    loading,
    error,
    fetchApiKeys,
    createApiKey: createNewApiKey,
    deleteApiKey: removeApiKey,
    toggleTheme,
  }
})