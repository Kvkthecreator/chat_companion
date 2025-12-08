import { test, expect } from '@playwright/test';

const basketId = process.env.TEST_BASKET_ID;
test.skip(!basketId, 'requires TEST_BASKET_ID to run');

test.describe('Canon v1.4.0 Memory: Capture Sacred + Async Intelligence', () => {

  test('multiple dump creation with agent processing', async ({ page }) => {
    // Sacred Principle #1: Capture is Sacred - all input becomes immutable raw_dump
    await page.goto(`/baskets/${basketId}/new/dumps`);

    // Create first dump
    await page.fill('textarea', 'Market research findings for Q2 strategy planning.');
    await page.click('button:has-text("Create")');
    await expect(page.locator('text=✓')).toBeVisible({ timeout: 5000 });

    // Create second dump
    await page.goto(`/baskets/${basketId}/new/dumps`);
    await page.fill('textarea', 'Customer feedback analysis from recent feature releases.');
    await page.click('button:has-text("Create")');
    await expect(page.locator('text=✓')).toBeVisible({ timeout: 5000 });

    // Verify both dumps are queued for processing (Sacred Principle #4: Agent Intelligence Mandatory)
    await page.goto(`/baskets/${basketId}/dashboard`);
    
    // Should show processing activity for multiple dumps
    await expect(page.locator('text=processing, text=queue')).toBeVisible({ timeout: 10000 });
    
    // Eventually all should process
    await expect(page.locator('text=complete, text=ready')).toBeVisible({ timeout: 120000 });
  });

  test('file upload triggers async intelligence', async ({ page }) => {
    // Test file upload path with async processing
    await page.goto(`/baskets/${basketId}/new/dumps`);

    // Create file content for upload
    const fileContent = `
# Product Roadmap Document

## Q2 Objectives
- Launch mobile app beta
- Implement advanced analytics
- Expand international markets

## Key Metrics
- User acquisition: 25% increase
- Revenue growth: 40% target
- Customer satisfaction: 95%+ 
    `.trim();

    // Simulate file upload
    const input = page.locator('input[type=file]');
    await input.setInputFiles([
      { name: 'roadmap.md', mimeType: 'text/markdown', buffer: Buffer.from(fileContent) }
    ]);
    
    await page.click('button:has-text("Create")');
    await expect(page.locator('text=✓')).toBeVisible({ timeout: 5000 });

    // Should trigger agent processing for file content
    await expect(page.locator('text=⏳, text=processing')).toBeVisible({ timeout: 3000 });
    await expect(page.locator('text=✅, text=complete')).toBeVisible({ timeout: 90000 });
  });

});