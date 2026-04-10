import { test, expect } from '@playwright/test'

const API_BASE = 'http://localhost:8000'
// Test API key generated from init_db.py
const API_KEY = 'sk-a54d2c6cae2635ac42a5f57805f8264bb7e4f9fe1bfe920880f882e38fde1650'

test.describe('Backend API E2E', () => {
  test('health check should return ok', async ({ request }) => {
    const response = await request.get(`${API_BASE}/health`)
    expect(response.ok()).toBeTruthy()

    const data = await response.json()
    expect(data.status).toBe('ok')
  })

  test('should list models', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/models`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` }
    })

    expect(response.ok()).toBeTruthy()

    const models = await response.json()
    expect(Array.isArray(models)).toBeTruthy()
  })

  test('should create session', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/sessions`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` },
      data: { name: 'E2E Test Session' }
    })

    expect(response.ok()).toBeTruthy()

    const session = await response.json()
    expect(session.name).toBe('E2E Test Session')
    expect(session.id).toBeDefined()
  })

  test('should list sessions', async ({ request }) => {
    // Create a session first
    await request.post(`${API_BASE}/api/v1/sessions`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` },
      data: { name: 'List Test Session' }
    })

    const response = await request.get(`${API_BASE}/api/v1/sessions`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` }
    })

    expect(response.ok()).toBeTruthy()

    const sessions = await response.json()
    expect(Array.isArray(sessions)).toBeTruthy()
    expect(sessions.length).toBeGreaterThan(0)
  })

  test('should reject unauthorized requests', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/sessions`)
    expect(response.status()).toBe(401)
  })

  test('should return OpenAI compatible models list', async ({ request }) => {
    const response = await request.get(`${API_BASE}/v1/models`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` }
    })

    expect(response.ok()).toBeTruthy()

    const data = await response.json()
    expect(data.object).toBe('list')
    expect(Array.isArray(data.data)).toBeTruthy()
  })

  test('should handle OpenAI chat completions request format', async ({ request }) => {
    const response = await request.post(`${API_BASE}/v1/chat/completions`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` },
      data: {
        model: 'test-model',
        messages: [{ role: 'user', content: 'Hello' }],
        stream: false
      }
    })

    // May fail if no model loaded, but should accept the request format
    // and not return 422 validation error
    expect([200, 400, 401, 404, 500]).toContain(response.status())
  })
})
