import { describe, it, expect } from 'vitest';
import {
  SubstrateTypeSchema,
  SubstrateReferenceSchema,
  AttachSubstrateRequestSchema,
  GetDocumentReferencesRequestSchema,
  DocumentCompositionSchema,
  SubstrateSummarySchema,
} from '@/shared/contracts/substrate_references';

describe('Substrate Reference Contracts', () => {
  describe('SubstrateTypeSchema', () => {
    it('validates all canonical substrate types', () => {
      // Reflections are artifacts, not substrates
      const validTypes = ['block', 'dump', 'context_item', 'timeline_event'];
      
      validTypes.forEach(type => {
        const result = SubstrateTypeSchema.safeParse(type);
        expect(result.success).toBe(true);
      });
    });

    it('rejects invalid substrate types', () => {
      const invalidTypes = ['document', 'user', 'workspace', '', null, undefined];
      
      invalidTypes.forEach(type => {
        const result = SubstrateTypeSchema.safeParse(type);
        expect(result.success).toBe(false);
      });
    });
  });

  describe('SubstrateReferenceSchema', () => {
    const validReference = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      document_id: '123e4567-e89b-12d3-a456-426614174001',
      substrate_type: 'block',
      substrate_id: '123e4567-e89b-12d3-a456-426614174002',
      role: 'primary',
      weight: 0.8,
      snippets: ['test snippet'],
      metadata: { source: 'manual' },
      created_at: '2025-01-01T10:00:00Z',
      created_by: '123e4567-e89b-12d3-a456-426614174003',
    };

    it('validates complete substrate reference', () => {
      const result = SubstrateReferenceSchema.safeParse(validReference);
      expect(result.success).toBe(true);
      
      if (result.success) {
        expect(result.data.substrate_type).toBe('block');
        expect(result.data.weight).toBe(0.8);
        expect(result.data.snippets).toEqual(['test snippet']);
      }
    });

    it('validates minimal substrate reference', () => {
      const minimal = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        document_id: '123e4567-e89b-12d3-a456-426614174001',
        substrate_type: 'dump',
        substrate_id: '123e4567-e89b-12d3-a456-426614174002',
        created_at: '2025-01-01T10:00:00Z',
      };

      const result = SubstrateReferenceSchema.safeParse(minimal);
      expect(result.success).toBe(true);
      
      if (result.success) {
        expect(result.data.snippets).toEqual([]); // default value
        expect(result.data.metadata).toEqual({}); // default value
      }
    });

    it('enforces UUID format for IDs', () => {
      const invalidId = { ...validReference, id: 'not-a-uuid' };
      const result = SubstrateReferenceSchema.safeParse(invalidId);
      expect(result.success).toBe(false);
    });

    it('enforces weight constraints', () => {
      const invalidWeights = [-0.1, 1.1, 2.0];
      
      invalidWeights.forEach(weight => {
        const invalid = { ...validReference, weight };
        const result = SubstrateReferenceSchema.safeParse(invalid);
        expect(result.success).toBe(false);
      });
    });

    it('accepts valid weight values', () => {
      const validWeights = [0.0, 0.5, 1.0];
      
      validWeights.forEach(weight => {
        const valid = { ...validReference, weight };
        const result = SubstrateReferenceSchema.safeParse(valid);
        expect(result.success).toBe(true);
      });
    });
  });

  describe('AttachSubstrateRequestSchema', () => {
    const validRequest = {
      substrate_type: 'context_item',
      substrate_id: '123e4567-e89b-12d3-a456-426614174000',
      role: 'supporting',
      weight: 0.6,
      snippets: ['relevant text'],
      metadata: { importance: 'high' },
    };

    it('validates complete attachment request', () => {
      const result = AttachSubstrateRequestSchema.safeParse(validRequest);
      expect(result.success).toBe(true);
    });

    it('validates minimal attachment request', () => {
      const minimal = {
        substrate_type: 'dump',
        substrate_id: '123e4567-e89b-12d3-a456-426614174000',
      };

      const result = AttachSubstrateRequestSchema.safeParse(minimal);
      expect(result.success).toBe(true);
    });

    it('requires substrate_type and substrate_id', () => {
      const incomplete = { substrate_type: 'block' }; // missing substrate_id
      const result = AttachSubstrateRequestSchema.safeParse(incomplete);
      expect(result.success).toBe(false);
    });
  });

  describe('GetDocumentReferencesRequestSchema', () => {
    it('validates query with all filters', () => {
      const query = {
        substrate_types: ['block', 'dump'],
        role: 'primary',
        limit: 50,
        cursor: '2025-01-01T10:00:00Z',
      };

      const result = GetDocumentReferencesRequestSchema.safeParse(query);
      expect(result.success).toBe(true);
    });

    it('applies default limit', () => {
      const query = {};
      const result = GetDocumentReferencesRequestSchema.safeParse(query);
      
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.limit).toBe(100);
      }
    });

    it('validates substrate type filters', () => {
      const validQuery = { substrate_types: ['block', 'timeline_event'] };
      const result = GetDocumentReferencesRequestSchema.safeParse(validQuery);
      expect(result.success).toBe(true);

      const invalidQuery = { substrate_types: ['invalid_type'] };
      const result2 = GetDocumentReferencesRequestSchema.safeParse(invalidQuery);
      expect(result2.success).toBe(false);
    });
  });

  describe('SubstrateSummarySchema', () => {
    it('validates block substrate summary', () => {
      const blockSummary = {
        substrate_type: 'block',
        substrate_id: '123e4567-e89b-12d3-a456-426614174000',
        title: 'Test Block',
        preview: 'This is a test block',
        created_at: '2025-01-01T10:00:00Z',
        state: 'active',
        version: 1,
      };

      const result = SubstrateSummarySchema.safeParse(blockSummary);
      expect(result.success).toBe(true);
    });

    it('validates dump substrate summary', () => {
      const dumpSummary = {
        substrate_type: 'dump',
        substrate_id: '123e4567-e89b-12d3-a456-426614174000',
        title: null,
        preview: 'Raw dump content',
        created_at: '2025-01-01T10:00:00Z',
        char_count: 1500,
        source_type: 'clipboard',
      };

      const result = SubstrateSummarySchema.safeParse(dumpSummary);
      expect(result.success).toBe(true);
    });

    it('validates timeline event substrate summary', () => {
      const eventSummary = {
        substrate_type: 'timeline_event',
        substrate_id: '123e4567-e89b-12d3-a456-426614174000',
        title: null,
        preview: 'document.created',
        created_at: '2025-01-01T10:00:00Z',
        event_kind: 'document.created',
        actor_id: '123e4567-e89b-12d3-a456-426614174001',
      };

      const result = SubstrateSummarySchema.safeParse(eventSummary);
      expect(result.success).toBe(true);
    });

    it('allows null title for substrate types without titles', () => {
      const summaryWithNullTitle = {
        substrate_type: 'dump',
        substrate_id: '123e4567-e89b-12d3-a456-426614174000',
        title: null,
        preview: 'Raw dump preview',
        created_at: '2025-01-01T10:00:00Z',
      };

      const result = SubstrateSummarySchema.safeParse(summaryWithNullTitle);
      expect(result.success).toBe(true);
    });
  });

  describe('DocumentCompositionSchema', () => {
    const validComposition = {
      document: {
        id: '123e4567-e89b-12d3-a456-426614174000',
        basket_id: '123e4567-e89b-12d3-a456-426614174001',
        title: 'Test Document',
        created_at: '2025-01-01T10:00:00Z',
        updated_at: '2025-01-01T11:00:00Z',
        metadata: { type: 'test' },
      },
      references: [
        {
          reference: {
            id: '123e4567-e89b-12d3-a456-426614174002',
            document_id: '123e4567-e89b-12d3-a456-426614174000',
            substrate_type: 'block',
            substrate_id: '123e4567-e89b-12d3-a456-426614174003',
            created_at: '2025-01-01T10:30:00Z',
          },
          substrate: {
            substrate_type: 'block',
            substrate_id: '123e4567-e89b-12d3-a456-426614174003',
            title: 'Test Block',
            preview: 'Block content',
            created_at: '2025-01-01T10:00:00Z',
          },
        },
      ],
      composition_stats: {
        blocks_count: 1,
        dumps_count: 0,
        context_items_count: 0,
        reflections_count: 0,
        timeline_events_count: 0,
        total_references: 1,
      },
    };

    it('validates complete document composition', () => {
      const result = DocumentCompositionSchema.safeParse(validComposition);
      expect(result.success).toBe(true);
    });

    it('validates composition stats consistency', () => {
      const result = DocumentCompositionSchema.safeParse(validComposition);
      
      if (result.success) {
        const stats = result.data.composition_stats;
        expect(stats.total_references).toBe(
          stats.blocks_count + 
          stats.dumps_count + 
          stats.context_items_count + 
          stats.reflections_count + 
          stats.timeline_events_count
        );
      }
    });

    it('validates empty composition', () => {
      const emptyComposition = {
        ...validComposition,
        references: [],
        composition_stats: {
          blocks_count: 0,
          dumps_count: 0,
          context_items_count: 0,
          reflections_count: 0,
          timeline_events_count: 0,
          total_references: 0,
        },
      };

      const result = DocumentCompositionSchema.safeParse(emptyComposition);
      expect(result.success).toBe(true);
    });
  });

  describe('Substrate Canon Compliance', () => {
    it('ensures all substrate types are treated as peers', () => {
      const substrateTypes = SubstrateTypeSchema.options;
      
      // All substrate types should have equal status in the enum
      expect(substrateTypes).toContain('block');
      expect(substrateTypes).toContain('dump');
      expect(substrateTypes).toContain('context_item');
      expect(substrateTypes).toContain('timeline_event');
      
      // No type should have special precedence
      expect(substrateTypes.length).toBe(4);
    });

    it('validates substrate reference uniformity', () => {
      const substrateTypes = ['block', 'dump', 'context_item', 'timeline_event'];
      
      substrateTypes.forEach(type => {
        const reference = {
          id: '123e4567-e89b-12d3-a456-426614174000',
          document_id: '123e4567-e89b-12d3-a456-426614174001',
          substrate_type: type,
          substrate_id: '123e4567-e89b-12d3-a456-426614174002',
          created_at: '2025-01-01T10:00:00Z',
        };

        const result = SubstrateReferenceSchema.safeParse(reference);
        expect(result.success).toBe(true);
      });
    });

    it('supports generic attachment for all substrate types', () => {
      const substrateTypes = ['block', 'dump', 'context_item', 'timeline_event'];
      
      substrateTypes.forEach(type => {
        const attachRequest = {
          substrate_type: type,
          substrate_id: '123e4567-e89b-12d3-a456-426614174000',
          role: 'test',
        };

        const result = AttachSubstrateRequestSchema.safeParse(attachRequest);
        expect(result.success).toBe(true);
      });
    });
  });
});
