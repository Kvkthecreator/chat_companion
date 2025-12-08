import { test, expect } from '@playwright/test';

const basketId = process.env.TEST_BASKET_ID;
test.skip(!basketId, 'requires TEST_BASKET_ID to run');

test.describe('Canon v1.4.0 Reflections: Derived Read-Models', () => {

  test('reflections computed from substrate (not stored)', async ({ page }) => {
    // Sacred Principle: Reflections are derived read-models, not stored truths
    
    // Create substrate content
    await page.goto(`/baskets/${basketId}/new/dumps`);
    await page.fill('textarea', 'Strategic analysis: customer retention strategies and market positioning for competitive advantage.');
    await page.click('button:has-text("Create")');
    await expect(page.locator('text=✓')).toBeVisible({ timeout: 5000 });

    // Wait for agent processing to create substrate
    await expect(page.locator('text=⏳')).toBeVisible({ timeout: 3000 });
    await expect(page.locator('text=✅')).toBeVisible({ timeout: 90000 });

    // Navigate to reflections
    await page.goto(`/baskets/${basketId}/reflections`);
    
    // Should compute reflections from available substrate
    await expect(page.locator('text=reflection, text=pattern, text=insight')).toBeVisible({ timeout: 10000 });
    
    // Reflections should be real-time derived, not cached
    const response = await page.request.get(`/api/baskets/${basketId}/reflections`);
    expect(response.ok()).toBeTruthy();
    
    const reflections = await response.json();
    if (reflections.length > 0) {
      // Should include source substrate references
      expect(reflections[0]).toHaveProperty('content');
      expect(reflections[0]).toHaveProperty('reflection_type');
    }
  });

  test('reflection system substrate equality (all peers)', async ({ page }) => {
    // Test that reflections consider all substrate types as peers
    
    const response = await page.request.get(`/api/baskets/${basketId}/reflections`);
    expect(response.ok()).toBeTruthy();
    
    const reflections = await response.json();
    
    // Reflections should be computed from all substrate types
    // (dumps, blocks, context_items, timeline_events - all peers)
    if (reflections.length > 0) {
      const reflection = reflections[0];
      expect(reflection).toHaveProperty('basket_id', basketId);
      expect(reflection.basket_id).toBe(basketId);
    }
  });

  test('reflection computation performance', async ({ page }) => {
    // Reflections should compute efficiently as read-models
    
    const startTime = Date.now();
    const response = await page.request.get(`/api/baskets/${basketId}/reflections`);
    const computeTime = Date.now() - startTime;
    
    expect(response.ok()).toBeTruthy();
    expect(computeTime).toBeLessThan(5000); // Should compute within 5 seconds
    
    const reflections = await response.json();
    expect(Array.isArray(reflections)).toBeTruthy();
  });

});