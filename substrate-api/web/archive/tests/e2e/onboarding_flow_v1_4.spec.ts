import { test, expect } from '@playwright/test';

/**
 * Onboarding Flow Test - Canon v1.4.0
 * 
 * Tests the complete user journey from welcome → onboarding → active basket
 * Validates async intelligence integration during onboarding
 */

test.describe('Canon v1.4.0 Onboarding Flow with Async Intelligence', () => {
  
  test('complete onboarding journey with agent processing', async ({ page }) => {
    // Step 1: Start at welcome page
    await page.goto('/welcome');
    
    // Should see onboarding UI
    await expect(page.locator('text=Welcome, text=Get Started, text=Begin')).toBeVisible({ timeout: 5000 });
    
    // Step 2: Initiate onboarding process
    await page.click('button:has-text("Get Started"), button:has-text("Begin"), button:has-text("Start"), [data-testid="start-onboarding"]');
    
    // Step 3: Fill in initial project information
    await expect(page.locator('text=Project, text=About, text=Tell us')).toBeVisible({ timeout: 5000 });
    
    const projectInfo = `
# My SaaS Product Strategy

## Vision
Building a next-generation productivity platform that helps remote teams collaborate more effectively.

## Current Challenges
- User retention is lower than industry average
- Feature adoption rates need improvement  
- Customer support scaling issues

## Key Goals
- Increase monthly active users by 50%
- Improve feature discoverability
- Reduce customer acquisition cost
- Build stronger product-market fit

## Market Analysis  
The remote work space is growing rapidly, with increasing demand for integrated collaboration tools.
Our main competitors include Slack, Notion, and Asana, but we have unique advantages in AI-powered insights.
    `.trim();
    
    // Fill in comprehensive project information
    await page.fill('textarea, [data-testid="project-description"], [placeholder*="project"], [name="content"]', projectInfo);
    
    // Step 4: Submit onboarding information
    await page.click('button:has-text("Continue"), button:has-text("Next"), button:has-text("Create"), [data-testid="submit-onboarding"]');
    
    // Step 5: Should get immediate feedback (Sacred Principle: immediate UX)
    await expect(page.locator('text=✓, text=Success, text=Created, text=Welcome')).toBeVisible({ timeout: 5000 });
    
    // Step 6: Should show async intelligence processing has begun
    await expect(page.locator('text=⏳ Analyzing, text=Processing, text=Setting up')).toBeVisible({ timeout: 3000 });
    
    // Step 7: Should be redirected to new basket
    await expect(page).toHaveURL(/\/baskets\/[a-f0-9-]+/);
    
    // Get the basket ID from URL for further testing
    const url = page.url();
    const basketId = url.match(/\/baskets\/([a-f0-9-]+)/)?.[1];
    expect(basketId).toBeTruthy();
    
    // Step 8: Verify onboarding dump was created and queued for processing
    await expect(page.locator('text=onboarding, text=initial, text=project')).toBeVisible({ timeout: 5000 });
    
    // Step 9: Wait for agent processing to complete (Agent Intelligence is Mandatory)
    await expect(page.locator('text=✅ Analysis complete, text=Processing complete, text=Ready')).toBeVisible({ timeout: 90000 });
    
    // Step 10: Verify substrate was created from onboarding content
    
    // Should have generated context blocks
    await page.goto(`/baskets/${basketId}/blocks`);
    await expect(page.locator('text=blocks, text=insights')).toBeVisible({ timeout: 5000 });
    
    // Should have extracted context items  
    await page.goto(`/baskets/${basketId}`);
    await expect(page.locator('text=context, text=goals, text=challenges')).toBeVisible({ timeout: 5000 });
    
    // Step 11: Verify system genesis context item was created
    await expect(page.locator('text=identity_genesis, text=yarnnn_system')).toBeVisible({ timeout: 5000 });
    
    // Step 12: Test that new dumps continue to process
    await page.goto(`/baskets/${basketId}/new/dumps`);
    
    const followupContent = `
# Follow-up Meeting Notes

## User Research Findings
- 73% of users want better mobile experience
- Integration with calendar tools is high priority
- Notification fatigue is a real concern

## Next Steps
- Schedule user interviews for next week
- Create mobile app prototype
- Review integration roadmap
    `.trim();
    
    await page.fill('textarea, [data-testid="dump-content"]', followupContent);
    await page.click('[data-testid="create-dump"], button:has-text("Create")');
    
    // Should continue to process new dumps
    await expect(page.locator('text=⏳ Analyzing')).toBeVisible({ timeout: 3000 });
    await expect(page.locator('text=✅ Analysis complete')).toBeVisible({ timeout: 60000 });
  });
  
  test('onboarding error handling and recovery', async ({ page }) => {
    // Test graceful handling of onboarding issues
    
    await page.goto('/welcome');
    
    // Try onboarding with minimal content
    await page.click('button:has-text("Get Started"), [data-testid="start-onboarding"]');
    
    // Submit empty or very minimal content
    await page.fill('textarea', 'Test project');
    await page.click('button:has-text("Continue"), [data-testid="submit-onboarding"]');
    
    // Should still create basket and process gracefully
    await expect(page.locator('text=✓, text=Success')).toBeVisible({ timeout: 5000 });
    
    // Should handle minimal content gracefully in processing
    await expect(page).toHaveURL(/\/baskets\/[a-f0-9-]+/);
    
    // Processing should complete even with minimal content
    await expect(page.locator('text=✅, text=complete, text=ready')).toBeVisible({ timeout: 60000 });
  });
  
  test('onboarding redirects and URL handling', async ({ page }) => {
    // Test proper URL redirects during onboarding flow
    
    await page.goto('/welcome');
    await page.click('button:has-text("Get Started")');
    
    // Fill and submit onboarding
    await page.fill('textarea', 'Strategic planning for Q2 product development initiatives.');
    await page.click('button:has-text("Continue")');
    
    // Should redirect with onboarded query parameter
    await expect(page).toHaveURL(/\/baskets\/[a-f0-9-]+.*onboarded=1/);
    
    // Should show onboarding completion message
    await expect(page.locator('text=onboarding complete, text=welcome, text=getting started')).toBeVisible();
  });
  
  test('workspace and basket initialization during onboarding', async ({ page }) => {
    // Test that onboarding properly initializes workspace and basket
    
    await page.goto('/welcome');
    await page.click('button:has-text("Get Started")');
    
    await page.fill('textarea', 'E-commerce platform development roadmap and technical requirements.');
    await page.click('button:has-text("Continue")');
    
    // Wait for redirect
    await expect(page).toHaveURL(/\/baskets\/[a-f0-9-]+/);
    
    const basketId = page.url().match(/\/baskets\/([a-f0-9-]+)/)?.[1];
    
    // Verify basket was created with proper structure
    const basketResponse = await page.request.get(`/api/baskets/${basketId}`);
    expect(basketResponse.ok()).toBeTruthy();
    
    const basket = await basketResponse.json();
    expect(basket).toHaveProperty('id', basketId);
    expect(basket).toHaveProperty('workspace_id');
    expect(basket).toHaveProperty('name');
    expect(basket.state).toBe('ACTIVE'); // Should be active after onboarding
  });
});