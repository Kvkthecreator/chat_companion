import { test, expect } from '@playwright/test';

const basketId = process.env.TEST_BASKET_ID;
test.skip(!basketId, 'requires TEST_BASKET_ID to run');

test.describe('Canon v1.4.0 Timeline: Async Intelligence Events', () => {

  test('timeline captures complete async intelligence pipeline', async ({ page }) => {
    // Create dump to trigger full pipeline
    await page.goto(`/baskets/${basketId}/new/dumps`);
    
    const testContent = 'Timeline test: analyzing user engagement patterns and conversion metrics.';
    await page.fill('textarea', testContent);
    await page.click('button:has-text("Create")');
    
    await expect(page.locator('text=✓')).toBeVisible({ timeout: 5000 });
    
    // Navigate to timeline
    await page.goto(`/baskets/${basketId}/timeline`);
    
    // Should see dump.created event immediately
    await expect(page.locator('text=dump created')).toBeVisible({ timeout: 5000 });
    
    // Should see agent processing events
    await expect(page.locator('text=agent, text=processing')).toBeVisible({ timeout: 30000 });
    
    // Should see substrate creation events
    await expect(page.locator('text=blocks, text=substrate')).toBeVisible({ timeout: 90000 });
  });

  test('timeline event structure validation', async ({ page }) => {
    const response = await page.request.get(`/api/baskets/${basketId}/timeline`);
    expect(response.ok()).toBeTruthy();
    
    const timeline = await response.json();
    
    if (timeline.length > 0) {
      const event = timeline[0];
      
      // Canon-compliant event structure
      expect(event).toHaveProperty('id');
      expect(event).toHaveProperty('basket_id');
      expect(event).toHaveProperty('event_type');
      expect(event).toHaveProperty('payload');
      expect(event).toHaveProperty('created_at');
      
      expect(event.basket_id).toBe(basketId);
      expect(typeof event.payload).toBe('object');
    }
  });

  test('timeline chronological order (append-only)', async ({ page }) => {
    const response = await page.request.get(`/api/baskets/${basketId}/timeline`);
    const timeline = await response.json();
    
    if (timeline.length > 1) {
      // Should be in descending chronological order (newest first)
      for (let i = 0; i < timeline.length - 1; i++) {
        const current = new Date(timeline[i].created_at);
        const next = new Date(timeline[i + 1].created_at);
        expect(current.getTime()).toBeGreaterThanOrEqual(next.getTime());
      }
    }
  });

});