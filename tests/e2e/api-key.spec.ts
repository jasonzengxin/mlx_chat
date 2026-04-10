import { test, expect } from '@playwright/test'

const API_KEY = 'sk-a8cd50445e4f3600087ca396df42fe96ccff2d8183470663738f75848871e48e'

test.describe('API Key Flow E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test
    await page.goto('/')
    await page.evaluate(() => localStorage.clear())
  })

  test('should show API key modal when no key exists', async ({ page }) => {
    await page.goto('/')

    // Should show the welcome modal
    await expect(page.locator('h2:has-text("Welcome")')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button:has-text("Continue")')).toBeVisible()
  })

  test('should save API key when user enters it', async ({ page }) => {
    await page.goto('/')

    // Enter API key
    await page.fill('input[type="password"]', API_KEY)
    await page.click('button:has-text("Continue")')

    // Wait for reload
    await page.waitForLoadState('networkidle')

    // Should now show the main UI, not the modal
    await expect(page.locator('.chat-view')).toBeVisible()
    await expect(page.locator('h2:has-text("Welcome")')).not.toBeVisible()
  })

  test('should persist API key in localStorage', async ({ page }) => {
    await page.goto('/')

    // Enter API key
    await page.fill('input[type="password"]', API_KEY)
    await page.click('button:has-text("Continue")')

    await page.waitForLoadState('networkidle')

    // Check localStorage
    const storedKey = await page.evaluate(() => localStorage.getItem('mlx_api_key'))
    expect(storedKey).toBe(API_KEY)
  })

  test('should successfully create session after API key is set', async ({ page }) => {
    // Pre-set the API key
    await page.goto('/')
    await page.evaluate((key) => localStorage.setItem('mlx_api_key', key), API_KEY)
    await page.goto('/')

    // Should show main UI directly
    await expect(page.locator('.chat-view')).toBeVisible()

    // Click "新建会话" to create session
    await page.click('button:has-text("新建会话")')

    // Should show session list
    await expect(page.locator('.session-item').first()).toBeVisible({ timeout: 5000 })
  })

  test('should send Authorization header with API requests', async ({ page }) => {
    // Intercept the API call
    let authorizationHeader = ''
    await page.route('**/api/v1/sessions**', async (route) => {
      authorizationHeader = route.request().headers()['authorization'] || ''
      await route.continue()
    })

    // Pre-set the API key
    await page.goto('/')
    await page.evaluate((key) => localStorage.setItem('mlx_api_key', key), API_KEY)
    await page.goto('/')

    // Create session
    await page.click('button:has-text("新建会话")')

    // Wait a bit for the request
    await page.waitForTimeout(1000)

    // Check that Authorization header was sent
    expect(authorizationHeader).toBe(`Bearer ${API_KEY}`)
  })
})
