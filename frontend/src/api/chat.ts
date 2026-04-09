/**
 * Chat API
 *
 * 聊天相关 API 调用
 */

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
 * 流式聊天
 */
export async function streamingChat(
  params: ChatParams,
  onToken: (token: string) => void
): Promise<void> {
  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
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
          if (data.error) {
            throw new Error(data.error)
          }
        } catch {
          // 忽略解析错误
        }
      }
    }
  }
}

/**
 * OpenAI 兼容格式聊天
 */
export async function streamingChatCompletions(
  params: CompletionParams,
  onDelta: (content: string) => void
): Promise<void> {
  const response = await fetch('/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
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
          // 忽略解析错误
        }
      }
    }
  }
}