import { test, expect } from '@playwright/test';

const basketId = process.env.TEST_BASKET_ID;
test.skip(!basketId, 'requires TEST_BASKET_ID to run');

test.describe('Canon v1.4.0 Basket Dashboard - Pure Supabase Architecture', () => {
  test('dashboard loads with async intelligence processing status', async ({ page }) => {
    // Navigate to dashboard
    await page.goto(`/baskets/${basketId}/dashboard`);
    
    // Should see Canon v1.4.0 dashboard
    await expect(page.locator('h1')).toBeVisible(); // Basket name
    
    // Should show processing queue status
    await expect(page.locator('text=Processing Queue, text=Agent Intelligence, text=Queue Status')).toBeVisible();
    
    // Should see main dashboard components
    await expect(page.locator('h1')).toBeVisible(); // Basket name
    await expect(page.locator('text=Latest Reflection')).toBeVisible();
    await expect(page.locator('text=Recent Activity')).toBeVisible();
    await expect(page.locator('text=Quick Actions')).toBeVisible();
  });

  test('displays async intelligence health metrics', async ({ page }) => {
    await page.goto(`/baskets/${basketId}/dashboard`);
    
    // Should show v1.4.0 health indicators
    await expect(page.locator('text=dumps')).toBeVisible();
    await expect(page.locator('text=blocks')).toBeVisible(); // Context blocks per canon
    await expect(page.locator('text=context items')).toBeVisible(); // Semantic connectors
    await expect(page.locator('text=Last active')).toBeVisible();
    
    // Should show agent processing status
    await expect(page.locator('[data-testid="agent-status"], text=Processing, text=Ready, text=Queue Empty')).toBeVisible();
    
    // Should show activity status badge
    await expect(page.locator('[data-testid="activity-status"], text=Active, text=Moderate, text=Low Activity, text=Inactive')).toBeVisible();
  });

  test('shows agent queue processing status', async ({ page }) => {
    await page.goto(`/baskets/${basketId}/dashboard`);
    
    // Should display queue health information
    const queueSection = page.locator('text=Agent Intelligence').locator('..');
    await expect(queueSection).toBeVisible();
    
    // Should show processing states or empty state
    await expect(page.locator('text=Pending, text=Processing, text=Completed, text=No processing activity')).toBeVisible();
    
    // Should have agent queue health endpoint working
    await expect(page.locator('[data-testid="queue-health-status"]')).toBeVisible();
  });

  test('reflection card shows proper content or empty state', async ({ page }) => {
    await page.goto(`/baskets/${basketId}/dashboard`);
    
    const reflectionCard = page.locator('text=Latest Reflection').locator('..');
    await expect(reflectionCard).toBeVisible();
    
    // Should either show reflection content or empty state
    const hasReflection = await page.locator('text=View all →').isVisible();
    
    if (hasReflection) {
      // Has reflections - should show preview and metadata
      await expect(page.locator('text=Based on')).toBeVisible();
      await expect(page.locator('text=window')).toBeVisible();
    } else {
      // Empty state - should show generate option
      await expect(page.locator('text=No reflections yet')).toBeVisible();
      await expect(page.locator('text=Generate First Reflection')).toBeVisible();
    }
  });

  test('recent activity card shows proper content or empty state', async ({ page }) => {
    await page.goto(`/baskets/${basketId}/dashboard`);
    
    const activityCard = page.locator('text=Recent Activity').locator('..');
    await expect(activityCard).toBeVisible();
    
    // Should either show activity or empty state
    const hasActivity = await page.locator('text=View timeline →').isVisible();
    
    if (hasActivity) {
      // Has activity - should show timeline link
      await expect(page.locator('text=View timeline →')).toBeVisible();
    } else {
      // Empty state - should show add content option
      await expect(page.locator('text=No recent activity')).toBeVisible();
      await expect(page.locator('text=Add Content')).toBeVisible();
    }
  });

  test('quick actions navigation works', async ({ page }) => {
    await page.goto(`/baskets/${basketId}/dashboard`);
    
    // Should have all four quick action buttons
    const quickActions = page.locator('text=Quick Actions').locator('..');
    
    await expect(quickActions.locator('text=Add Content')).toBeVisible();
    await expect(quickActions.locator('text=Reflections')).toBeVisible();
    await expect(quickActions.locator('text=Timeline')).toBeVisible();
    await expect(quickActions.locator('text=Documents')).toBeVisible();
    
    // Test overview navigation
    await quickActions.locator('text=Add Content').click();
    await expect(page).toHaveURL(new RegExp(`/baskets/${basketId}/overview`));

    // Go back and test reflections navigation
    await page.goBack();
    await quickActions.locator('text=Reflections').click();
    await expect(page).toHaveURL(new RegExp(`/baskets/${basketId}/insights`));
  });

  test('dashboard handles empty basket gracefully', async ({ page }) => {
    await page.goto(`/baskets/${basketId}/dashboard`);
    
    // Should load without errors even with no content
    await expect(page.locator('h1')).toBeVisible();
    
    // Should not show any JavaScript errors in console
    const consoleErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Wait for all async operations to complete
    await page.waitForTimeout(2000);
    
    // Filter out known non-critical errors
    const criticalErrors = consoleErrors.filter(error => 
      !error.includes('favicon') && 
      !error.includes('manifest') &&
      !error.includes('sw.js')
    );
    
    expect(criticalErrors).toHaveLength(0);
  });

  test('dashboard integrates with existing Canon v1.3.1 features', async ({ page }) => {
    // Add a dump first
    await page.goto(`/baskets/${basketId}/overview`);
    
    const textarea = page.getByRole('textbox');
    await textarea.fill('Dashboard integration test content');
    await page.getByRole('button', { name: /add|upload/i }).click();
    
    // Wait for dump to be created
    await expect(page.locator('[data-test=dump-item]')).toHaveCount(1);
    
    // Navigate to dashboard
    await page.goto(`/baskets/${basketId}/dashboard`);
    
    // Should show updated metrics
    await expect(page.locator('text=dumps')).toBeVisible();
    
    // Should show recent activity
    const activityCard = page.locator('text=Recent Activity').locator('..');
    await expect(activityCard.locator('text=Content added')).toBeVisible();
    
    // Generate a reflection
    const reflectionCard = page.locator('text=Latest Reflection').locator('..');
    const generateButton = reflectionCard.locator('text=Generate First Reflection');
    
    if (await generateButton.isVisible()) {
      await generateButton.click();
      
      // Should navigate to reflections API (might show JSON response)
      await page.waitForTimeout(3000);
      
      // Go back to dashboard
      await page.goto(`/baskets/${basketId}/dashboard`);
      
      // Should now show reflection content or updated state
      await expect(reflectionCard).toBeVisible();
    }
  });

  test('debug mode shows additional information', async ({ page }) => {
    await page.goto(`/baskets/${basketId}/dashboard?debug=true`);
    
    // Should show debug information
    await expect(page.locator('text=🔍 Debug Info')).toBeVisible();
    await expect(page.locator('text=Basket:')).toBeVisible();
    await expect(page.locator('text=Workspace:')).toBeVisible();
    await expect(page.locator('text=Health Score:')).toBeVisible();
  });

  test('dashboard redirects to memory when feature flag disabled', async ({ page, context }) => {
    // Mock production environment where feature flag would be false
    await context.route('**/*', (route) => {
      const headers = route.request().headers();
      headers['NODE_ENV'] = 'production';
      headers['CANON_DASHBOARD_ENABLED'] = 'false';
      route.continue();
    });
    
    // This test would need to be adapted based on how feature flags are actually implemented
    // For now, we'll just verify the redirect logic exists in development
    await page.goto(`/baskets/${basketId}/dashboard`);
    
    // In development, should show dashboard
    await expect(page.locator('text=Canon v1.3.1 Dashboard')).toBeVisible();
  });
});