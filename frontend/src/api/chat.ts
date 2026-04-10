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
  ttftMs: number
  generationMs: number
  outputCharsPerSecond: number
}

function collectSseDataBlocks(buffer: string): { events: string[]; remainder: string } {
  const normalized = buffer.replace(/\r\n/g, '\n')
  const blocks = normalized.split('\n\n')

  if (!normalized.endsWith('\n\n')) {
    return {
      events: blocks.slice(0, -1),
      remainder: blocks[blocks.length - 1] || '',
    }
  }

  return {
    events: blocks.filter(Boolean),
    remainder: '',
  }
}

function parseSseDataLine<T>(eventBlock: string): T | null {
  const dataLines = eventBlock
    .split('\n')
    .filter((line) => line.startsWith('data: '))
    .map((line) => line.slice(6))

  if (dataLines.length === 0) {
    return null
  }

  try {
    return JSON.parse(dataLines.join('\n')) as T
  } catch {
    return null
  }
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
  let ttftMs = 0
  let generationMs = 0
  let outputCharsPerSecond = 0
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })

    const { events, remainder } = collectSseDataBlocks(buffer)
    buffer = remainder

    for (const eventBlock of events) {
      const data = parseSseDataLine<{
        token?: string
        total_tokens?: number
        duration_ms?: number
        ttft_ms?: number
        generation_ms?: number
        output_chars_per_second?: number
        error?: string
      }>(eventBlock)

      if (!data) {
        continue
      }

      if (data.token) {
        onToken(data.token)
      }
      if (data.total_tokens !== undefined) {
        totalTokens = data.total_tokens
      }
      if (data.duration_ms !== undefined) {
        durationMs = data.duration_ms
      }
      if (data.ttft_ms !== undefined) {
        ttftMs = data.ttft_ms
      }
      if (data.generation_ms !== undefined) {
        generationMs = data.generation_ms
      }
      if (data.output_chars_per_second !== undefined) {
        outputCharsPerSecond = data.output_chars_per_second
      }
      if (data.error) {
        throw new Error(data.error)
      }
    }

    if (done) break
  }

  return { durationMs, totalTokens, ttftMs, generationMs, outputCharsPerSecond }
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

  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })

    const { events, remainder } = collectSseDataBlocks(buffer)
    buffer = remainder

    for (const eventBlock of events) {
      const rawData = eventBlock
        .split('\n')
        .find((line) => line.startsWith('data: '))
        ?.slice(6)

      if (!rawData || rawData === '[DONE]') {
        continue
      }

      try {
        const data = JSON.parse(rawData)
        if (data.choices?.[0]?.delta?.content) {
          onDelta(data.choices[0].delta.content)
        }
      } catch {
        // Ignore parse errors
      }
    }

    if (done) break
  }
}
