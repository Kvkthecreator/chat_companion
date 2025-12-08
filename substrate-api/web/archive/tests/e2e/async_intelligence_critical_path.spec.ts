import { test, expect } from '@playwright/test';

/**
 * Critical Path Test: Canon v1.4.0 Async Intelligence System
 * 
 * Tests the core YARNNN value proposition:
 * Raw Capture → Agent Processing → Substrate Evolution → Intelligence Delivery
 * 
 * Sacred Principle #4: "Agent Intelligence is Mandatory"
 */

const basketId = process.env.TEST_BASKET_ID;
test.skip(!basketId, 'requires TEST_BASKET_ID to run');

test.describe('Canon v1.4.0 Critical Path: Async Intelligence System', () => {
  test('full flow: dump creation → queue processing → substrate creation', async ({ page }) => {
    // Step 1: Navigate to dump creation
    await page.goto(`/baskets/${basketId}/new/dumps`);
    await expect(page.locator('h1, h2')).toContainText(['New', 'Dump', 'Share']);

    // Step 2: Create a rich dump with meaningful content
    const testContent = `
# Project Strategy Meeting Notes

## Key Insights
- User engagement has increased 40% since implementing new onboarding
- Technical debt in authentication system needs addressing
- AI integration showing promising early results

## Action Items  
- Schedule security audit for Q2
- Implement new user analytics dashboard
- Research competitive landscape for AI features

## Questions
- How can we improve conversion rates further?
- What's the timeline for the mobile app redesign?
- Should we prioritize performance or new features next quarter?
    `.trim();

    // Fill in the dump content
    await page.fill('[data-testid="dump-content"], textarea, [placeholder*="content"], [placeholder*="dump"], [name="content"]', testContent);
    
    // Submit the dump
    await page.click('[data-testid="create-dump"], [type="submit"], button:has-text("Create"), button:has-text("Share"), button:has-text("Save")');

    // Step 3: Verify immediate user feedback (Sacred Principle: immediate UX)
    await expect(page.locator('text=✓, text=Success, text=Created, text=Shared')).toBeVisible({ timeout: 5000 });
    
    // Step 4: Verify queue processing initiated
    // Should show processing status immediately
    await expect(page.locator('text=⏳ Analyzing, text=Processing, text=Agent working')).toBeVisible({ timeout: 3000 });

    // Step 5: Wait for agent processing to complete (up to 60s for comprehensive test)
    // Agent Intelligence is Mandatory - must eventually process
    await expect(page.locator('text=✅ Analysis complete, text=Processing complete, text=Intelligence ready')).toBeVisible({ timeout: 60000 });

    // Step 6: Navigate back to basket to verify substrate creation
    await page.goto(`/baskets/${basketId}`);

    // Step 7: Verify substrate creation (All Substrates are Peers principle)
    // Should see new blocks created by agent
    await expect(page.locator('text=blocks, text=insights, text=context')).toBeVisible({ timeout: 5000 });
    
    // Should see increased substrate count
    await expect(page.locator('[data-testid="substrate-count"], text=Total')).toBeVisible();

    // Step 8: Verify timeline events created (append-only memory stream)
    await page.goto(`/baskets/${basketId}/timeline`);
    await expect(page.locator('text=dump created, text=agent processed, text=blocks created')).toBeVisible({ timeout: 5000 });

    // Step 9: Verify reflection system can access new substrate
    await page.goto(`/baskets/${basketId}/reflections`);
    
    // Reflections are derived read-models - should incorporate new substrate
    await expect(page.locator('text=reflection, text=pattern, text=insight')).toBeVisible({ timeout: 10000 });
  });

  test('queue health monitoring and error handling', async ({ page }) => {
    // Test the monitoring endpoints
    await page.goto(`/baskets/${basketId}/dashboard`);

    // Should show queue health status
    await expect(page.locator('[data-testid="queue-health"], text=Queue Status')).toBeVisible();

    // Test queue health API endpoint
    const response = await page.request.get('/api/health/queue');
    expect(response.ok()).toBeTruthy();
    
    const queueHealth = await response.json();
    expect(queueHealth).toHaveProperty('status');
    expect(queueHealth.status).toMatch(/healthy|unhealthy/);
  });

  test('concurrent dump processing (scale test)', async ({ page, context }) => {
    // Test multiple dumps can be processed concurrently
    const dumps = [
      'Technical requirements for API v2.0',
      'User feedback from latest feature release', 
      'Competitive analysis of market trends'
    ];

    // Create multiple dumps rapidly
    for (let i = 0; i < dumps.length; i++) {
      const newPage = await context.newPage();
      await newPage.goto(`/baskets/${basketId}/new/dumps`);
      await newPage.fill('[data-testid="dump-content"], textarea', dumps[i]);
      await newPage.click('[data-testid="create-dump"], [type="submit"]');
      
      // Don't wait for processing, just verify creation
      await expect(newPage.locator('text=✓, text=Success')).toBeVisible({ timeout: 5000 });
      await newPage.close();
    }

    // Verify all dumps eventually process (queue can handle concurrent load)
    await page.goto(`/baskets/${basketId}/dashboard`);
    
    // Wait for queue to clear (all dumps processed)
    await expect(page.locator('text=Queue Empty, text=No pending')).toBeVisible({ timeout: 120000 });
  });

  test('agent processing failure recovery', async ({ page }) => {
    // Test error handling and retry mechanisms
    
    // Create a dump that might cause processing issues
    await page.goto(`/baskets/${basketId}/new/dumps`);
    
    // Very large content that might timeout
    const stressContent = 'A'.repeat(10000) + '\n' + 'B'.repeat(10000);
    await page.fill('[data-testid="dump-content"], textarea', stressContent);
    await page.click('[data-testid="create-dump"], [type="submit"]');

    // Should still get immediate feedback
    await expect(page.locator('text=✓, text=Success')).toBeVisible({ timeout: 5000 });

    // Processing may take longer or fail, but system should handle gracefully
    await page.waitForTimeout(10000); // Give processing time
    
    // Should show either success or graceful error handling
    await expect(page.locator('text=✅ Analysis complete, text=⚠️ Analysis failed, text=🔄 Retrying')).toBeVisible({ timeout: 30000 });
  });
});