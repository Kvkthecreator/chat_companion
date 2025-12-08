import { describe, it, expect } from 'vitest';
import { 
  validateChangeDescriptor, 
  createManualEditDescriptor,
  createDumpExtractionDescriptor,
  summarizeChange,
  computeOperationRisk
} from '@/lib/governance/changeDescriptor';

describe('ChangeDescriptor', () => {
  describe('Validation', () => {
    it('should validate complete change descriptor', () => {
      const cd = {
        entry_point: 'manual_edit' as const,
        actor_id: 'user-123',
        workspace_id: 'workspace-456',
        basket_id: 'basket-789',
        ops: [{
          type: 'CreateBlock' as const,
          data: { content: 'Test goal', semantic_type: 'goal' }
        }]
      };

      const result = validateChangeDescriptor(cd);

      expect(result.valid).toBe(true);
      expect(result.errors).toEqual([]);
    });

    it('should reject missing required fields', () => {
      const incomplete = {
        entry_point: 'manual_edit' as const,
        // Missing actor_id, workspace_id, ops
      } as any;

      const result = validateChangeDescriptor(incomplete);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('actor_id required');
      expect(result.errors).toContain('workspace_id required');
      expect(result.errors).toContain('ops array required and non-empty');
    });

    it('should validate operation-specific requirements', () => {
      const invalidOps = {
        entry_point: 'manual_edit' as const,
        actor_id: 'user-123',
        workspace_id: 'workspace-456',
        ops: [
          { type: 'CreateBlock', data: {} }, // Missing content and semantic_type
          { type: 'CreateContextItem', data: {} }, // Missing label
          { type: 'ReviseBlock', data: {} } // Missing block_id
        ]
      };

      const result = validateChangeDescriptor(invalidOps);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('ops[0].data.content required for CreateBlock');
      expect(result.errors).toContain('ops[0].data.semantic_type required for CreateBlock');
      expect(result.errors).toContain('ops[1].data.label required for CreateContextItem');
      expect(result.errors).toContain('ops[2].data.block_id required for ReviseBlock');
    });

    it('should validate blast radius values', () => {
      const invalidBlastRadius = {
        entry_point: 'manual_edit' as const,
        actor_id: 'user-123',
        workspace_id: 'workspace-456',
        blast_radius: 'Invalid' as any,
        ops: [{ type: 'CreateBlock', data: { content: 'Test', semantic_type: 'goal' } }]
      };

      const result = validateChangeDescriptor(invalidBlastRadius);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('blast_radius must be Local, Scoped, or Global');
    });
  });

  describe('Helper constructors', () => {
    it('should create manual edit descriptor with defaults', () => {
      const cd = createManualEditDescriptor(
        'user-123',
        'workspace-456', 
        'basket-789',
        [{ type: 'CreateBlock', data: { content: 'Manual goal', semantic_type: 'goal' } }]
      );

      expect(cd.entry_point).toBe('manual_edit');
      expect(cd.actor_id).toBe('user-123');
      expect(cd.workspace_id).toBe('workspace-456');
      expect(cd.basket_id).toBe('basket-789');
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

  describe('Risk assessment', () => {
    it('should assess medium risk for substrate operations', () => {
      const blockOps = [
        { type: 'CreateBlock', data: { content: 'Simple goal', semantic_type: 'goal' } }
      ];

      const risk = computeOperationRisk(blockOps);

      expect(risk.scope_impact).toBe('medium');
      expect(risk.operation_count).toBe(1);
      expect(risk.operation_types).toEqual(['CreateBlock']);
    });

    it('should assess medium risk for relationship operations', () => {
      const mediumOps = [
        { type: 'MergeContextItems', data: { from_ids: ['a', 'b'], canonical_id: 'c' } },
        { type: 'AttachContextItem', data: { context_item_id: 'ci-1', target_id: 'block-1', target_type: 'block' } }
      ];

      const risk = computeOperationRisk(mediumOps);

      expect(risk.scope_impact).toBe('medium');
      expect(risk.operation_count).toBe(2);
      expect(risk.operation_types).toContain('MergeContextItems');
      expect(risk.operation_types).toContain('AttachContextItem');
    });

    it('should assess high risk for scope promotion operations', () => {
      const highOps = [
        { type: 'PromoteScope', data: { block_id: 'block-1', to_scope: 'GLOBAL' } },
        { type: 'Delete', data: { target_id: 'item-1', target_type: 'block' } }
      ];

      const risk = computeOperationRisk(highOps);

      expect(risk.scope_impact).toBe('high');
      expect(risk.operation_types).toContain('PromoteScope');
      expect(risk.operation_types).toContain('Delete');
    });
  });

  describe('Change summarization', () => {
    it('should create readable summary of change', () => {
      const complexChange = {
        entry_point: 'manual_edit' as const,
        actor_id: 'user-123',
        workspace_id: 'workspace-456',
        blast_radius: 'Global' as const,
        ops: [
          { type: 'CreateBlock', data: { content: 'Goal 1', semantic_type: 'goal' } },
          { type: 'CreateContextItem', data: { label: 'Context 1' } },
          { type: 'MergeContextItems', data: { from_ids: ['a', 'b'], canonical_id: 'c' } }
        ]
      };

      const summary = summarizeChange(complexChange);

      expect(summary).toBe('manual_edit: 3 ops (CreateBlock, CreateContextItem, MergeContextItems) [Global]');
    });

    it('should handle missing blast radius in summary', () => {
      const change = {
        entry_point: 'onboarding_dump' as const,
        actor_id: 'user-123',
        workspace_id: 'workspace-456',
        ops: [
          { type: 'CreateBlock', data: { content: 'Extracted goal', semantic_type: 'goal' } }
        ]
      };

      const summary = summarizeChange(change);

      expect(summary).toBe('onboarding_dump: 1 ops (CreateBlock) [Unknown]');
    });
  });
});