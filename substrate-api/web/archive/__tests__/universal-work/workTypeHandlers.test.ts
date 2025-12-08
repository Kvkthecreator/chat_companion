/**
 * Work Type Handlers Tests - Canon v2.2
 * 
 * Tests individual work type processing handlers and their Sacred Principles compliance.
 * Validates that each work type (P0-P4, MANUAL_EDIT, etc.) respects canon boundaries.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { UniversalWorkTestCase, TestDataFactory } from './UniversalWorkTestBase';

describe('Work Type Handlers - Canon v2.2', () => {
  let testCase: UniversalWorkTestCase;
  let mockSupabase: any;

  beforeEach(() => {
    testCase = new UniversalWorkTestCase();
    mockSupabase = {
      from: vi.fn().mockReturnThis(),
      select: vi.fn().mockReturnThis(),
      insert: vi.fn().mockReturnThis(),
      update: vi.fn().mockReturnThis(),
      delete: vi.fn().mockReturnThis(),
      in: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      single: vi.fn().mockResolvedValue({ data: { id: 'gen-id' }, error: null }),
      execute: vi.fn()
    };
  });

  describe('P0_CAPTURE Work Type Handler', () => {
    it('should only create raw_dumps and timeline_events', async () => {
      const captureOperations = [
        { type: 'create_raw_dump', data: { content: 'User uploaded file content', source: 'file_upload' } },
        { type: 'create_timeline_event', data: { kind: 'capture', description: 'File uploaded' } }
      ];

      mockSupabase.execute
        .mockResolvedValueOnce({ data: { id: 'dump-123' }, error: null })
        .mockResolvedValueOnce({ data: { id: 'event-456' }, error: null });

      const result = await processP0CaptureWork(mockSupabase, {
        operations: captureOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace'
      });

      expect(result.success).toBe(true);
      expect(result.created_dumps.length).toBe(1);
      expect(result.created_events).toEqual(['event-456']);
      
      // Verify Sacred Principles: P0 never interprets, only captures
      expect(mockSupabase.from).not.toHaveBeenCalledWith('context_blocks');
      expect(mockSupabase.from).not.toHaveBeenCalledWith('context_items');
    });

    it('should reject operations that violate P0 Sacred Principles', async () => {
      const invalidOperations = [
        { type: 'create_block', data: { content: 'This would be interpretation' } },
        { type: 'create_relationship', data: { from: 'A', to: 'B' } }
      ];

      await expect(processP0CaptureWork(mockSupabase, {
        operations: invalidOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace'
      })).rejects.toThrow('P0_CAPTURE can only create raw_dumps and timeline_events');
    });

    it('should preserve provenance chain for captured content', async () => {
      const captureOperations = [
        { 
          type: 'create_raw_dump', 
          data: { 
            content: 'User input via chat', 
            source: 'chat_message',
            trace_id: 'trace-abc123',
            provenance: ['user_input', 'chat_interface']
          } 
        }
      ];

      mockSupabase.execute.mockResolvedValue({ data: { id: 'dump-123' }, error: null });

      await processP0CaptureWork(mockSupabase, {
        operations: captureOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace'
      });

      expect(mockSupabase.insert).toHaveBeenCalledWith(
        expect.objectContaining({
          trace_id: 'trace-abc123',
          provenance: ['user_input', 'chat_interface']
        })
      );
    });
  });

  describe('P1_SUBSTRATE Work Type Handler', () => {
    it('should create and modify substrate elements', async () => {
      const substrateOperations = [
        { type: 'create_block', data: { content: 'Key insight from analysis', semantic_type: 'insight' } },
        { type: 'update_block', data: { id: 'block-456', content: 'Updated insight' } },
        { type: 'create_context_items', data: { items: [{ content: 'Supporting context' }] } }
      ];

      mockSupabase.execute
        .mockResolvedValueOnce({ data: { id: 'block-123' }, error: null })
        .mockResolvedValueOnce({ data: { id: 'block-456' }, error: null })
        .mockResolvedValueOnce({ data: [{ id: 'item-789' }], error: null });

      const result = await processP1SubstrateWork(mockSupabase, {
        operations: substrateOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace'
      });

      expect(result.success).toBe(true);
      expect(result.created_blocks.length).toBe(1);
      expect(result.updated_blocks).toEqual(['block-456']);
      expect(result.created_context_items).toEqual(['item-789']);
    });

    it('should reject operations that violate P1 Sacred Principles', async () => {
      const invalidOperations = [
        { type: 'create_relationship', data: { from: 'block-1', to: 'block-2' } }, // P2 territory
        { type: 'create_reflection', data: { content: 'This is reflection' } }, // P3 territory
        { type: 'create_document', data: { title: 'Document' } } // P4 territory
      ];

      await expect(processP1SubstrateWork(mockSupabase, {
        operations: invalidOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace'
      })).rejects.toThrow('P1_SUBSTRATE can only create/update substrate elements');
    });

    it('should handle block merging operations', async () => {
      const mergeOperations = [
        { 
          type: 'merge_blocks', 
          data: { 
            source_blocks: ['block-1', 'block-2'],
            merged_content: 'Combined insight from multiple sources',
            merge_strategy: 'semantic_union'
          } 
        }
      ];

      mockSupabase.execute.mockResolvedValue({ data: { id: 'merged-block-123' }, error: null });

      const result = await processP1SubstrateWork(mockSupabase, {
        operations: mergeOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace'
      });

      expect(result.merged_blocks).toEqual(['merged-block-123']);
      expect(mockSupabase.update).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'merged'
        })
      );
    });
  });

  describe('P2_GRAPH Work Type Handler', () => {
    it('should create and update relationships only', async () => {
      const graphOperations = [
        { 
          type: 'create_relationship', 
          data: { 
            from_block: 'block-1', 
            to_block: 'block-2', 
            relationship_type: 'supports',
            strength: 0.8 
          } 
        },
        { 
          type: 'update_relationship', 
          data: { 
            id: 'rel-456', 
            strength: 0.9,
            confidence: 0.85
          } 
        }
      ];

      mockSupabase.execute
        .mockResolvedValueOnce({ data: { id: 'rel-123' }, error: null })
        .mockResolvedValueOnce({ data: { id: 'rel-456' }, error: null });

      const result = await processP2GraphWork(mockSupabase, {
        operations: graphOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace'
      });

      expect(result.success).toBe(true);
      expect(result.created_relationships.length).toBe(1);
      expect(result.updated_relationships).toEqual(['rel-456']);
    });

    it('should reject operations that create new substrate', async () => {
      const invalidOperations = [
        { type: 'create_block', data: { content: 'New substrate' } },
        { type: 'create_context_items', data: { items: [] } }
      ];

      await expect(processP2GraphWork(mockSupabase, {
        operations: invalidOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace'
      })).rejects.toThrow('P2_GRAPH can only create/update relationships');
    });

    it('should validate relationship targets exist', async () => {
      const relationshipOperations = [
        { 
          type: 'create_relationship', 
          data: { 
            from_block: 'nonexistent-block', 
            to_block: 'block-2',
            relationship_type: 'contradicts'
          } 
        }
      ];

      mockSupabase.execute.mockResolvedValue({ data: null, error: { message: 'Referenced block does not exist' } });

      await expect(processP2GraphWork(mockSupabase, {
        operations: relationshipOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace'
      })).rejects.toThrow('Referenced block does not exist');
    });
  });

  describe('P3_REFLECTION Work Type Handler', () => {
    it('should create reflections and analysis artifacts', async () => {
      const reflectionOperations = [
        { 
          type: 'create_reflection', 
          data: { 
            content: 'Pattern analysis reveals recurring themes in user feedback',
            reflection_type: 'pattern_analysis',
            source_blocks: ['block-1', 'block-2', 'block-3']
          } 
        }
      ];

      mockSupabase.execute.mockResolvedValue({ data: { id: 'reflection-123' }, error: null });

      const result = await processP3ReflectionWork(mockSupabase, {
        operations: reflectionOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace'
      });

      expect(result.success).toBe(true);
      expect(result.created_reflections.length).toBe(1);
    });

    it('should reject substrate modification operations', async () => {
      const invalidOperations = [
        { type: 'update_block', data: { id: 'block-1', content: 'Modified' } },
        { type: 'create_relationship', data: { from: 'A', to: 'B' } }
      ];

      await expect(processP3ReflectionWork(mockSupabase, {
        operations: invalidOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace'
      })).rejects.toThrow('P3_REFLECTION can only create reflections and analysis');
    });

    it('should support different reflection types', async () => {
      const reflectionTypes = [
        'pattern_analysis',
        'insight_synthesis', 
        'contradiction_detection',
        'knowledge_gap_analysis',
        'temporal_analysis'
      ];

      for (const reflectionType of reflectionTypes) {
        mockSupabase.execute.mockResolvedValue({ data: { id: `ref-${reflectionType}` }, error: null });

        const result = await processP3ReflectionWork(mockSupabase, {
          operations: [{ 
            type: 'create_reflection', 
            data: { 
              content: `${reflectionType} result`,
              reflection_type: reflectionType
            } 
          }],
          basket_id: 'test-basket',
          workspace_id: 'test-workspace'
        });

        expect(result.success).toBe(true);
      }
    });
  });

  describe('P4_COMPOSE Work Type Handler', () => {
    it('should create documents and compositions', async () => {
      const composeOperations = [
        { 
          type: 'create_document', 
          data: { 
            title: 'Project Summary Report',
            content: 'Synthesized insights from project analysis...',
            document_type: 'summary',
            source_blocks: ['block-1', 'block-2'],
            source_reflections: ['reflection-1']
          } 
        }
      ];

      mockSupabase.execute.mockResolvedValue({ data: { id: 'doc-123' }, error: null });

      const result = await processP4ComposeWork(mockSupabase, {
        operations: composeOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace'
      });

      expect(result.success).toBe(true);
      expect(result.created_documents.length).toBe(1);
    });

    it('should reject substrate creation operations', async () => {
      const invalidOperations = [
        { type: 'create_block', data: { content: 'New substrate' } },
        { type: 'create_relationship', data: { from: 'A', to: 'B' } }
      ];

      await expect(processP4ComposeWork(mockSupabase, {
        operations: invalidOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace'
      })).rejects.toThrow('P4_COMPOSE can only create documents and compositions');
    });

    it('should validate source material exists', async () => {
      const composeOperations = [
        { 
          type: 'create_document', 
          data: { 
            title: 'Invalid Document',
            content: 'Document with invalid sources',
            source_blocks: ['nonexistent-block']
          } 
        }
      ];

      mockSupabase.execute.mockResolvedValue({ data: null, error: { message: 'Source blocks not found' } });

      await expect(processP4ComposeWork(mockSupabase, {
        operations: composeOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace'
      })).rejects.toThrow('Source blocks not found');
    });
  });

  describe('MANUAL_EDIT Work Type Handler', () => {
    it('should handle user-initiated substrate modifications', async () => {
      const manualOperations = [
        { type: 'update_block', data: { id: 'block-123', content: 'User edited content' } },
        { type: 'delete_context_items', data: { ids: ['item-456'] } }
      ];

      mockSupabase.execute
        .mockResolvedValueOnce({ data: { id: 'block-123' }, error: null })
        .mockResolvedValueOnce({ data: { affected_rows: 1 }, error: null });

      const result = await processManualEditWork(mockSupabase, {
        operations: manualOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace',
        user_id: 'user-123'
      });

      expect(result.success).toBe(true);
      expect(result.updated_blocks.length).toBe(1);
      expect(result.deleted_context_items).toBe(1);
    });

    it('should record user attribution for manual edits', async () => {
      const manualOperations = [
        { type: 'update_block', data: { id: 'block-123', content: 'Manually updated' } }
      ];

      mockSupabase.execute.mockResolvedValue({ data: { id: 'block-123' }, error: null });

      await processManualEditWork(mockSupabase, {
        operations: manualOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace',
        user_id: 'user-123'
      });

      expect(mockSupabase.update).toHaveBeenCalledWith(
        expect.objectContaining({
          last_modified_by: 'user-123',
          modification_type: 'manual_edit'
        })
      );
    });

    it('should prevent creation of new substrate via manual edit', async () => {
      const invalidOperations = [
        { type: 'create_block', data: { content: 'New block via manual edit' } }
      ];

      await expect(processManualEditWork(mockSupabase, {
        operations: invalidOperations,
        basket_id: 'test-basket',
        workspace_id: 'test-workspace',
        user_id: 'user-123'
      })).rejects.toThrow('MANUAL_EDIT cannot create new substrate');
    });
  });

  describe('Work Type Processing Integration', () => {
    it('should route work to correct handler based on work type', async () => {
      const workTypeTests = [
        { workType: 'P0_CAPTURE', expectedHandler: 'processP0CaptureWork' },
        { workType: 'P1_SUBSTRATE', expectedHandler: 'processP1SubstrateWork' },
        { workType: 'P2_GRAPH', expectedHandler: 'processP2GraphWork' },
        { workType: 'P3_REFLECTION', expectedHandler: 'processP3ReflectionWork' },
        { workType: 'P4_COMPOSE', expectedHandler: 'processP4ComposeWork' },
        { workType: 'MANUAL_EDIT', expectedHandler: 'processManualEditWork' }
      ];

      for (const { workType, expectedHandler } of workTypeTests) {
        const workRequest = testCase.createWorkRequest({ work_type: workType });
        
        const handler = getWorkTypeHandler(workType);
        expect(handler.name).toBe(expectedHandler);
      }
    });

    it('should validate work type against Sacred Principles before processing', async () => {
      const workRequest = testCase.createWorkRequest({
        work_type: 'P0_CAPTURE',
        operations: [
          { type: 'create_block', data: { content: 'Invalid for P0' } } // Should be rejected
        ]
      });

      mockSupabase.execute.mockResolvedValue({ data: null, error: null });

      await expect(
        processWorkByType(mockSupabase, workRequest)
      ).rejects.toThrow('Sacred Principles violation');
    });

    it('should handle unknown work types gracefully', async () => {
      const invalidWorkRequest = testCase.createWorkRequest({
        work_type: 'UNKNOWN_TYPE'
      });

      await expect(
        processWorkByType(mockSupabase, invalidWorkRequest)
      ).rejects.toThrow('Unknown work type: UNKNOWN_TYPE');
    });
  });
});

// Mock handler implementations (simplified for testing)
async function processP0CaptureWork(supabase: any, payload: any): Promise<any> {
  const validOperations = ['create_raw_dump', 'create_timeline_event'];
  
  for (const op of payload.operations) {
    if (!validOperations.includes(op.type)) {
      throw new Error('P0_CAPTURE can only create raw_dumps and timeline_events');
    }
  }

  const results = { success: true, created_dumps: [], created_events: [] };
  
  for (const op of payload.operations) {
    const { data } = await supabase.from(op.type === 'create_raw_dump' ? 'raw_dumps' : 'timeline_events').insert(op.data).select('id').single();
    
    if (op.type === 'create_raw_dump') {
      results.created_dumps.push(data.id);
    } else {
      results.created_events.push(data.id);
    }
  }
  
  return results;
}

async function processP1SubstrateWork(supabase: any, payload: any): Promise<any> {
  const validOperations = ['create_block', 'update_block', 'merge_blocks', 'create_context_items', 'update_context_items'];
  
  for (const op of payload.operations) {
    if (!validOperations.includes(op.type)) {
      throw new Error('P1_SUBSTRATE can only create/update substrate elements');
    }
  }

  const results = { success: true, created_blocks: [], updated_blocks: [], merged_blocks: [], created_context_items: [] };
  
  for (const op of payload.operations) {
    if (op.type === 'create_block') {
      const { data } = await supabase.from('blocks').insert(op.data).select('id').single();
      results.created_blocks.push(data.id);
    } else if (op.type === 'update_block') {
      const { data } = await supabase.from('blocks').update(op.data).eq('id', op.data.id).select('id').single();
      results.updated_blocks.push(data.id);
    } else if (op.type === 'merge_blocks') {
      const { data } = await supabase.from('blocks').insert({ content: op.data.merged_content }).select('id').single();
      results.merged_blocks.push(data.id);
      // Update source blocks to merged status
      await supabase.from('blocks').update({ status: 'merged' }).in('id', op.data.source_blocks);
    } else if (op.type === 'create_context_items') {
      const { data } = await supabase.from('context_items').insert(op.data.items).select('id');
      results.created_context_items.push(data[0].id);
    }
  }
  
  return results;
}

async function processP2GraphWork(supabase: any, payload: any): Promise<any> {
  const validOperations = ['create_relationship', 'update_relationship'];
  
  for (const op of payload.operations) {
    if (!validOperations.includes(op.type)) {
      throw new Error('P2_GRAPH can only create/update relationships');
    }
  }

  const results = { success: true, created_relationships: [], updated_relationships: [] };
  
  for (const op of payload.operations) {
    const table = 'substrate_relationships';
    const { data, error } = await supabase.from(table).insert(op.data).select('id').single();
    
    if (error) throw error;
    
    if (op.type === 'create_relationship') {
      results.created_relationships.push(data.id);
    } else {
      results.updated_relationships.push(data.id);
    }
  }
  
  return results;
}

async function processP3ReflectionWork(supabase: any, payload: any): Promise<any> {
  const validOperations = ['create_reflection', 'update_reflection'];
  
  for (const op of payload.operations) {
    if (!validOperations.includes(op.type)) {
      throw new Error('P3_REFLECTION can only create reflections and analysis');
    }
  }

  const results = { success: true, created_reflections: [] };
  
  for (const op of payload.operations) {
      const { data } = await supabase.from('reflections_artifact').insert(op.data).select('id').single();
    results.created_reflections.push(data.id);
  }
  
  return results;
}

async function processP4ComposeWork(supabase: any, payload: any): Promise<any> {
  const validOperations = ['create_document', 'update_document'];
  
  for (const op of payload.operations) {
    if (!validOperations.includes(op.type)) {
      throw new Error('P4_COMPOSE can only create documents and compositions');
    }
  }

  const results = { success: true, created_documents: [] };
  
  for (const op of payload.operations) {
    const { data, error } = await supabase.from('documents').insert(op.data).select('id').single();
    
    if (error) throw error;
    results.created_documents.push(data.id);
  }
  
  return results;
}

async function processManualEditWork(supabase: any, payload: any): Promise<any> {
  const validOperations = ['update_block', 'delete_block', 'update_context_items', 'delete_context_items'];
  
  for (const op of payload.operations) {
    if (!validOperations.includes(op.type)) {
      throw new Error('MANUAL_EDIT cannot create new substrate');
    }
  }

  const results = { success: true, updated_blocks: [], deleted_context_items: 0 };
  
  for (const op of payload.operations) {
    if (op.type === 'update_block') {
      const { data } = await supabase
        .from('blocks')
        .update({
          ...op.data,
          last_modified_by: payload.user_id,
          modification_type: 'manual_edit'
        })
        .eq('id', op.data.id)
        .select('id')
        .single();
      results.updated_blocks.push(data.id);
    } else if (op.type === 'delete_context_items') {
      const { data } = await supabase.from('context_items').delete().in('id', op.data.ids);
      results.deleted_context_items = data.affected_rows;
    }
  }
  
  return results;
}

function getWorkTypeHandler(workType: string): Function {
  const handlers = {
    'P0_CAPTURE': processP0CaptureWork,
    'P1_SUBSTRATE': processP1SubstrateWork,
    'P2_GRAPH': processP2GraphWork,
    'P3_REFLECTION': processP3ReflectionWork,
    'P4_COMPOSE': processP4ComposeWork,
    'MANUAL_EDIT': processManualEditWork
  };

  return handlers[workType];
}

async function processWorkByType(supabase: any, workRequest: any): Promise<any> {
  // Validate Sacred Principles compliance
  const testCase = new UniversalWorkTestCase();
  testCase.assertSacredPrinciplesCompliance(workRequest.work_type, workRequest.work_payload.operations);

  const handler = getWorkTypeHandler(workRequest.work_type);
  if (!handler) {
    throw new Error(`Unknown work type: ${workRequest.work_type}`);
  }

  return await handler(supabase, workRequest.work_payload);
}
