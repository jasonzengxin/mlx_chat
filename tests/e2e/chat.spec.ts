import { test, expect } from '@playwright/test'

const API_KEY = 'sk-a8cd50445e4f3600087ca396df42fe96ccff2d8183470663738f75848871e48e'

test.describe('MLX Chat Frontend E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Set API key before each test
    await page.goto('/')
    await page.evaluate((key) => localStorage.setItem('mlx_api_key', key), API_KEY)
  })

  test('should load the chat page', async ({ page }) => {
    await page.goto('/')

    // Should show chat view (not modal)
    await expect(page.locator('.chat-view')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('.modal-overlay')).not.toBeVisible()
  })

  test('should display sidebar with session list', async ({ page }) => {
    await page.goto('/')

    await expect(page.locator('.chat-view')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('.sidebar')).toBeVisible()
  })

  test('should display main chat area', async ({ page }) => {
    await page.goto('/')

    await expect(page.locator('.main')).toBeVisible()
    await expect(page.locator('.chat-area')).toBeVisible()
  })

  test('should display input area', async ({ page }) => {
    await page.goto('/')

    await expect(page.locator('textarea')).toBeVisible()
  })

  test('should have message area', async ({ page }) => {
    await page.goto('/')

    // Check that chat area exists
    await expect(page.locator('.chat-area')).toBeVisible()
  })

  test('should show empty state when no messages', async ({ page }) => {
    await page.goto('/')

    // Should show empty state
    await expect(page.locator('.empty')).toBeVisible()
    await expect(page.locator('.empty')).toContainText('开始对话')
  })

  test('should allow typing in textarea', async ({ page }) => {
    await page.goto('/')

    const textarea = page.locator('textarea')
    await textarea.fill('Hello, this is a test message')
    await expect(textarea).toHaveValue('Hello, this is a test message')
  })
})
