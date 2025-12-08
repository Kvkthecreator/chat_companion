import { test, expect } from '@playwright/test';

/**
 * Contract Validation Test Suite
 * 
 * Validates that Frontend ↔ Backend ↔ Database contracts are aligned
 * Tests the integration points that have historically caused issues
 */

const basketId = process.env.TEST_BASKET_ID;
test.skip(!basketId, 'requires TEST_BASKET_ID to run');

test.describe('Contract Validation: Frontend ↔ Backend ↔ Database', () => {
  
  test('context items contract alignment', async ({ page }) => {
    // Test that context_items table structure matches frontend expectations
    
    const response = await page.request.get(`/api/baskets/${basketId}/context`);
    expect(response.ok()).toBeTruthy();
    
    const contextItems = await response.json();
    
    if (contextItems.length > 0) {
      const item = contextItems[0];
      
      // Verify required fields per YARNNN_CANON v1.4.0
      expect(item).toHaveProperty('id');
      expect(item).toHaveProperty('basket_id');
      expect(item).toHaveProperty('type'); // Not context_type
      expect(item).toHaveProperty('content'); // Not content_text  
      expect(item).toHaveProperty('status');
      
      // Optional fields should be present or null
      expect('title' in item).toBeTruthy();
      expect('description' in item).toBeTruthy();
      expect('confidence_score' in item).toBeTruthy();
    }
  });

  test('raw dumps contract alignment', async ({ page }) => {
    // Test dumps creation and retrieval contracts
    
    const response = await page.request.get(`/api/baskets/${basketId}/dumps`);
    expect(response.ok()).toBeTruthy();
    
    const dumps = await response.json();
    
    if (dumps.length > 0) {
      const dump = dumps[0];
      
      // Core dump fields
      expect(dump).toHaveProperty('id');
      expect(dump).toHaveProperty('basket_id');
      expect(dump).toHaveProperty('body_md'); // Canonical field name
      expect(dump).toHaveProperty('created_at');
      
      // Should match database schema
      expect(dump.basket_id).toBe(basketId);
    }
  });

  test('blocks (context_blocks) contract alignment', async ({ page }) => {
    // Test blocks/context_blocks contract consistency
    
    const response = await page.request.get(`/api/baskets/${basketId}/building-blocks`);
    expect(response.ok()).toBeTruthy();
    
    const buildingBlocksData = await response.json();
    const captures = buildingBlocksData.captures || [];
    const orphanBlocks = buildingBlocksData.orphans?.blocks || [];
    const allBlocks = [
      ...captures.flatMap((capture: any) => capture.derived_blocks || []),
      ...orphanBlocks,
    ];

    if (allBlocks.length > 0) {
      const block = allBlocks[0];

      // Block structure per canon
      expect(block).toHaveProperty('id');
      expect(block).toHaveProperty('semantic_type');
      // Derived block payload exposes metadata rather than raw content; ensure canonical props exist
      expect(block).toHaveProperty('created_at');

      // State should be valid when provided
      if (block.state) {
        expect(['PROPOSED', 'ACCEPTED', 'LOCKED', 'CONSTANT', 'REJECTED', 'SUPERSEDED']).toContain(block.state);
      }
    }
  });

  test('agent processing queue contract', async ({ page }) => {
    // Test queue status API contracts
    
    const healthResponse = await page.request.get('/api/health/queue');
    expect(healthResponse.ok()).toBeTruthy();
    
    const queueHealth = await healthResponse.json();
    
    // Queue health structure
    expect(queueHealth).toHaveProperty('status');
    expect(['healthy', 'unhealthy']).toContain(queueHealth.status);
    
    if (queueHealth.status === 'healthy') {
      expect(queueHealth).toHaveProperty('processor_running');
      expect(typeof queueHealth.processor_running).toBe('boolean');
    }
  });

  test('workspace isolation contract', async ({ page }) => {
    // Test that workspace isolation is properly enforced
    
    // Should only see data for current workspace
    const basketResponse = await page.request.get('/api/baskets');
    expect(basketResponse.ok()).toBeTruthy();
    
    const baskets = await basketResponse.json();
    
    // All baskets should belong to same workspace (single workspace model)
    if (baskets.length > 1) {
      const workspaceIds = [...new Set(baskets.map((b: any) => b.workspace_id))];
      expect(workspaceIds).toHaveLength(1); // Single workspace guarantee
    }
  });

  test('timeline events contract alignment', async ({ page }) => {
    // Test timeline events structure
    
    const response = await page.request.get(`/api/baskets/${basketId}/timeline`);
    expect(response.ok()).toBeTruthy();
    
    const timeline = await response.json();
    
    if (timeline.length > 0) {
      const event = timeline[0];
      
      // Timeline event structure
      expect(event).toHaveProperty('id');
      expect(event).toHaveProperty('basket_id');
      expect(event).toHaveProperty('event_type');
      expect(event).toHaveProperty('created_at');
      expect(event).toHaveProperty('payload');
      
      // Should be append-only (chronological)
      if (timeline.length > 1) {
        const first = new Date(timeline[0].created_at);
        const second = new Date(timeline[1].created_at);
        expect(first.getTime()).toBeGreaterThanOrEqual(second.getTime()); // Descending order
      }
    }
  });

  test('reflection system contract alignment', async ({ page }) => {
    // Test reflections are properly derived (read-model)
    
    const response = await page.request.get(`/api/baskets/${basketId}/reflections`);
    expect(response.ok()).toBeTruthy();
    
    const reflections = await response.json();
    
    if (reflections.length > 0) {
      const reflection = reflections[0];
      
      // Reflection structure (derived from substrate)
      expect(reflection).toHaveProperty('id');
      expect(reflection).toHaveProperty('basket_id');
      expect(reflection).toHaveProperty('content');
      expect(reflection).toHaveProperty('reflection_type');
      
      // Should be workspace-scoped
      expect(reflection.basket_id).toBe(basketId);
    }
  });

  test('substrate equality contract (all peers)', async ({ page }) => {
    // Test that all substrate types are treated as peers
    
    // Get all substrate types for basket
    const [dumps, blocks, contextItems, timeline] = await Promise.all([
      page.request.get(`/api/baskets/${basketId}/dumps`).then(r => r.json()),
      page.request.get(`/api/baskets/${basketId}/blocks`).then(r => r.json()),
      page.request.get(`/api/baskets/${basketId}/context`).then(r => r.json()),
      page.request.get(`/api/baskets/${basketId}/timeline`).then(r => r.json())
    ]);

    // All should be accessible (no hierarchy)
    expect(Array.isArray(dumps)).toBeTruthy();
    expect(Array.isArray(blocks)).toBeTruthy();
    expect(Array.isArray(contextItems)).toBeTruthy();
    expect(Array.isArray(timeline)).toBeTruthy();

    // All should share common patterns (workspace isolation, timestamps)
    const allSubstrate = [...dumps, ...blocks, ...contextItems, ...timeline];
    
    if (allSubstrate.length > 0) {
      allSubstrate.forEach(item => {
        expect(item).toHaveProperty('id');
        expect(item).toHaveProperty('basket_id');
        expect(item.basket_id).toBe(basketId);
      });
    }
  });

  test('authentication contract validation', async ({ page }) => {
    // Test auth headers and JWT validation
    
    // Make authenticated request
    const response = await page.request.get('/api/baskets');
    expect(response.ok()).toBeTruthy();
    
    // Should have proper CORS headers
    const headers = response.headers();
    expect(headers['access-control-allow-origin']).toBeDefined();
    
    // Should reject unauthenticated requests
    const unauthResponse = await page.request.get('/api/baskets', {
      headers: {} // No auth headers
    });
    
    // Should either redirect to login or return 401
    expect([401, 302, 403]).toContain(unauthResponse.status());
  });

  test('error response contract consistency', async ({ page }) => {
    // Test that error responses follow consistent structure
    
    // Try to access non-existent basket
    const response = await page.request.get('/api/baskets/00000000-0000-0000-0000-000000000000');
    expect([404, 403]).toContain(response.status());
    
    if (response.status() === 404) {
      const error = await response.json();
      expect(error).toHaveProperty('error');
      expect(typeof error.error).toBe('string');
    }
  });
});
