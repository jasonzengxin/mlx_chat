/**
 * Export API - Knowledge base export
 */

import { getAuthHeaders } from './auth'

// ── Types ────────────────────────────────────────────────

export interface ExportTemplate {
  id: string
  name: string
  description: string
  language: string
  template_content: string
  system_prompt: string
  is_builtin: boolean
  created_at: string
  updated_at: string
}

export interface ExportEstimate {
  estimated_tokens: number
  message_count: number
  is_remote: boolean
  warning: string | null
}

export interface ExportResult {
  total_chars: number
  duration_ms: number
  ttft_ms: number
  content: string
}

// ── Template CRUD ────────────────────────────────────────

export async function getExportTemplates(): Promise<ExportTemplate[]> {
  const response = await fetch('/api/v1/export/templates', {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to get templates: ${response.statusText}`)
  }
  return response.json()
}

export async function getExportTemplate(id: string): Promise<ExportTemplate> {
  const response = await fetch(`/api/v1/export/templates/${id}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to get template: ${response.statusText}`)
  }
  return response.json()
}

export async function createExportTemplate(data: {
  name: string
  description?: string
  language?: string
  template_content: string
  system_prompt: string
}): Promise<ExportTemplate> {
  const response = await fetch('/api/v1/export/templates', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`Failed to create template: ${response.statusText}`)
  }
  return response.json()
}

export async function deleteExportTemplate(id: string): Promise<void> {
  const response = await fetch(`/api/v1/export/templates/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to delete template: ${response.statusText}`)
  }
}

// ── Export Generation ────────────────────────────────────

export async function estimateExport(
  sessionId: string,
  templateId: string,
  language: string = 'zh'
): Promise<ExportEstimate> {
  const response = await fetch(
    `/api/v1/export/sessions/${sessionId}/export/estimate`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ template_id: templateId, language }),
    }
  )
  if (!response.ok) {
    throw new Error(`Failed to estimate export: ${response.statusText}`)
  }
  return response.json()
}

/**
 * SSE streaming export. Returns the full content on completion.
 */
export async function streamingExport(
  sessionId: string,
  templateId: string,
  language: string,
  onToken: (token: string) => void,
  signal?: AbortSignal
): Promise<ExportResult> {
  const response = await fetch(
    `/api/v1/export/sessions/${sessionId}/export`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ template_id: templateId, language }),
      signal,
    }
  )

  if (!response.ok) {
    throw new Error(`Export failed: ${response.statusText}`)
  }

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  if (!reader) {
    throw new Error('No response body')
  }

  let fullContent = ''
  let durationMs = 0
  let ttftMs = 0
  let buffer = ''
  let sawDone = false

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })

    // Parse SSE events
    const blocks = buffer.split('\n\n')
    if (!buffer.endsWith('\n\n')) {
      buffer = blocks.pop() || ''
    } else {
      buffer = ''
    }

    for (const block of blocks) {
      if (!block.trim()) continue

      const lines = block.split('\n')
      let eventType = ''
      let dataStr = ''

      for (const line of lines) {
        if (line.startsWith('event: ')) eventType = line.slice(7)
        if (line.startsWith('data: ')) dataStr = line.slice(6)
      }

      if (!dataStr) continue

      if (eventType === 'error') {
        try {
          const data = JSON.parse(dataStr)
          throw new Error(data.error || 'Export failed')
        } catch (e) {
          if (e instanceof Error) throw e
          throw new Error('Export failed')
        }
      }

      let data: any
      try {
        data = JSON.parse(dataStr)
      } catch {
        // Only ignore malformed/incomplete JSON payloads
        continue
      }

      if (eventType === 'token' && data.token) {
        onToken(data.token)
        fullContent += data.token
      } else if (eventType === 'done') {
        fullContent = data.content || fullContent
        durationMs = data.duration_ms || 0
        ttftMs = data.ttft_ms || 0
        sawDone = true
      }
    }

    if (done) break
  }

  if (!sawDone) {
    throw new Error('Export ended before completion')
  }
  if (!fullContent.trim()) {
    throw new Error('Export returned empty content')
  }

  return {
    total_chars: fullContent.length,
    duration_ms: durationMs,
    ttft_ms: ttftMs,
    content: fullContent,
  }
}
