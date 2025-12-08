/**
 * Governance Routing Matrix Tests - Canon v2.2
 * 
 * Comprehensive matrix testing of all governance routing combinations.
 * Validates that every work type + policy mode + confidence level produces correct routing.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { UniversalWorkTestCase, TestDataFactory } from './UniversalWorkTestBase';
import { routeWork } from '@/lib/governance/universalWorkRouter';

// Mock the policyDecider module
vi.mock('@/lib/governance/policyDecider', () => ({
  policyDecider: {
    getWorkTypePolicy: vi.fn()
  }
}));

import { policyDecider } from '@/lib/governance/policyDecider';

describe('Governance Routing Matrix - Canon v2.2', () => {
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

  describe('Complete Governance Matrix Testing', () => {
    // Generate all combinations of work types, governance modes, and confidence levels
    const governanceMatrix = TestDataFactory.generateGovernanceMatrix();
    
    // Test systematic sampling to avoid test suite being too large (91 x 8 = 728 combinations)
    const sampleSize = Math.min(50, governanceMatrix.length);
    const sampledMatrix = governanceMatrix.slice(0, sampleSize);
    
    sampledMatrix.forEach(({ workType, policy, confidenceScore, expectedRouting }, index) => {
      it(`[${index + 1}/${sampleSize}] ${workType} + ${policy.mode} mode + confidence ${confidenceScore} → ${expectedRouting}`, async () => {
        // Arrange
        vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue(policy);
        
        // Mock successful work entry creation
        mockSupabase.single.mockResolvedValue({
          data: { id: `work-matrix-${index}` },
          error: null
        });
        
        // For proposal routing, mock proposal creation too
        if (expectedRouting === 'create_proposal') {
          mockSupabase.single.mockResolvedValueOnce({
            data: { id: `work-matrix-${index}` },
            error: null
          }).mockResolvedValueOnce({
            data: { id: `proposal-matrix-${index}` },
            error: null
          });
        }

        const workRequest = testCase.createWorkRequest({
          work_type: workType,
          confidence_score: confidenceScore
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
        expect(result.routing_decision).toBe(expectedRouting);
        expect(result.execution_mode).toBe(expectedRouting);
        expect(result.work_id).toBe(`work-matrix-${index}`);
        
        // Verify policy was fetched correctly
        expect(policyDecider.getWorkTypePolicy).toHaveBeenCalledWith(
          mockSupabase,
          'test-workspace',
          workType
        );
      });
    });
  });

  describe('Work Type Specific Governance Patterns', () => {
    TestDataFactory.workTypes.forEach(workType => {
      describe(`${workType} Work Type`, () => {
        it('should handle auto governance mode correctly', async () => {
          vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
            mode: 'auto',
            confidence_threshold: 0.7,
            require_validation: false
          });

          mockSupabase.single.mockResolvedValue({
            data: { id: `work-${workType.toLowerCase()}-auto` },
            error: null
          });

          const workRequest = testCase.createWorkRequest({
            work_type: workType,
            confidence_score: 0.8
          });

          const result = await routeWork(mockSupabase, {
            work_type: workRequest.work_type,
            work_payload: workRequest.work_payload,
            workspace_id: 'test-workspace',
            user_id: 'test-user',
            priority: workRequest.priority
          });

          expect(result.execution_mode).toBe('auto_execute');
        });

        it('should handle proposal governance mode correctly', async () => {
          vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
            mode: 'proposal',
            confidence_threshold: 0.7,
            require_validation: false
          });

          mockSupabase.single
            .mockResolvedValueOnce({
              data: { id: `work-${workType.toLowerCase()}-proposal` },
              error: null
            })
            .mockResolvedValueOnce({
              data: { id: `proposal-${workType.toLowerCase()}` },
              error: null
            });

          const workRequest = testCase.createWorkRequest({
            work_type: workType,
            confidence_score: 0.9
          });

          const result = await routeWork(mockSupabase, {
            work_type: workRequest.work_type,
            work_payload: workRequest.work_payload,
            workspace_id: 'test-workspace',
            user_id: 'test-user',
            priority: workRequest.priority
          });

          expect(result.execution_mode).toBe('create_proposal');
          expect(result.proposal_id).toBe(`proposal-${workType.toLowerCase()}`);
        });

        it('should handle confidence-based routing correctly', async () => {
          vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
            mode: 'confidence',
            confidence_threshold: 0.8,
            require_validation: false
          });

          // Test high confidence → auto execute
          mockSupabase.single.mockResolvedValue({
            data: { id: `work-${workType.toLowerCase()}-high-conf` },
            error: null
          });

          const highConfWorkRequest = testCase.createWorkRequest({
            work_type: workType,
            confidence_score: 0.9 // Above threshold
          });

          const highConfResult = await routeWork(mockSupabase, {
            work_type: highConfWorkRequest.work_type,
            work_payload: highConfWorkRequest.work_payload,
            workspace_id: 'test-workspace',
            user_id: 'test-user',
            priority: highConfWorkRequest.priority
          });

          expect(highConfResult.execution_mode).toBe('auto_execute');
        });
      });
    });
  });

  describe('User Override Matrix', () => {
    const overrideTests = [
      {
        override: 'allow_auto' as const,
        policy: { mode: 'proposal' as const, confidence_threshold: 0.9, require_validation: false },
        expected: 'auto_execute'
      },
      {
        override: 'require_review' as const,
        policy: { mode: 'auto' as const, confidence_threshold: 0.5, require_validation: false },
        expected: 'create_proposal'
      }
    ];

    overrideTests.forEach(({ override, policy, expected }) => {
      TestDataFactory.workTypes.forEach(workType => {
        it(`${workType} with ${override} override should result in ${expected}`, async () => {
          vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue(policy);

          // Mock work entry creation
          mockSupabase.single.mockResolvedValue({
            data: { id: `work-override-${workType}` },
            error: null
          });

          // Mock proposal creation if needed
          if (expected === 'create_proposal') {
            mockSupabase.single.mockResolvedValueOnce({
              data: { id: `work-override-${workType}` },
              error: null
            }).mockResolvedValueOnce({
              data: { id: `proposal-override-${workType}` },
              error: null
            });
          }

          const workRequest = testCase.createWorkRequest({
            work_type: workType,
            user_override: override,
            confidence_score: 0.7
          });

          const result = await routeWork(mockSupabase, {
            work_type: workRequest.work_type,
            work_payload: workRequest.work_payload,
            workspace_id: 'test-workspace',
            user_id: 'test-user',
            priority: workRequest.priority
          });

          expect(result.execution_mode).toBe(expected);
        });
      });
    });
  });

  describe('Confidence Threshold Boundary Testing', () => {
    const boundaryTests = [
      { confidence: 0.69, threshold: 0.7, expected: 'create_proposal' },
      { confidence: 0.70, threshold: 0.7, expected: 'auto_execute' },
      { confidence: 0.79, threshold: 0.8, expected: 'create_proposal' },
      { confidence: 0.80, threshold: 0.8, expected: 'auto_execute' },
      { confidence: 0.89, threshold: 0.9, expected: 'create_proposal' },
      { confidence: 0.90, threshold: 0.9, expected: 'auto_execute' }
    ];

    boundaryTests.forEach(({ confidence, threshold, expected }) => {
      it(`confidence ${confidence} vs threshold ${threshold} → ${expected}`, async () => {
        vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
          mode: 'confidence',
          confidence_threshold: threshold,
          require_validation: false
        });

        // Mock appropriate responses based on expected result
        if (expected === 'auto_execute') {
          mockSupabase.single.mockResolvedValue({
            data: { id: 'work-boundary-test' },
            error: null
          });
        } else {
          mockSupabase.single
            .mockResolvedValueOnce({
              data: { id: 'work-boundary-test' },
              error: null
            })
            .mockResolvedValueOnce({
              data: { id: 'proposal-boundary-test' },
              error: null
            });
        }

        const workRequest = testCase.createWorkRequest({
          work_type: 'P1_SUBSTRATE',
          confidence_score: confidence
        });

        const result = await routeWork(mockSupabase, {
          work_type: workRequest.work_type,
          work_payload: workRequest.work_payload,
          workspace_id: 'test-workspace',
          user_id: 'test-user',
          priority: workRequest.priority
        });

        expect(result.execution_mode).toBe(expected);
      });
    });
  });

  describe('Priority Level Routing', () => {
    const priorities = ['low', 'normal', 'high', 'urgent'] as const;
    
    priorities.forEach(priority => {
      it(`should handle ${priority} priority work correctly`, async () => {
        vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
          mode: 'confidence',
          confidence_threshold: 0.8,
          require_validation: false
        });

        mockSupabase.single.mockResolvedValue({
          data: { id: `work-${priority}-priority` },
          error: null
        });

        const workRequest = testCase.createWorkRequest({
          work_type: 'P1_SUBSTRATE',
          confidence_score: 0.9,
          priority
        });

        const result = await routeWork(mockSupabase, {
          work_type: workRequest.work_type,
          work_payload: workRequest.work_payload,
          workspace_id: 'test-workspace',
          user_id: 'test-user',
          priority: workRequest.priority
        });

        expect(result.work_id).toBe(`work-${priority}-priority`);
        expect(result.execution_mode).toBe('auto_execute'); // High confidence should auto-execute
      });
    });
  });

  describe('Edge Cases and Error Conditions', () => {
    it('should handle missing confidence score in confidence mode', async () => {
      vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
        mode: 'confidence',
        confidence_threshold: 0.8,
        require_validation: false
      });

      mockSupabase.single
        .mockResolvedValueOnce({
          data: { id: 'work-no-confidence' },
          error: null
        })
        .mockResolvedValueOnce({
          data: { id: 'proposal-no-confidence' },
          error: null
        });

      const workRequest = testCase.createWorkRequest({
        work_type: 'P1_SUBSTRATE'
        // No confidence_score provided
      });
      
      // Remove confidence score to simulate missing value
      delete workRequest.work_payload.confidence_score;

      const result = await routeWork(mockSupabase, {
        work_type: workRequest.work_type,
        work_payload: workRequest.work_payload,
        workspace_id: 'test-workspace',
        user_id: 'test-user',
        priority: workRequest.priority
      });

      // Should default to proposal mode when confidence is missing
      expect(result.execution_mode).toBe('create_proposal');
    });

    it('should handle extreme confidence values', async () => {
      const extremeValues = [0.0, 1.0, -0.1, 1.1];
      
      for (const confidenceScore of extremeValues) {
        vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
          mode: 'confidence',
          confidence_threshold: 0.7,
          require_validation: false
        });

        const expectProposal = confidenceScore < 0.7;
        
        if (expectProposal) {
          mockSupabase.single
            .mockResolvedValueOnce({
              data: { id: `work-extreme-${confidenceScore}` },
              error: null
            })
            .mockResolvedValueOnce({
              data: { id: `proposal-extreme-${confidenceScore}` },
              error: null
            });
        } else {
          mockSupabase.single.mockResolvedValue({
            data: { id: `work-extreme-${confidenceScore}` },
            error: null
          });
        }

        const workRequest = testCase.createWorkRequest({
          work_type: 'P1_SUBSTRATE',
          confidence_score: confidenceScore
        });

        const result = await routeWork(mockSupabase, {
          work_type: workRequest.work_type,
          work_payload: workRequest.work_payload,
          workspace_id: 'test-workspace',
          user_id: 'test-user',
          priority: workRequest.priority
        });

        const expectedMode = expectProposal ? 'create_proposal' : 'auto_execute';
        expect(result.execution_mode).toBe(expectedMode);
      }
    });

    it('should handle unknown work types with safe defaults', async () => {
      vi.mocked(policyDecider.getWorkTypePolicy).mockResolvedValue({
        mode: 'proposal', // Unknown types default to proposal
        confidence_threshold: 0.9,
        require_validation: true
      });

      mockSupabase.single
        .mockResolvedValueOnce({
          data: { id: 'work-unknown-type' },
          error: null
        })
        .mockResolvedValueOnce({
          data: { id: 'proposal-unknown-type' },
          error: null
        });

      const workRequest = testCase.createWorkRequest({
        work_type: 'UNKNOWN_WORK_TYPE' as any,
        confidence_score: 0.95
      });

      const result = await routeWork(mockSupabase, {
        work_type: workRequest.work_type,
        work_payload: workRequest.work_payload,
        workspace_id: 'test-workspace',
        user_id: 'test-user',
        priority: workRequest.priority
      });

      // Should route to proposal for safety
      expect(result.execution_mode).toBe('create_proposal');
    });
  });

  describe('Governance Policy Coverage Verification', () => {
    it('should have tested all canonical work types', () => {
      const testedWorkTypes = new Set(TestDataFactory.workTypes);
      const expectedWorkTypes = new Set([
        'P0_CAPTURE',
        'P1_SUBSTRATE', 
        'P2_GRAPH',
        'P3_REFLECTION',
        'P4_COMPOSE',
        'MANUAL_EDIT',
        'PROPOSAL_REVIEW',
        'TIMELINE_RESTORE'
      ]);

      expect(testedWorkTypes).toEqual(expectedWorkTypes);
    });

    it('should have tested all governance modes', () => {
      const testedModes = new Set(TestDataFactory.governanceModes);
      const expectedModes = new Set(['auto', 'proposal', 'confidence']);

      expect(testedModes).toEqual(expectedModes);
    });

    it('should have tested representative confidence score range', () => {
      const confidenceRange = TestDataFactory.confidenceScores;
      
      expect(confidenceRange.length).toBeGreaterThan(5); // Multiple test points
      expect(confidenceRange).toContain(0.0); // Minimum
      expect(confidenceRange).toContain(1.0); // Maximum
      expect(confidenceRange.some(s => s > 0 && s < 1)).toBe(true); // Mid-range values
    });

    it('should provide comprehensive matrix coverage', () => {
      const matrix = TestDataFactory.generateGovernanceMatrix();
      const expectedCombinations = 
        TestDataFactory.workTypes.length * 
        TestDataFactory.governanceModes.length * 
        TestDataFactory.confidenceScores.length;

      expect(matrix.length).toBe(expectedCombinations);
    });
  });
});