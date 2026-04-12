/**
 * Sessions API
 */

import { getAuthHeaders } from './auth'

export interface Session {
  id: string
  name: string
  model?: string
  temperature?: number
  max_tokens?: number
  system_prompt?: string
  context_messages?: number
  messages?: Array<{
    id: string
    role: string
    content: string
    created_at: string
  }>
  created_at?: string
  updated_at?: string
}

export async function listSessions(): Promise<Session[]> {
  const response = await fetch('/api/v1/sessions', {
    headers: getAuthHeaders()
  })

  if (!response.ok) {
    throw new Error(`Failed to list sessions: ${response.statusText}`)
  }

  return response.json()
}

export async function getSession(id: string): Promise<Session> {
  const response = await fetch(`/api/v1/sessions/${id}`, {
    headers: getAuthHeaders()
  })

  if (!response.ok) {
    throw new Error(`Failed to get session: ${response.statusText}`)
  }

  return response.json()
}

export async function createSession(params: { name?: string; model?: string }): Promise<Session> {
  const response = await fetch('/api/v1/sessions', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(params),
  })

  if (!response.ok) {
    throw new Error(`Failed to create session: ${response.statusText}`)
  }

  return response.json()
}

export async function updateSession(
  id: string,
  params: Partial<Session>
): Promise<Session> {
  const response = await fetch(`/api/v1/sessions/${id}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(params),
  })

  if (!response.ok) {
    throw new Error(`Failed to update session: ${response.statusText}`)
  }

  return response.json()
}

export async function deleteSession(id: string): Promise<void> {
  const response = await fetch(`/api/v1/sessions/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  })

  if (!response.ok) {
    throw new Error(`Failed to delete session: ${response.statusText}`)
  }
}

export async function deleteAllSessions(): Promise<{ deleted_count: number }> {
  const response = await fetch('/api/v1/sessions', {
    method: 'DELETE',
    headers: getAuthHeaders()
  })

  if (!response.ok) {
    throw new Error(`Failed to delete all sessions: ${response.statusText}`)
  }

  return response.json()
}
