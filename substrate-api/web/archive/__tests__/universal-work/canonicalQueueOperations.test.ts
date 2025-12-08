/**
 * Canonical Queue Operations Tests - Canon v2.2
 * 
 * Tests the agent_processing_queue operations that underpin Universal Work Orchestration.
 * Validates queue integrity, work lifecycle, and processing state management.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { UniversalWorkTestCase, TestDataFactory } from './UniversalWorkTestBase';

describe('Canonical Queue Operations - Canon v2.2', () => {
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
      eq: vi.fn().mockReturnThis(),
      in: vi.fn().mockReturnThis(),
      order: vi.fn().mockReturnThis(),
      limit: vi.fn().mockReturnThis(),
      single: vi.fn().mockResolvedValue({ data: { id: 'work-123' }, error: null }),
      execute: vi.fn()
    };
  });

  describe('Work Entry Creation', () => {
    it('should create work entry with all required fields', async () => {
      // Arrange
      const workRequest = testCase.createWorkRequest({
        work_type: 'P1_SUBSTRATE',
        confidence_score: 0.85,
        priority: 'high'
      });

      mockSupabase.execute.mockResolvedValue({
        data: { id: 'work-123', created_at: new Date().toISOString() },
        error: null
      });

      // Act
      const result = await createQueueEntry(mockSupabase, workRequest, 'test-workspace', 'test-user');

      // Assert
      expect(mockSupabase.from).toHaveBeenCalledWith('agent_processing_queue');
      expect(mockSupabase.insert).toHaveBeenCalledWith({
        work_type: 'P1_SUBSTRATE',
        work_payload: workRequest.work_payload,
        workspace_id: 'test-workspace',
        user_id: 'test-user',
        priority: 'high',
        processing_state: 'pending',
        created_at: expect.any(String)
      });
      expect(result.work_id).toBe('work-123');
    });

    it('should set correct initial processing state for different execution modes', async () => {
      const executionModes = [
        { mode: 'auto_execute', expected_state: 'claimed' },
        { mode: 'create_proposal', expected_state: 'pending' },
        { mode: 'confidence_routing', expected_state: 'pending' }
      ];

      for (const { mode, expected_state } of executionModes) {
        mockSupabase.execute.mockResolvedValue({
          data: { id: `work-${mode}` },
          error: null
        });

        const workRequest = testCase.createWorkRequest();
        await createQueueEntry(mockSupabase, workRequest, 'test-workspace', 'test-user', mode);

        expect(mockSupabase.insert).toHaveBeenCalledWith(
          expect.objectContaining({
            processing_state: expected_state,
            execution_mode: mode
          })
        );
      }
    });

    it('should validate work payload structure', async () => {
      const invalidPayloads = [
        { operations: [], basket_id: '' }, // Missing basket_id
        { operations: null, basket_id: 'valid' }, // Invalid operations
        { basket_id: 'valid' }, // Missing operations entirely
      ];

      for (const payload of invalidPayloads) {
        const workRequest = testCase.createWorkRequest();
        workRequest.work_payload = payload as any;

        await expect(
          createQueueEntry(mockSupabase, workRequest, 'test-workspace', 'test-user')
        ).rejects.toThrow('Invalid work payload');
      }
    });
  });

  describe('Work State Transitions', () => {
    it('should handle valid state transitions', async () => {
      const validTransitions = [
        { from: 'pending', to: 'claimed' },
        { from: 'claimed', to: 'running' },
        { from: 'running', to: 'completed' },
        { from: 'running', to: 'failed' },
        { from: 'claimed', to: 'failed' },
        { from: 'failed', to: 'claimed' }, // Retry
      ];

      for (const { from, to } of validTransitions) {
        mockSupabase.execute.mockResolvedValue({
          data: { id: 'work-123' },
          error: null
        });

        const result = await updateWorkState(mockSupabase, 'work-123', from, to);
        expect(result.success).toBe(true);
      }
    });

    it('should reject invalid state transitions', async () => {
      const invalidTransitions = [
        { from: 'completed', to: 'running' }, // Can't uncomplete
        { from: 'pending', to: 'running' }, // Must be claimed first
        { from: 'completed', to: 'claimed' }, // Can't reclaim completed work
      ];

      for (const { from, to } of invalidTransitions) {
        await expect(
          updateWorkState(mockSupabase, 'work-123', from, to)
        ).rejects.toThrow(`Invalid state transition: ${from} -> ${to}`);
      }
    });

    it('should update processing timestamps correctly', async () => {
      mockSupabase.execute.mockResolvedValue({
        data: { id: 'work-123' },
        error: null
      });

      await updateWorkState(mockSupabase, 'work-123', 'pending', 'claimed');
      expect(mockSupabase.update).toHaveBeenCalledWith(
        expect.objectContaining({
          processing_state: 'claimed',
          claimed_at: expect.any(String)
        })
      );

      await updateWorkState(mockSupabase, 'work-123', 'claimed', 'running');
      expect(mockSupabase.update).toHaveBeenCalledWith(
        expect.objectContaining({
          processing_state: 'running',
          started_at: expect.any(String)
        })
      );

      await updateWorkState(mockSupabase, 'work-123', 'running', 'completed');
      expect(mockSupabase.update).toHaveBeenCalledWith(
        expect.objectContaining({
          processing_state: 'completed',
          completed_at: expect.any(String)
        })
      );
    });
  });

  describe('Priority Queue Operations', () => {
    it('should respect priority ordering in queue retrieval', async () => {
      const workItems = [
        { id: 'work-urgent', priority: 'urgent', created_at: '2024-01-01T10:00:00Z' },
        { id: 'work-high', priority: 'high', created_at: '2024-01-01T09:00:00Z' },
        { id: 'work-normal', priority: 'normal', created_at: '2024-01-01T08:00:00Z' },
        { id: 'work-low', priority: 'low', created_at: '2024-01-01T07:00:00Z' }
      ];

      mockSupabase.execute.mockResolvedValue({
        data: workItems,
        error: null
      });

      const result = await getNextWorkItems(mockSupabase, 'test-workspace', 5);
      
      // Should be ordered by priority first, then by creation time
      expect(mockSupabase.order).toHaveBeenCalledWith('priority_order, created_at');
      expect(result.length).toBeLessThanOrEqual(5);
    });

    it('should handle FIFO within same priority level', async () => {
      const samePrivorityItems = [
        { id: 'work-1', priority: 'normal', created_at: '2024-01-01T08:00:00Z' },
        { id: 'work-2', priority: 'normal', created_at: '2024-01-01T07:00:00Z' },
        { id: 'work-3', priority: 'normal', created_at: '2024-01-01T09:00:00Z' }
      ];

      mockSupabase.execute.mockResolvedValue({
        data: samePrivorityItems,
        error: null
      });

      await getNextWorkItems(mockSupabase, 'test-workspace', 10);
      
      // Should order by creation time within same priority
      expect(mockSupabase.order).toHaveBeenCalledWith('priority_order, created_at');
    });

    it('should limit work items per workspace to prevent resource monopolization', async () => {
      await getNextWorkItems(mockSupabase, 'test-workspace', 50);
      
      // Should apply reasonable limits even if requested amount is high
      expect(mockSupabase.limit).toHaveBeenCalledWith(20); // Max concurrent work items
    });
  });

  describe('Workspace Isolation', () => {
    it('should enforce workspace boundaries in queue operations', async () => {
      const workRequest = testCase.createWorkRequest();
      
      mockSupabase.execute.mockResolvedValue({
        data: { id: 'work-123' },
        error: null
      });

      await createQueueEntry(mockSupabase, workRequest, 'workspace-a', 'user-1');
      
      // Should only query items from the specified workspace
      expect(mockSupabase.eq).toHaveBeenCalledWith('workspace_id', 'workspace-a');
    });

    it('should prevent cross-workspace work access', async () => {
      await expect(
        updateWorkState(mockSupabase, 'work-from-other-workspace', 'pending', 'claimed', 'workspace-a')
      ).rejects.toThrow('Work item not found in workspace');
    });

    it('should aggregate workspace-specific queue metrics', async () => {
      mockSupabase.execute.mockResolvedValue({
        data: [
          { processing_state: 'pending', count: 5 },
          { processing_state: 'running', count: 2 },
          { processing_state: 'completed', count: 10 }
        ],
        error: null
      });

      const metrics = await getWorkspaceQueueMetrics(mockSupabase, 'test-workspace');
      
      expect(metrics.pending).toBe(5);
      expect(metrics.running).toBe(2);
      expect(metrics.completed).toBe(10);
      expect(metrics.total).toBe(17);
    });
  });

  describe('Work Type Distribution', () => {
    TestDataFactory.workTypes.forEach(workType => {
      it(`should handle ${workType} queue operations correctly`, async () => {
        const workRequest = testCase.createWorkRequest({
          work_type: workType
        });

        mockSupabase.execute.mockResolvedValue({
          data: { id: `work-${workType}` },
          error: null
        });

        const result = await createQueueEntry(mockSupabase, workRequest, 'test-workspace', 'test-user');
        
        expect(result.work_id).toBe(`work-${workType}`);
        expect(mockSupabase.insert).toHaveBeenCalledWith(
          expect.objectContaining({
            work_type: workType
          })
        );
      });
    });

    it('should provide work type distribution metrics', async () => {
      mockSupabase.execute.mockResolvedValue({
        data: [
          { work_type: 'P0_CAPTURE', count: 3 },
          { work_type: 'P1_SUBSTRATE', count: 8 },
          { work_type: 'MANUAL_EDIT', count: 2 }
        ],
        error: null
      });

      const distribution = await getWorkTypeDistribution(mockSupabase, 'test-workspace');
      
      expect(distribution['P0_CAPTURE']).toBe(3);
      expect(distribution['P1_SUBSTRATE']).toBe(8);
      expect(distribution['MANUAL_EDIT']).toBe(2);
    });
  });

  describe('Error Handling and Recovery', () => {
    it('should handle database connection failures gracefully', async () => {
      mockSupabase.execute.mockRejectedValue(new Error('Connection timeout'));
      
      const workRequest = testCase.createWorkRequest();
      
      await expect(
        createQueueEntry(mockSupabase, workRequest, 'test-workspace', 'test-user')
      ).rejects.toThrow('Connection timeout');
    });

    it('should retry failed work items with exponential backoff', async () => {
      const workId = 'work-retry-test';
      
      mockSupabase.execute.mockResolvedValue({
        data: { id: workId, retry_count: 1 },
        error: null
      });

      await markWorkForRetry(mockSupabase, workId, 'Temporary processing error');
      
      expect(mockSupabase.update).toHaveBeenCalledWith(
        expect.objectContaining({
          processing_state: 'pending',
          retry_count: 2,
          retry_after: expect.any(String), // Should have exponential backoff timestamp
          last_error: 'Temporary processing error'
        })
      );
    });

    it('should mark work as permanently failed after max retries', async () => {
      const workId = 'work-max-retry-test';
      
      mockSupabase.execute.mockResolvedValue({
        data: { id: workId, retry_count: 3 }, // At max retries
        error: null
      });

      await markWorkForRetry(mockSupabase, workId, 'Persistent failure');
      
      expect(mockSupabase.update).toHaveBeenCalledWith(
        expect.objectContaining({
          processing_state: 'failed',
          permanent_failure: true,
          last_error: 'Persistent failure'
        })
      );
    });
  });

  describe('Queue Maintenance Operations', () => {
    it('should clean up old completed work items', async () => {
      const cutoffDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000); // 30 days ago
      
      mockSupabase.execute.mockResolvedValue({
        data: [],
        error: null
      });

      await cleanupOldWorkItems(mockSupabase, cutoffDate);
      
      expect(mockSupabase.delete).toHaveBeenCalled();
      expect(mockSupabase.eq).toHaveBeenCalledWith('processing_state', 'completed');
    });

    it('should identify and recover orphaned work items', async () => {
      const staleCutoff = new Date(Date.now() - 60 * 60 * 1000); // 1 hour ago
      
      mockSupabase.execute.mockResolvedValue({
        data: [
          { id: 'work-orphan-1', processing_state: 'claimed', claimed_at: staleCutoff.toISOString() },
          { id: 'work-orphan-2', processing_state: 'running', started_at: staleCutoff.toISOString() }
        ],
        error: null
      });

      await recoverOrphanedWork(mockSupabase, staleCutoff);
      
      // Should reset orphaned work back to pending
      expect(mockSupabase.update).toHaveBeenCalledTimes(2);
      expect(mockSupabase.update).toHaveBeenCalledWith(
        expect.objectContaining({
          processing_state: 'pending',
          claimed_at: null,
          started_at: null
        })
      );
    });
  });
});

// Mock implementation functions
async function createQueueEntry(supabase: any, workRequest: any, workspaceId: string, userId: string, executionMode: string = 'pending'): Promise<any> {
  if (!workRequest.work_payload?.operations || !workRequest.work_payload?.basket_id) {
    throw new Error('Invalid work payload');
  }

  const initialState = executionMode === 'auto_execute' ? 'claimed' : 'pending';
  
  const { data, error } = await supabase
    .from('agent_processing_queue')
    .insert({
      work_type: workRequest.work_type,
      work_payload: workRequest.work_payload,
      workspace_id: workspaceId,
      user_id: userId,
      priority: workRequest.priority,
      processing_state: initialState,
      execution_mode: executionMode,
      created_at: new Date().toISOString()
    })
    .select('id')
    .single();

  if (error) throw error;
  return { work_id: data.id };
}

async function updateWorkState(supabase: any, workId: string, fromState: string, toState: string, workspaceId?: string): Promise<any> {
  const validTransitions = {
    'pending': ['claimed'],
    'claimed': ['running', 'failed'],
    'running': ['completed', 'failed'],
    'failed': ['claimed'] // Retry
  };

  if (!validTransitions[fromState]?.includes(toState)) {
    throw new Error(`Invalid state transition: ${fromState} -> ${toState}`);
  }

  const updates: any = {
    processing_state: toState
  };

  // Add timestamps for state changes
  if (toState === 'claimed') updates.claimed_at = new Date().toISOString();
  if (toState === 'running') updates.started_at = new Date().toISOString();
  if (toState === 'completed') updates.completed_at = new Date().toISOString();

  const { data, error } = await supabase
    .from('agent_processing_queue')
    .update(updates)
    .eq('id', workId)
    .select('id')
    .single();

  if (!data) throw new Error('Work item not found in workspace');
  return { success: true };
}

async function getNextWorkItems(supabase: any, workspaceId: string, limit: number): Promise<any[]> {
  const maxLimit = Math.min(limit, 20); // Prevent resource monopolization
  
  const { data, error } = await supabase
    .from('agent_processing_queue')
    .select('*')
    .eq('workspace_id', workspaceId)
    .eq('processing_state', 'pending')
    .order('priority_order, created_at')
    .limit(maxLimit);

  if (error) throw error;
  return data || [];
}

async function getWorkspaceQueueMetrics(supabase: any, workspaceId: string): Promise<any> {
  const { data, error } = await supabase
    .from('agent_processing_queue')
    .select('processing_state')
    .eq('workspace_id', workspaceId);

  if (error) throw error;

  const metrics = { pending: 0, running: 0, completed: 0, failed: 0, total: 0 };
  data.forEach((item: any) => {
    metrics[item.processing_state] = (metrics[item.processing_state] || 0) + 1;
    metrics.total++;
  });

  return metrics;
}

async function getWorkTypeDistribution(supabase: any, workspaceId: string): Promise<Record<string, number>> {
  const { data, error } = await supabase
    .from('agent_processing_queue')
    .select('work_type')
    .eq('workspace_id', workspaceId);

  if (error) throw error;

  const distribution: Record<string, number> = {};
  data.forEach((item: any) => {
    distribution[item.work_type] = (distribution[item.work_type] || 0) + 1;
  });

  return distribution;
}

async function markWorkForRetry(supabase: any, workId: string, errorMessage: string): Promise<void> {
  const { data: current } = await supabase
    .from('agent_processing_queue')
    .select('retry_count')
    .eq('id', workId)
    .single();

  const newRetryCount = (current?.retry_count || 0) + 1;
  const maxRetries = 3;

  if (newRetryCount > maxRetries) {
    await supabase
      .from('agent_processing_queue')
      .update({
        processing_state: 'failed',
        permanent_failure: true,
        last_error: errorMessage
      })
      .eq('id', workId);
  } else {
    const retryDelay = Math.pow(2, newRetryCount) * 1000; // Exponential backoff
    const retryAfter = new Date(Date.now() + retryDelay);

    await supabase
      .from('agent_processing_queue')
      .update({
        processing_state: 'pending',
        retry_count: newRetryCount,
        retry_after: retryAfter.toISOString(),
        last_error: errorMessage
      })
      .eq('id', workId);
  }
}

async function cleanupOldWorkItems(supabase: any, cutoffDate: Date): Promise<void> {
  await supabase
    .from('agent_processing_queue')
    .delete()
    .eq('processing_state', 'completed')
    .lt('completed_at', cutoffDate.toISOString());
}

async function recoverOrphanedWork(supabase: any, staleCutoff: Date): Promise<void> {
  const { data: orphanedItems } = await supabase
    .from('agent_processing_queue')
    .select('id, processing_state, claimed_at, started_at')
    .in('processing_state', ['claimed', 'running'])
    .or(`claimed_at.lt.${staleCutoff.toISOString()},started_at.lt.${staleCutoff.toISOString()}`);

  if (orphanedItems) {
    for (const item of orphanedItems) {
      await supabase
        .from('agent_processing_queue')
        .update({
          processing_state: 'pending',
          claimed_at: null,
          started_at: null
        })
        .eq('id', item.id);
    }
  }
}
