import { test, expect } from '@playwright/test'

const API_KEY = 'sk-a8cd50445e4f3600087ca396df42fe96ccff2d8183470663738f75848871e48e'

test.describe('Chat Flow E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.evaluate((key) => {
      localStorage.setItem('mlx_api_key', key)
    }, API_KEY)
  })

  test('should show "请先创建或选择一个会话" when no session', async ({ page }) => {
    // Clear any existing sessions first by using a fresh page
    await page.evaluate(() => {
      localStorage.clear()
      localStorage.setItem('mlx_api_key', arguments[0])
    }, API_KEY)
    await page.goto('/')

    // Wait for page to load
    await page.waitForSelector('.chat-view')

    // Should show no session message (after sessions are fetched but none selected)
    // Note: if sessions exist in backend, one might be auto-selected
    const noSessionEl = page.locator('.no-session')
    const isVisible = await noSessionEl.isVisible().catch(() => false)

    // Either shows no session message, or has sessions loaded
    if (isVisible) {
      await expect(noSessionEl).toContainText('请先创建或选择一个会话')
    } else {
      // Sessions might have been loaded from backend
      const sessions = page.locator('.session-item')
      const sessionCount = await sessions.count()
      expect(sessionCount).toBeGreaterThan(0)
    }
  })

  test('should be able to create session and send message', async ({ page }) => {
    await page.goto('/')

    // Click create new session
    await page.click('button:has-text("新建会话")')

    // Wait for session to be created
    await page.waitForSelector('.session-item', { timeout: 5000 })

    // Should be able to type in textarea
    const textarea = page.locator('textarea')
    await expect(textarea).toBeVisible()
    await textarea.fill('hello')

    // Click send button
    await page.click('button:has-text("发送")')

    // Should show user message
    await expect(page.locator('.message-bubble.user').first()).toContainText('hello')

    // Should show assistant message (may be loading or have content)
    await expect(page.locator('.message-bubble.assistant').first()).toBeVisible({ timeout: 10000 })
  })

  test('should show model selector', async ({ page }) => {
    await page.goto('/')

    // Should show model selector
    await expect(page.locator('.model-selector')).toBeVisible()
    await expect(page.locator('.toggle-list')).toContainText('选择模型')
  })

  test('should be able to expand model list', async ({ page }) => {
    await page.goto('/')

    // Click to expand model list
    await page.click('.toggle-list')

    // Should show model list
    await expect(page.locator('.model-list')).toBeVisible()
    await expect(page.locator('.model-item').first()).toBeVisible()
  })

  test('should show streaming response in real-time', async ({ page }) => {
    await page.goto('/')

    // Create session
    await page.click('button:has-text("新建会话")')
    await page.waitForSelector('.session-item')

    // Send message
    const textarea = page.locator('textarea')
    await textarea.fill('hi')
    await page.click('button:has-text("发送")')

    // Should show user message immediately
    await expect(page.locator('.message-bubble.user')).toContainText('hi')

    // Should start showing assistant response (streaming)
    // Wait for assistant message to appear with some content
    await expect(async () => {
      const content = await page.locator('.message-bubble.assistant .content').first().textContent()
      expect(content?.length).toBeGreaterThan(0)
    }).toPass({ timeout: 30000, intervals: [1000] })
  })
})
