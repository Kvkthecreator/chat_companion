/**
 * Governance-Compliant Capture Tests
 * 
 * Ensures capture workflow respects Sacred Principles and Decision Gateway routing.
 * Tests both direct commit and proposal creation paths.
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { createGovernedDump, createDumpChangeDescriptor } from '@/lib/api/capture';
import { routeChange } from '@/lib/governance/decisionGateway';
import { getWorkspaceFlags } from '@/lib/governance/flagsServer';
import type { ChangeDescriptor } from '@/lib/governance/changeDescriptor';

// Mock modules
vi.mock('@/lib/governance/decisionGateway');
vi.mock('@/lib/governance/flagsServer');

const mockSupabase = {
  from: vi.fn(() => ({
    select: vi.fn(() => ({
      eq: vi.fn(() => ({
        maybeSingle: vi.fn()
      }))
    }))
  })),
  rpc: vi.fn()
};

const mockUserId = '123e4567-e89b-12d3-a456-426614174000';
const mockWorkspaceId = '987fcdeb-51a2-43d1-9f83-123456789abc';
const mockBasketId = '456789ab-cdef-1234-5678-9abcdef01234';

describe('Governance-Compliant Capture', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('createGovernedDump', () => {
    test('should create ChangeDescriptor with CreateDump operation', async () => {
      const mockRouteChange = vi.mocked(routeChange);
      mockRouteChange.mockResolvedValue({
        committed: true,
        decision: { route: 'direct', reason: 'low_risk', effective_blast_radius: 'Local', require_validator: false, validator_mode: 'lenient' },
        execution_summary: { operations_executed: 1, execution_time_ms: 100, timeline_events_emitted: 1 }
      });

      const result = await createGovernedDump(
        mockSupabase as any,
        mockUserId,
        mockWorkspaceId,
        {
          basket_id: mockBasketId,
          text_dump: 'Test capture content',
          source_meta: { client_ts: new Date().toISOString() }
        }
      );

      expect(mockRouteChange).toHaveBeenCalledWith(
        mockSupabase,
        expect.objectContaining({
          entry_point: 'onboarding_dump',
          actor_id: mockUserId,
          workspace_id: mockWorkspaceId,
          basket_id: mockBasketId,
          blast_radius: 'Local',
          ops: expect.arrayContaining([
            expect.objectContaining({
              type: 'CreateDump',
              data: expect.objectContaining({
                text_dump: 'Test capture content',
                dump_request_id: expect.any(String)
              })
            })
          ])
        })
      );

      expect(result.success).toBe(true);
      expect(result.route).toBe('direct');
      expect(result.message).toContain('saved directly');
    });

    test('should create proposal when governance requires it', async () => {
      const mockRouteChange = vi.mocked(routeChange);
      mockRouteChange.mockResolvedValue({
        proposal_id: 'proposal-123',
        decision: { route: 'proposal', reason: 'ep_policy_proposal:onboarding_dump', effective_blast_radius: 'Local', require_validator: true, validator_mode: 'strict' },
        validation_report: { confidence: 0.8, impact_summary: '1 dump creation pending review' }
      });

      const result = await createGovernedDump(
        mockSupabase as any,
        mockUserId,
        mockWorkspaceId,
        {
          basket_id: mockBasketId,
          text_dump: 'Sensitive content requiring review'
        }
      );

      expect(result.success).toBe(true);
      expect(result.route).toBe('proposal');
      expect(result.proposal_id).toBe('proposal-123');
      expect(result.message).toContain('proposed for governance review');
    });

    test('should reject capture without content', async () => {
      await expect(
        createGovernedDump(
          mockSupabase as any,
          mockUserId,
          mockWorkspaceId,
          { basket_id: mockBasketId }
        )
      ).rejects.toThrow('Either text_dump or file_url is required');
    });

    test('should handle Decision Gateway failures gracefully', async () => {
      const mockRouteChange = vi.mocked(routeChange);
      mockRouteChange.mockRejectedValue(new Error('Policy evaluation failed'));

      await expect(
        createGovernedDump(
          mockSupabase as any,
          mockUserId,
          mockWorkspaceId,
          {
            basket_id: mockBasketId,
            text_dump: 'Test content'
          }
        )
      ).rejects.toThrow('Capture workflow failed: Policy evaluation failed');
    });
  });

  describe('createDumpChangeDescriptor', () => {
    test('should create valid ChangeDescriptor for text dump', () => {
      const cd = createDumpChangeDescriptor(
        mockUserId,
        mockWorkspaceId,
        mockBasketId,
        {
          basket_id: mockBasketId,
          text_dump: 'Test capture content',
          source_meta: { client_ts: '2025-09-01T12:00:00Z' }
        }
      );

      expect(cd.entry_point).toBe('onboarding_dump');
      expect(cd.actor_id).toBe(mockUserId);
      expect(cd.workspace_id).toBe(mockWorkspaceId);
      expect(cd.basket_id).toBe(mockBasketId);
      expect(cd.blast_radius).toBe('Local');
      expect(cd.ops).toHaveLength(1);
      expect(cd.ops[0].type).toBe('CreateDump');
      expect(cd.ops[0].data.text_dump).toBe('Test capture content');
      expect(cd.ops[0].data.dump_request_id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);
      expect(cd.provenance).toEqual([{ type: 'user', id: mockUserId }]);
    });

    test('should create valid ChangeDescriptor for file upload', () => {
      const cd = createDumpChangeDescriptor(
        mockUserId,
        mockWorkspaceId,
        mockBasketId,
        {
          basket_id: mockBasketId,
          file_url: 'https://example.com/file.pdf',
          source_meta: { upload_type: 'pdf' }
        }
      );

      expect(cd.ops[0].data.file_url).toBe('https://example.com/file.pdf');
      expect(cd.ops[0].data.text_dump).toBeUndefined();
      expect(cd.ops[0].data.source_meta).toEqual({ upload_type: 'pdf' });
    });
  });

  describe('Sacred Principles Compliance', () => {
    test('should enforce Sacred Principle #1: All mutations through governance', async () => {
      const mockRouteChange = vi.mocked(routeChange);
      mockRouteChange.mockResolvedValue({
        committed: true,
        decision: { route: 'direct', reason: 'governance_disabled', effective_blast_radius: 'Local', require_validator: false, validator_mode: 'lenient' }
      });

      await createGovernedDump(
        mockSupabase as any,
        mockUserId,
        mockWorkspaceId,
        { basket_id: mockBasketId, text_dump: 'test' }
      );

      // Verify that routeChange (Decision Gateway) was called
      expect(mockRouteChange).toHaveBeenCalledOnce();
      expect(mockRouteChange).toHaveBeenCalledWith(
        mockSupabase,
        expect.objectContaining({
          entry_point: 'onboarding_dump'
        })
      );
    });

    test('should respect ep_onboarding_dump policy settings', async () => {
      // This test verifies the Decision Gateway respects workspace settings
      // The actual policy evaluation is tested in policyDecider.test.ts
      const mockRouteChange = vi.mocked(routeChange);
      mockRouteChange.mockResolvedValue({
        proposal_id: 'test-proposal',
        decision: { route: 'proposal', reason: 'ep_policy_proposal:onboarding_dump', effective_blast_radius: 'Local', require_validator: true, validator_mode: 'strict' }
      });

      const result = await createGovernedDump(
        mockSupabase as any,
        mockUserId,
        mockWorkspaceId,
        { basket_id: mockBasketId, text_dump: 'test' }
      );

      expect(result.route).toBe('proposal');
      expect(result.decision_reason).toContain('ep_policy_proposal:onboarding_dump');
    });
  });

  describe('Error Handling', () => {
    test('should handle malformed capture requests', async () => {
      await expect(
        createGovernedDump(
          mockSupabase as any,
          mockUserId,
          mockWorkspaceId,
          { basket_id: mockBasketId, text_dump: '' }
        )
      ).rejects.toThrow('Either text_dump or file_url is required');
    });

    test('should handle network failures in Decision Gateway', async () => {
      const mockRouteChange = vi.mocked(routeChange);
      mockRouteChange.mockRejectedValue(new Error('Network timeout'));

      await expect(
        createGovernedDump(
          mockSupabase as any,
          mockUserId,
          mockWorkspaceId,
          { basket_id: mockBasketId, text_dump: 'test' }
        )
      ).rejects.toThrow('Capture workflow failed: Network timeout');
    });
  });

  describe('Integration with P0 Pipeline Boundary', () => {
    test('should maintain P0 Capture boundary enforcement', () => {
      // This verifies that CreateDump operations maintain the P0->P1 boundary
      // The actual boundary enforcement is in PipelineBoundaryGuard
      const cd = createDumpChangeDescriptor(
        mockUserId,
        mockWorkspaceId,
        mockBasketId,
        { basket_id: mockBasketId, text_dump: 'Raw capture data' }
      );

      // P0 operations should only create dumps, no interpretation
      expect(cd.ops).toHaveLength(1);
      expect(cd.ops[0].type).toBe('CreateDump');
      expect(cd.entry_point).toBe('onboarding_dump');
      
      // Blast radius should be Local for P0 capture
      expect(cd.blast_radius).toBe('Local');
    });
  });
});