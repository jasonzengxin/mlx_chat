import { test, expect } from '@playwright/test'

const API_KEY = 'sk-a8cd50445e4f3600087ca396df42fe96ccff2d8183470663738f75848871e48e'

test.describe('API Key Flow', () => {
  test('should show API key modal when no key is stored', async ({ page }) => {
    // Clear localStorage
    await page.goto('/')
    await page.evaluate(() => localStorage.clear())
    await page.goto('/')

    // Should show modal
    await expect(page.locator('.modal-overlay')).toBeVisible()
    await expect(page.locator('.modal h2')).toContainText('Welcome to MLX Chat')
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button:has-text("Continue")')).toBeVisible()
  })

  test('should save API key and hide modal on submit', async ({ page }) => {
    await page.goto('/')
    await page.evaluate(() => localStorage.clear())
    await page.goto('/')

    // Enter API key
    await page.fill('input[type="password"]', API_KEY)
    await page.click('button:has-text("Continue")')

    // Modal should be hidden
    await expect(page.locator('.modal-overlay')).not.toBeVisible()

    // Should show main chat UI
    await expect(page.locator('.chat-view')).toBeVisible()

    // Verify key was saved
    const savedKey = await page.evaluate(() => localStorage.getItem('mlx_api_key'))
    expect(savedKey).toBe(API_KEY)
  })

  test('should not show modal when API key already exists', async ({ page }) => {
    await page.goto('/')

    // Pre-set API key
    await page.evaluate((key) => localStorage.setItem('mlx_api_key', key), API_KEY)

    // Reload page
    await page.goto('/')

    // Modal should not be visible
    await expect(page.locator('.modal-overlay')).not.toBeVisible()

    // Main UI should be visible
    await expect(page.locator('.chat-view')).toBeVisible()
    await expect(page.locator('.sidebar')).toBeVisible()
  })

  test('should send Authorization header with API requests', async ({ page }) => {
    const capturedRequests: { url: string; method: string; headers: Record<string, string> }[] = []

    // Intercept API requests BEFORE navigating
    await page.route('**/api/v1/**', async (route) => {
      capturedRequests.push({
        url: route.request().url(),
        method: route.request().method(),
        headers: route.request().headers()
      })
      await route.continue()
    })

    await page.goto('/')
    await page.evaluate((key) => localStorage.setItem('mlx_api_key', key), API_KEY)
    await page.goto('/')

    // Click new session button to trigger API call
    const newBtn = page.locator('button:has-text("新建会话")')
    await expect(newBtn).toBeVisible()
    await newBtn.click()

    // Wait for API call
    await page.waitForTimeout(1000)

    // Check that Authorization header was sent
    const authRequests = capturedRequests.filter(r => r.headers['authorization'])
    expect(authRequests.length).toBeGreaterThan(0)
    expect(authRequests[0].headers['authorization']).toBe(`Bearer ${API_KEY}`)
  })

  test('should show error when submitting empty API key', async ({ page }) => {
    await page.goto('/')
    await page.evaluate(() => localStorage.clear())
    await page.goto('/')

    // Submit without entering key
    await page.click('button:has-text("Continue")')

    // Should show error
    await expect(page.locator('.error')).toContainText('Please enter an API key')
    await expect(page.locator('.modal-overlay')).toBeVisible()
  })

  test('should persist API key across page reloads', async ({ page }) => {
    await page.goto('/')

    // Set API key
    await page.evaluate((key) => localStorage.setItem('mlx_api_key', key), API_KEY)

    // Reload multiple times
    await page.goto('/')
    await expect(page.locator('.modal-overlay')).not.toBeVisible()

    await page.goto('/')
    await expect(page.locator('.modal-overlay')).not.toBeVisible()
  })
})

test.describe('Session Creation with Auth', () => {
  test('should create session with Authorization header', async ({ page }) => {
    const capturedRequests: { url: string; method: string; headers: Record<string, string> }[] = []

    await page.route('**/api/v1/sessions', async (route) => {
      capturedRequests.push({
        url: route.request().url(),
        method: route.request().method(),
        headers: route.request().headers()
      })
      await route.continue()
    })

    await page.goto('/')
    await page.evaluate((key) => localStorage.setItem('mlx_api_key', key), API_KEY)
    await page.goto('/')

    // Click new session button (text is "新建会话" in Chinese)
    const newBtn = page.locator('button:has-text("新建会话")')
    await expect(newBtn).toBeVisible()
    await newBtn.click()

    // Wait for POST request
    await page.waitForTimeout(1000)

    // Verify POST request has Authorization header
    const postRequest = capturedRequests.find(r => r.method === 'POST')
    expect(postRequest).toBeDefined()
    expect(postRequest!.headers['authorization']).toContain('Bearer')
  })
})
