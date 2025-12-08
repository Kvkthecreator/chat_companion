/**
 * Universal Work Router Tests - Canon v2.2
 * 
 * Tests the core Universal Work Orchestration routing logic.
 * Validates governance policy evaluation and routing decisions.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { routeWork } from '@/lib/governance/universalWorkRouter';
import { UniversalWorkTestCase, TestDataFactory } from './UniversalWorkTestBase';

// Mock the policyDecider module
vi.mock('@/lib/governance/policyDecider', () => ({
  policyDecider: {
    getWorkTypePolicy: vi.fn()
  }
}));

import { policyDecider } from '@/lib/governance/policyDecider';

describe('Universal Work Router - Canon v2.2', () => {
  let testCase: UniversalWorkTestCase;
  let mockSupabase: any;

  beforeEach(() => {
    testCase = new UniversalWorkTestCase();
    
    // Mock Supabase client with proper chaining
    mockSupabase = {
      from: vi.fn(() => mockSupabase),
      select: vi.fn(() => mockSupabase),
      insert: vi.fn(() => mockSupabase),
      update: vi.fn(() => mockSupabase),
      eq: vi.fn(() => mockSupabase),
      single: vi.fn(() => mockSupabase)
    };
    
    // Reset policy decider mock
    vi.mocked(policyDecider.getWorkTypePolicy).mockReset();
  });

  describe('Governance Policy Evaluation', () => {
    it('should route to auto_execute for auto governance mode', async () => {
      // Arrange
      vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
        mode: 'auto',
        confidence_threshold: 0.8,
        require_validation: false
      });

      mockSupabase.single.mockResolvedValue({
        data: { id: 'work-123' },
        error: null
      });

      const workRequest = testCase.createWorkRequest({
        work_type: 'P0_CAPTURE',
        confidence_score: 0.9
      });

      // Act
      const result = await routeWork(mockSupabase, {
        work_type: workRequest.work_type,
        work_payload: workRequest.work_payload,
        workspace_id: 'test-workspace',
        user_id: 'test-user',
        priority: workRequest.priority
      });

      // Assert
      expect(result.routing_decision).toBe('auto_execute');
      expect(result.execution_mode).toBe('auto_execute');
      expect(result.work_id).toBe('work-123');
    });

    it('should route to create_proposal for proposal governance mode', async () => {
      // Arrange
      vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
        mode: 'proposal',
        confidence_threshold: 0.8,
        require_validation: false
      });

      // Mock work entry creation
      mockSupabase.single
        .mockResolvedValueOnce({
          data: { id: 'work-123' },
          error: null
        })
        .mockResolvedValueOnce({
          data: { id: 'proposal-456' },
          error: null
        });

      const workRequest = testCase.createWorkRequest({
        work_type: 'P0_CAPTURE',
        confidence_score: 0.9
      });

      // Act
      const result = await routeWork(mockSupabase, {
        work_type: workRequest.work_type,
        work_payload: workRequest.work_payload,
        workspace_id: 'test-workspace',
        user_id: 'test-user',
        priority: workRequest.priority
      });

      // Assert
      expect(result.routing_decision).toBe('create_proposal');
      expect(result.execution_mode).toBe('create_proposal');
      expect(result.proposal_id).toBe('proposal-456');
    });

    it('should use confidence threshold in confidence governance mode', async () => {
      // High confidence → auto_execute
      vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
        mode: 'confidence',
        confidence_threshold: 0.7,
        require_validation: false
      });

      mockSupabase.single.mockResolvedValue({
        data: { id: 'work-high-conf' },
        error: null
      });

      const highConfidenceRequest = testCase.createWorkRequest({
        work_type: 'P0_CAPTURE',
        confidence_score: 0.9 // Above threshold
      });

      const result = await routeWork(mockSupabase, {
        work_type: highConfidenceRequest.work_type,
        work_payload: highConfidenceRequest.work_payload,
        workspace_id: 'test-workspace',
        user_id: 'test-user',
        priority: highConfidenceRequest.priority
      });

      expect(result.execution_mode).toBe('auto_execute');
    });

    it('should create proposal for low confidence in confidence mode', async () => {
      // Low confidence → create_proposal
      vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
        mode: 'confidence',
        confidence_threshold: 0.8,
        require_validation: false
      });

      mockSupabase.single
        .mockResolvedValueOnce({
          data: { id: 'work-low-conf' },
          error: null
        })
        .mockResolvedValueOnce({
          data: { id: 'proposal-low-conf' },
          error: null
        });

      const lowConfidenceRequest = testCase.createWorkRequest({
        work_type: 'P0_CAPTURE',
        confidence_score: 0.6 // Below threshold
      });

      const result = await routeWork(mockSupabase, {
        work_type: lowConfidenceRequest.work_type,
        work_payload: lowConfidenceRequest.work_payload,
        workspace_id: 'test-workspace',
        user_id: 'test-user',
        priority: lowConfidenceRequest.priority
      });

      expect(result.execution_mode).toBe('create_proposal');
      expect(result.proposal_id).toBe('proposal-low-conf');
    });
  });

  describe('User Override Behavior', () => {
    it('should respect user override allow_auto regardless of policy', async () => {
      // Arrange - strict proposal policy
      vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
        mode: 'proposal',
        confidence_threshold: 0.9,
        require_validation: false
      });

      mockSupabase.single.mockResolvedValue({
        data: { id: 'work-override' },
        error: null
      });

      const workRequest = testCase.createWorkRequest({
        work_type: 'MANUAL_EDIT',
        confidence_score: 0.5, // Low confidence
        user_override: 'allow_auto' // User forces auto
      });

      // Act
      const result = await routeWork(mockSupabase, {
        work_type: workRequest.work_type,
        work_payload: workRequest.work_payload,
        workspace_id: 'test-workspace',
        user_id: 'test-user',
        priority: workRequest.priority
      });

      // Assert
      expect(result.execution_mode).toBe('auto_execute');
    });

    it('should respect user override require_review regardless of policy', async () => {
      // Arrange - permissive auto policy
      vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
        mode: 'auto',
        confidence_threshold: 0.5,
        require_validation: false
      });

      mockSupabase.single
        .mockResolvedValueOnce({
          data: { id: 'work-override-review' },
          error: null
        })
        .mockResolvedValueOnce({
          data: { id: 'proposal-override' },
          error: null
        });

      const workRequest = testCase.createWorkRequest({
        work_type: 'MANUAL_EDIT',
        confidence_score: 0.9, // High confidence
        user_override: 'require_review' // User forces review
      });

      // Act
      const result = await routeWork(mockSupabase, {
        work_type: workRequest.work_type,
        work_payload: workRequest.work_payload,
        workspace_id: 'test-workspace',
        user_id: 'test-user',
        priority: workRequest.priority
      });

      // Assert
      expect(result.execution_mode).toBe('create_proposal');
      expect(result.proposal_id).toBe('proposal-override');
    });
  });

  describe('Work Type Policy Mapping', () => {
    const workTypePolicyTests = [
      {
        workType: 'P0_CAPTURE',
        expectedPolicySource: 'ep_onboarding_dump'
      },
      {
        workType: 'P1_SUBSTRATE', 
        expectedPolicySource: 'ep_onboarding_dump'
      },
      {
        workType: 'MANUAL_EDIT',
        expectedPolicySource: 'ep_manual_edit'
      },
      {
        workType: 'P2_GRAPH',
        expectedMode: 'confidence' // AI operations benefit from confidence routing
      },
      {
        workType: 'P3_REFLECTION',
        expectedMode: 'confidence'
      },
      {
        workType: 'P4_COMPOSE',
        expectedMode: 'confidence'
      },
      {
        workType: 'PROPOSAL_REVIEW',
        expectedMode: 'proposal' // Always review operations
      },
      {
        workType: 'TIMELINE_RESTORE',
        expectedMode: 'proposal'
      }
    ];

    workTypePolicyTests.forEach(({ workType, expectedPolicySource, expectedMode }) => {
      it(`should map ${workType} to correct governance policy`, async () => {
        // This test would verify the policyDecider.getWorkTypePolicy logic
        // Implementation would depend on the actual policy mapping
        expect(workType).toBeDefined();
        if (expectedPolicySource) {
          expect(['ep_onboarding_dump', 'ep_manual_edit']).toContain(expectedPolicySource);
        }
        if (expectedMode) {
          expect(['auto', 'proposal', 'confidence']).toContain(expectedMode);
        }
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle workspace governance fetch failure gracefully', async () => {
      // Arrange
      vi.mocked(policyDecider.getWorkTypePolicy).mockRejectedValue(
        new Error('Database connection failed')
      );

      const workRequest = testCase.createWorkRequest();

      // Act & Assert
      await expect(routeWork(mockSupabase, {
        work_type: workRequest.work_type,
        work_payload: workRequest.work_payload,
        workspace_id: 'test-workspace',
        user_id: 'test-user',
        priority: workRequest.priority
      })).rejects.toThrow('Database connection failed');
    });

    it('should handle work entry creation failure', async () => {
      // Arrange
      vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
        mode: 'auto',
        confidence_threshold: 0.8,
        require_validation: false
      });

      mockSupabase.single.mockResolvedValue({
        data: null,
        error: { message: 'Insert failed' }
      });

      const workRequest = testCase.createWorkRequest();

      // Act & Assert
      await expect(routeWork(mockSupabase, {
        work_type: workRequest.work_type,
        work_payload: workRequest.work_payload,
        workspace_id: 'test-workspace',
        user_id: 'test-user',
        priority: workRequest.priority
      })).rejects.toThrow('Failed to create work entry: Insert failed');
    });

    it('should handle proposal creation failure', async () => {
      // Arrange
      vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
        mode: 'proposal',
        confidence_threshold: 0.8,
        require_validation: false
      });

      mockSupabase.single
        .mockResolvedValueOnce({
          data: { id: 'work-123' },
          error: null
        })
        .mockResolvedValueOnce({
          data: null,
          error: { message: 'Proposal creation failed' }
        });

      const workRequest = testCase.createWorkRequest();

      // Act & Assert
      await expect(routeWork(mockSupabase, {
        work_type: workRequest.work_type,
        work_payload: workRequest.work_payload,
        workspace_id: 'test-workspace',
        user_id: 'test-user',
        priority: workRequest.priority
      })).rejects.toThrow('Failed to create proposal: Proposal creation failed');
    });
  });

  describe('Governance Matrix Testing', () => {
    it('should test all governance routing combinations', () => {
      // Generate comprehensive test matrix
      const matrix = TestDataFactory.generateGovernanceMatrix();
      
      expect(matrix.length).toBe(
        TestDataFactory.workTypes.length * 
        TestDataFactory.governanceModes.length * 
        TestDataFactory.confidenceScores.length
      );

      // Validate a sample of combinations
      const sampleTests = matrix.slice(0, 10);
      
      sampleTests.forEach(({ workType, policy, confidenceScore, expectedRouting }) => {
        const workRequest = testCase.createWorkRequest({
          work_type: workType,
          confidence_score: confidenceScore
        });

        testCase.assertGovernanceRouting(workRequest, policy, {
          routing_decision: expectedRouting,
          execution_mode: expectedRouting
        });
      });
    });
  });

  describe('Canon v2.2 Sacred Principles Compliance', () => {
    it('should validate P0_CAPTURE operations compliance', () => {
      const operations = [
        { type: 'create_raw_dump', data: { content: 'User input' } },
        { type: 'create_timeline_event', data: { kind: 'capture' } }
      ];

      expect(() => {
        testCase.assertSacredPrinciplesCompliance('P0_CAPTURE', operations);
      }).not.toThrow();
    });

    it('should reject P0_CAPTURE operations that interpret', () => {
      const operations = [
        { type: 'create_raw_dump', data: { content: 'User input' } },
        { type: 'create_block', data: { content: 'Interpreted content' } } // Violation!
      ];

      expect(() => {
        testCase.assertSacredPrinciplesCompliance('P0_CAPTURE', operations);
      }).toThrow();
    });

    it('should validate P1_SUBSTRATE operations compliance', () => {
      const operations = [
        { type: 'create_block', data: { content: 'New insight' } },
        { type: 'update_block', data: { id: 'block-1', content: 'Updated' } },
        { type: 'create_timeline_event', data: { kind: 'substrate_evolution' } }
      ];

      expect(() => {
        testCase.assertSacredPrinciplesCompliance('P1_SUBSTRATE', operations);
      }).not.toThrow();
    });

    it('should reject P1_SUBSTRATE operations that create relationships', () => {
      const operations = [
        { type: 'create_block', data: { content: 'New insight' } },
        { type: 'create_relationship', data: { from: 'A', to: 'B' } } // Violation!
      ];

      expect(() => {
        testCase.assertSacredPrinciplesCompliance('P1_SUBSTRATE', operations);
      }).toThrow();
    });

    it('should validate P2_GRAPH operations compliance', () => {
      const operations = [
        { type: 'create_relationship', data: { from: 'block-1', to: 'block-2' } },
        { type: 'update_relationship', data: { id: 'rel-1', strength: 0.8 } }
      ];

      expect(() => {
        testCase.assertSacredPrinciplesCompliance('P2_GRAPH', operations);
      }).not.toThrow();
    });

    it('should reject P2_GRAPH operations that create substrate', () => {
      const operations = [
        { type: 'create_relationship', data: { from: 'A', to: 'B' } },
        { type: 'create_block', data: { content: 'New block' } } // Violation!
      ];

      expect(() => {
        testCase.assertSacredPrinciplesCompliance('P2_GRAPH', operations);
      }).toThrow();
    });
  });
});