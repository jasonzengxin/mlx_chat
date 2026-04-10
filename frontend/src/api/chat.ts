/**
 * Chat API
 */

import { getAuthHeaders } from './auth'

export interface ChatParams {
  session_id: string
  message: string
  temperature?: number
  max_tokens?: number
  system_prompt?: string
}

export interface CompletionParams {
  model: string
  messages: Array<{ role: string; content: string }>
  temperature?: number
  max_tokens?: number
  stream?: boolean
}

/**
 * Stream chat response from backend
 */
export interface StreamingResult {
  durationMs: number
  totalTokens: number
}

export async function streamingChat(
  params: ChatParams,
  onToken: (token: string) => void
): Promise<StreamingResult> {
  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(params),
  })

  if (!response.ok) {
    throw new Error(`Chat failed: ${response.statusText}`)
  }

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  if (!reader) {
    throw new Error('No response body')
  }

  let durationMs = 0
  let totalTokens = 0

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value)
    const lines = chunk.split('\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.token) {
            onToken(data.token)
          }
          if (data.total_tokens !== undefined) {
            totalTokens = data.total_tokens
          }
          if (data.duration_ms !== undefined) {
            durationMs = data.duration_ms
          }
          if (data.error) {
            throw new Error(data.error)
          }
        } catch {
          // Ignore parse errors
        }
      }
    }
  }

  return { durationMs, totalTokens }
}

/**
 * OpenAI compatible streaming chat
 */
export async function streamingChatCompletions(
  params: CompletionParams,
  onDelta: (content: string) => void
): Promise<void> {
  const response = await fetch('/v1/chat/completions', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(params),
  })

  if (!response.ok) {
    throw new Error(`Chat completions failed: ${response.statusText}`)
  }

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  if (!reader) {
    throw new Error('No response body')
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value)
    const lines = chunk.split('\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.choices?.[0]?.delta?.content) {
            onDelta(data.choices[0].delta.content)
          }
        } catch {
          // Ignore parse errors
        }
      }
    }
  }
}
