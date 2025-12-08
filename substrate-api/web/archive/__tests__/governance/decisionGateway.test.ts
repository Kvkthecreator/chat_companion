import { describe, it, expect, vi, beforeEach } from 'vitest';
import { routeChange } from '@/lib/governance/decisionGateway';
import { 
  createManualEditDescriptor,
  createDumpExtractionDescriptor, 
  computeOperationRisk,
  summarizeChange
} from '@/lib/governance/changeDescriptor';

// Mock dependencies
vi.mock('@/lib/governance/flagsServer');
vi.mock('@/lib/governance/policyDecider');

describe('DecisionGateway', () => {
  let mockSupabase: any;

  beforeEach(() => {
    mockSupabase = {
      from: vi.fn().mockReturnThis(),
      select: vi.fn().mockReturnThis(),
      insert: vi.fn().mockReturnThis(),
      update: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      single: vi.fn().mockReturnThis(),
      rpc: vi.fn().mockReturnThis()
    };

    // Reset all mocks
    vi.clearAllMocks();
  });

  describe('Change routing', () => {
    it('should route low-risk changes to direct commit', async () => {
      // Mock workspace flags (direct policy)
      const mockGetWorkspaceFlags = await import('@/lib/governance/flagsServer');
      vi.mocked(mockGetWorkspaceFlags.getWorkspaceFlags).mockResolvedValue({
        governance_enabled: true,
        direct_substrate_writes: true,
        ep: { manual_edit: 'direct' },
        default_blast_radius: 'Local'
      } as any);

      // Mock policy decision
      const mockPolicyDecider = await import('@/lib/governance/policyDecider');
      vi.mocked(mockPolicyDecider.decide).mockReturnValue({
        route: 'direct',
        require_validator: false,
        validator_mode: 'lenient',
        effective_blast_radius: 'Local',
        reason: 'ep_policy_direct:manual_edit'
      });

      // Mock successful operation execution
      mockSupabase.from.mockImplementation((table: string) => {
        if (table === 'context_blocks') {
          return {
            insert: vi.fn().mockReturnValue({
              select: vi.fn().mockReturnValue({
                single: vi.fn().mockResolvedValue({
                  data: { id: 'block-123' },
                  error: null
                })
              })
            })
          };
        }
        return mockSupabase;
      });

      const changeDescriptor = {
        entry_point: 'manual_edit' as const,
        actor_id: 'user-123',
        workspace_id: 'workspace-456',
        basket_id: 'basket-789',
        ops: [{
          type: 'CreateBlock' as const,
          data: { content: 'Test goal', semantic_type: 'goal' }
        }]
      };

      const result = await routeChange(mockSupabase, changeDescriptor);

      expect(result.committed).toBe(true);
      expect(result.proposal_id).toBeUndefined();
      expect(result.execution_summary?.operations_executed).toBe(1);
    });

    it('should route high-risk changes to proposal', async () => {
      // Mock workspace flags (proposal policy)
      const mockGetWorkspaceFlags = await import('@/lib/governance/flagsServer');
      vi.mocked(mockGetWorkspaceFlags.getWorkspaceFlags).mockResolvedValue({
        governance_enabled: true,
        validator_required: true,
        ep: { manual_edit: 'proposal' },
        default_blast_radius: 'Scoped'
      } as any);

      // Mock policy decision
      const mockPolicyDecider = await import('@/lib/governance/policyDecider');
      vi.mocked(mockPolicyDecider.decide).mockReturnValue({
        route: 'proposal',
        require_validator: true,
        validator_mode: 'strict',
        effective_blast_radius: 'Global',
        reason: 'ep_policy_proposal:manual_edit'
      });

      // Mock validator API
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue({
          confidence: 0.8,
          dupes: [],
          ontology_hits: ['strategy'],
          suggested_merges: [],
          warnings: [],
          impact_summary: '1 CreateBlock operation - high confidence'
        })
      });

      // Mock proposal creation
      mockSupabase.from.mockImplementation((table: string) => {
        if (table === 'proposals') {
          return {
            insert: vi.fn().mockReturnValue({
              select: vi.fn().mockReturnValue({
                single: vi.fn().mockResolvedValue({
                  data: { id: 'proposal-abc' },
                  error: null
                })
              })
            })
          };
        }
        return mockSupabase;
      });

      const changeDescriptor = {
        entry_point: 'manual_edit' as const,
        actor_id: 'user-123',
        workspace_id: 'workspace-456',
        basket_id: 'basket-789',
        blast_radius: 'Global' as const,
        ops: [{
          type: 'PromoteScope' as const,
          data: { block_id: 'block-123', to_scope: 'GLOBAL' }
        }]
      };

      const result = await routeChange(mockSupabase, changeDescriptor);

      expect(result.committed).toBeUndefined();
      expect(result.proposal_id).toBe('proposal-abc');
      expect(result.validation_report?.confidence).toBe(0.8);
    });

    it('should handle validation errors gracefully', async () => {
      const invalidDescriptor = {
        entry_point: 'manual_edit' as const,
        // Missing required fields
        ops: []
      } as any;

      await expect(
        routeChange(mockSupabase, invalidDescriptor)
      ).rejects.toThrow('Invalid ChangeDescriptor');
    });
  });

  describe('Helper functions', () => {
    it('should create manual edit descriptor with correct defaults', () => {
      const cd = createManualEditDescriptor(
        'user-123',
        'workspace-456',
        'basket-789',
        [{ type: 'CreateBlock', data: { content: 'Manual goal', semantic_type: 'goal' } }]
      );

      expect(cd.entry_point).toBe('manual_edit');
      expect(cd.blast_radius).toBe('Local');
      expect(cd.provenance).toEqual([{ type: 'user', id: 'user-123' }]);
    });

    it('should create dump extraction descriptor with agent provenance', () => {
      const cd = createDumpExtractionDescriptor(
        'user-123',
        'workspace-456',
        'basket-789',
        'dump-abc',
        [{ type: 'CreateBlock', data: { content: 'Extracted goal', semantic_type: 'goal' } }]
      );

      expect(cd.entry_point).toBe('onboarding_dump');
      expect(cd.blast_radius).toBe('Scoped');
      expect(cd.provenance).toEqual([
        { type: 'dump', id: 'dump-abc' },
        { type: 'agent', id: 'P1_SUBSTRATE' }
      ]);
    });

    // Test removed: document_edit entry point and DocumentEdit operations no longer exist
    // Documents are now artifacts (not substrates) per Canon v2.0
  });

  describe('Risk computation', () => {
    it('should assess operation risk correctly', () => {
      const mediumRiskOps = [
        { type: 'CreateBlock', data: { content: 'Simple goal', semantic_type: 'goal' } }
      ];

      const mediumRiskOps2 = [
        { type: 'MergeContextItems', data: { from_ids: ['a', 'b'], canonical_id: 'c' } }
      ];

      const highRiskOps = [
        { type: 'PromoteScope', data: { block_id: 'block-1', to_scope: 'GLOBAL' } }
      ];

      expect(computeOperationRisk(mediumRiskOps).scope_impact).toBe('medium');
      expect(computeOperationRisk(mediumRiskOps2).scope_impact).toBe('medium');
      expect(computeOperationRisk(highRiskOps).scope_impact).toBe('high');
    });

    it('should count operations and types correctly', () => {
      const mixedOps = [
        { type: 'CreateBlock', data: { content: 'Goal 1', semantic_type: 'goal' } },
        { type: 'CreateBlock', data: { content: 'Goal 2', semantic_type: 'goal' } },
        { type: 'CreateContextItem', data: { label: 'Context 1' } }
      ];

      const risk = computeOperationRisk(mixedOps);

      expect(risk.operation_count).toBe(3);
      expect(risk.operation_types).toEqual(['CreateBlock', 'CreateContextItem']);
    });
  });

  describe('Change summarization', () => {
    it('should create readable change summaries', () => {
      const change = {
        entry_point: 'manual_edit' as const,
        actor_id: 'user-123',
        workspace_id: 'workspace-456',
        blast_radius: 'Global' as const,
        ops: [
          { type: 'PromoteScope', data: { block_id: 'block-1', to_scope: 'GLOBAL' } },
          { type: 'CreateBlock', data: { content: 'New goal', semantic_type: 'goal' } }
        ]
      };

      const summary = summarizeChange(change);

      expect(summary).toBe('manual_edit: 2 ops (PromoteScope, CreateBlock) [Global]');
    });
  });
});