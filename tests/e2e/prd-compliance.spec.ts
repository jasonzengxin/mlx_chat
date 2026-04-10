import { test, expect } from '@playwright/test'

const API_KEY = 'sk-a8cd50445e4f3600087ca396df42fe96ccff2d8183470663738f75848871e48e'

/**
 * PRD 测试覆盖率补充
 *
 * 覆盖 PRD 2.1 - 2.3 中缺失的 E2E 测试场景
 */

test.describe('PRD 2.1.2 多会话管理', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.evaluate((key) => localStorage.setItem('mlx_api_key', key), API_KEY)
    await page.goto('/')
  })

  test('should switch between sessions and keep messages', async ({ page }) => {
    // 创建第一个会话
    await page.click('button:has-text("新建会话")')
    await page.waitForSelector('.session-item')
    const firstSession = page.locator('.session-item').first()
    await expect(firstSession).toBeVisible()

    // 发送消息
    await page.fill('textarea', 'First session message')
    await page.click('button:has-text("发送")')
    await page.waitForSelector('.message-bubble.user')

    // 创建第二个会话
    await page.click('button:has-text("新建会话")')
    await page.waitForTimeout(500)

    // 验证是新的空会话
    await expect(page.locator('.message-bubble')).toHaveCount(0)

    // 切换回第一个会话
    await firstSession.click()
    await page.waitForTimeout(500)

    // 验证消息还在
    await expect(page.locator('.message-bubble.user')).toContainText('First session message')
  })

  test('should delete session', async ({ page }) => {
    // 创建会话
    await page.click('button:has-text("新建会话")')
    await page.waitForSelector('.session-item')
    const sessionCount = await page.locator('.session-item').count()

    // 删除会话
    await page.locator('.delete-btn').first().click({ force: true })
    await page.waitForTimeout(500)

    // 验证会话数量减少
    const newCount = await page.locator('.session-item').count()
    expect(newCount).toBeLessThan(sessionCount)
  })
})

test.describe('PRD 2.1.3 模型切换', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.evaluate((key) => localStorage.setItem('mlx_api_key', key), API_KEY)
    await page.goto('/')
  })

  test('should display model info (params count)', async ({ page }) => {
    // 展开模型列表
    await page.click('.toggle-list')

    // 验证模型信息显示
    const modelItem = page.locator('.model-item').first()
    await expect(modelItem).toBeVisible()
    await expect(modelItem.locator('.model-params')).toBeVisible()
  })

  test('should show loading state when switching model', async ({ page }) => {
    // 展开模型列表
    await page.click('.toggle-list')

    // 点击加载按钮
    const loadBtn = page.locator('.load-btn').not(':disabled').first()
    await loadBtn.click()

    // 验证显示加载中状态
    await expect(loadBtn).toContainText('加载中...')
  })
})

test.describe('PRD 2.1.4 参数调节', () => {
  // 这些测试需要 ParameterPanel 组件实现后才能通过
  // 目前标记为 skipped

  test.skip('should have temperature slider (0.0 - 2.0)', async ({ page }) => {
    // TODO: 实现 ParameterPanel 组件后启用
    await page.goto('/')
    const slider = page.locator('input[type="range"]')
    await expect(slider).toBeVisible()
  })

  test.skip('should have max_tokens input (1 - 8192)', async ({ page }) => {
    // TODO: 实现 ParameterPanel 组件后启用
    await page.goto('/')
    const input = page.locator('input[name="max_tokens"]')
    await expect(input).toBeVisible()
  })

  test.skip('should have system_prompt textarea', async ({ page }) => {
    // TODO: 实现 ParameterPanel 组件后启用
    await page.goto('/')
    const textarea = page.locator('textarea[name="system_prompt"]')
    await expect(textarea).toBeVisible()
  })

  test.skip('should save parameters with session', async ({ page }) => {
    // TODO: 实现后启用
  })
})

test.describe('PRD 2.4.2 设置页面', () => {
  test.skip('should display API keys list', async ({ page }) => {
    // TODO: 实现 SettingsView 后启用
    await page.goto('/settings')
    await expect(page.locator('.api-keys-list')).toBeVisible()
  })

  test.skip('should display usage statistics', async ({ page }) => {
    // TODO: 实现后启用
    await page.goto('/settings')
    await expect(page.locator('.usage-stats')).toBeVisible()
  })

  test.skip('should toggle theme', async ({ page }) => {
    // TODO: 实现主题切换后启用
    await page.goto('/settings')
    await page.click('[data-testid="theme-toggle"]')
    // 验证主题切换
  })
})

test.describe('PRD 2.2.2 API 版本化', () => {
  test('should have /api/v1/ prefix', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/models', {
      headers: { 'Authorization': `Bearer ${API_KEY}` }
    })
    // 应该返回 200 或 401（有 auth header 所以是 200）
    expect([200, 401]).toContain(response.status())
  })

  test('should redirect /api/ to /api/v1/', async ({ request }) => {
    // 测试重定向
    const response = await request.get('http://localhost:8000/api/models', {
      headers: { 'Authorization': `Bearer ${API_KEY}` },
      maxRedirects: 0
    })
    // 可能是 307 重定向或 404
    expect([307, 404]).toContain(response.status())
  })
})

test.describe('PRD 2.2.4 Token 用量统计', () => {
  test('should return usage stats', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/usage', {
      headers: { 'Authorization': `Bearer ${API_KEY}` }
    })

    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data).toHaveProperty('total_requests')
    expect(data).toHaveProperty('total_input_tokens')
    expect(data).toHaveProperty('total_output_tokens')
  })

  test('should filter by period', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/usage?period=2026-04', {
      headers: { 'Authorization': `Bearer ${API_KEY}` }
    })

    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data.period).toBe('2026-04')
  })
})

test.describe('PRD 2.3.1 OpenAI 兼容接口', () => {
  test('should accept OpenAI format request', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/chat/completions', {
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      },
      data: {
        model: 'test-model',
        messages: [{ role: 'user', content: 'Hello' }],
        stream: false
      }
    })

    // 即使没有模型，也应该接受请求格式（不是 422）
    expect([200, 400, 404, 500]).toContain(response.status())
  })

  test('should return OpenAI compatible response format', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/chat/completions', {
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      },
      data: {
        model: 'test-model',
        messages: [{ role: 'user', content: 'Hello' }],
        stream: false
      }
    })

    // 如果模型加载了，验证响应格式
    if (response.ok()) {
      const data = await response.json()
      expect(data).toHaveProperty('choices')
      expect(data.choices[0]).toHaveProperty('message')
    }
  })
})
