/**
 * Universal Work Testing Framework - Canon v2.2
 * 
 * Base test utilities for all Universal Work Orchestration testing.
 * Provides standardized factories, assertions, and test data for governance validation.
 */

import { vi, expect } from 'vitest';

export interface WorkRequest {
  work_type: string;
  work_payload: {
    operations: Array<{
      type: string;
      data: Record<string, any>;
    }>;
    basket_id: string;
    confidence_score?: number;
    user_override?: 'require_review' | 'allow_auto';
    trace_id?: string;
    provenance?: string[];
  };
  priority: 'low' | 'normal' | 'high' | 'urgent';
}

export interface WorkRoutingResult {
  work_id: string;
  routing_decision: 'auto_execute' | 'create_proposal' | 'confidence_routing';
  execution_mode: 'auto_execute' | 'create_proposal' | 'confidence_routing';
  proposal_id?: string;
  status_url: string;
}

export interface GovernancePolicy {
  mode: 'auto' | 'proposal' | 'confidence';
  confidence_threshold: number;
  require_validation: boolean;
}

/**
 * Base test case class for Universal Work operations
 */
export class UniversalWorkTestCase {
  protected mockSupabase: any;
  protected mockApiClient: any;

  constructor() {
    this.setupMocks();
  }

  private setupMocks() {
    this.mockSupabase = {
      from: vi.fn().mockReturnThis(),
      select: vi.fn().mockReturnThis(),
      insert: vi.fn().mockReturnThis(),
      update: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      single: vi.fn().mockReturnThis(),
      execute: vi.fn(),
    };

    this.mockApiClient = {
      request: vi.fn(),
    };
  }

  /**
   * Factory for creating standard work requests
   */
  createWorkRequest(options: {
    work_type?: string;
    operations?: Array<{ type: string; data: any }>;
    basket_id?: string;
    confidence_score?: number;
    user_override?: 'require_review' | 'allow_auto';
    priority?: 'low' | 'normal' | 'high' | 'urgent';
  } = {}): WorkRequest {
    return {
      work_type: options.work_type || 'P1_SUBSTRATE',
      work_payload: {
        operations: options.operations || [{
          type: 'create_block',
          data: {
            content: 'Test block content',
            semantic_type: 'insight',
            basket_id: options.basket_id || 'test-basket-id',
          }
        }],
        basket_id: options.basket_id || 'test-basket-id',
        confidence_score: options.confidence_score ?? 0.8,
        user_override: options.user_override,
        trace_id: `test-trace-${Date.now()}`,
        provenance: ['test-source']
      },
      priority: options.priority || 'normal'
    };
  }

  /**
   * Factory for governance policy configurations
   */
  createGovernancePolicy(options: {
    mode?: 'auto' | 'proposal' | 'confidence';
    confidence_threshold?: number;
    require_validation?: boolean;
  } = {}): GovernancePolicy {
    return {
      mode: options.mode || 'proposal',
      confidence_threshold: options.confidence_threshold ?? 0.8,
      require_validation: options.require_validation ?? false
    };
  }

  /**
   * Mock workspace governance settings
   */
  mockWorkspaceGovernance(policies: Record<string, GovernancePolicy> = {}) {
    const defaultPolicies = {
      ep_onboarding_dump: 'proposal',
      ep_manual_edit: 'proposal',
      confidence_threshold_onboarding: 0.8,
      confidence_threshold_manual: 0.6,
      validator_required: false,
    };

    this.mockSupabase.execute.mockResolvedValue({
      data: { ...defaultPolicies, ...policies },
      error: null
    });
  }

  /**
   * Assert that governance routing decisions are correct
   */
  assertGovernanceRouting(
    workRequest: WorkRequest,
    policy: GovernancePolicy,
    expectedResult: Partial<WorkRoutingResult>
  ) {
    // Test the routing logic
    const actualRoutingDecision = this.computeExpectedRouting(workRequest, policy);
    
    if (expectedResult.routing_decision) {
      expect(actualRoutingDecision).toBe(expectedResult.routing_decision);
    }
    if (expectedResult.execution_mode) {
      expect(actualRoutingDecision).toBe(expectedResult.execution_mode);
    }
  }

  /**
   * Compute expected routing decision based on governance policy
   */
  private computeExpectedRouting(
    request: WorkRequest,
    policy: GovernancePolicy
  ): string {
    // User override takes precedence
    if (request.work_payload.user_override) {
      return request.work_payload.user_override === 'allow_auto' 
        ? 'auto_execute' 
        : 'create_proposal';
    }

    // Apply policy-based routing
    switch (policy.mode) {
      case 'auto':
        return 'auto_execute';
      case 'proposal':
        return 'create_proposal';
      case 'confidence':
        const confidence = request.work_payload.confidence_score ?? 0.5;
        return confidence >= policy.confidence_threshold
          ? 'auto_execute'
          : 'create_proposal';
      default:
        return 'create_proposal'; // Safe default
    }
  }

  /**
   * Assert Sacred Principles compliance
   */
  assertSacredPrinciplesCompliance(
    workType: string,
    operations: Array<{ type: string; data: any }>
  ) {
    switch (workType) {
      case 'P0_CAPTURE':
        this.assertP0CaptureCompliance(operations);
        break;
      case 'P1_SUBSTRATE':
        this.assertP1SubstrateCompliance(operations);
        break;
      case 'P2_GRAPH':
        this.assertP2GraphCompliance(operations);
        break;
      case 'P3_REFLECTION':
        this.assertP3ReflectionCompliance(operations);
        break;
      case 'P4_COMPOSE':
        this.assertP4ComposeCompliance(operations);
        break;
      case 'MANUAL_EDIT':
        this.assertManualEditCompliance(operations);
        break;
    }
  }

  private assertP0CaptureCompliance(operations: Array<{ type: string; data: any }>) {
    // P0: Only writes raw_dumps, never interprets
    operations.forEach(op => {
      expect(['create_raw_dump', 'create_timeline_event']).toContain(op.type);
      expect(op.type).not.toBe('create_block'); // No interpretation in P0
      expect(op.type).not.toBe('create_relationship'); // No relationships in P0
    });
  }

  private assertP1SubstrateCompliance(operations: Array<{ type: string; data: any }>) {
    // P1: Creates, Updates, and Merges substrate via governance proposals
    operations.forEach(op => {
      expect([
        'create_block', 'update_block', 'merge_blocks',
        'create_context_items', 'update_context_items',
        'create_timeline_event'
      ]).toContain(op.type);
      expect(op.type).not.toBe('create_relationship'); // No relationships in P1
      expect(op.type).not.toBe('create_reflection'); // No artifacts in P1
    });
  }

  private assertP2GraphCompliance(operations: Array<{ type: string; data: any }>) {
    // P2: Creates relationships only, never creates new substrate
    operations.forEach(op => {
      expect(['create_relationship', 'update_relationship', 'create_timeline_event']).toContain(op.type);
      expect(op.type).not.toBe('create_block'); // No new substrate in P2
      expect(op.type).not.toBe('create_context_items'); // No new substrate in P2
    });
  }

  private assertP3ReflectionCompliance(operations: Array<{ type: string; data: any }>) {
    // P3: Creates reflections only, never modifies substrate
    operations.forEach(op => {
      expect(['create_reflection', 'update_reflection', 'create_timeline_event']).toContain(op.type);
      expect(op.type).not.toBe('create_block'); // No substrate modification in P3
      expect(op.type).not.toBe('update_block'); // No substrate modification in P3
    });
  }

  private assertP4ComposeCompliance(operations: Array<{ type: string; data: any }>) {
    // P4: Creates documents only, consumes substrate
    operations.forEach(op => {
      expect(['create_document', 'update_document', 'create_timeline_event']).toContain(op.type);
      expect(op.type).not.toBe('create_block'); // No substrate creation in P4
      expect(op.type).not.toBe('create_relationship'); // No relationships in P4
    });
  }

  private assertManualEditCompliance(operations: Array<{ type: string; data: any }>) {
    // MANUAL_EDIT: User-initiated substrate changes via governance
    operations.forEach(op => {
      expect([
        'update_block', 'delete_block',
        'update_context_items', 'delete_context_items',
        'create_timeline_event'
      ]).toContain(op.type);
      // Manual edits should not create new substrate (use specialized endpoints)
      expect(op.type).not.toBe('create_block');
    });
  }

  /**
   * Create mock work status response
   */
  createMockWorkStatus(workId: string, status: string = 'pending') {
    return {
      work_id: workId,
      work_type: 'P1_SUBSTRATE',
      processing_state: status,
      created_at: new Date().toISOString(),
      governance_policy: this.createGovernancePolicy(),
      operations: [{
        type: 'create_block',
        data: { content: 'Test content' }
      }]
    };
  }
}

/**
 * Common test data factories
 */
export const TestDataFactory = {
  /**
   * Standard work types for testing
   */
  workTypes: [
    'P0_CAPTURE',
    'P1_SUBSTRATE', 
    'P2_GRAPH',
    'P3_REFLECTION',
    'P4_COMPOSE',
    'MANUAL_EDIT',
    'PROPOSAL_REVIEW',
    'TIMELINE_RESTORE'
  ] as const,

  /**
   * Governance mode combinations
   */
  governanceModes: [
    'auto',
    'proposal', 
    'confidence'
  ] as const,

  /**
   * Confidence score test ranges
   */
  confidenceScores: [
    0.0, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0
  ],

  /**
   * Generate all governance routing combinations for matrix testing
   */
  generateGovernanceMatrix() {
    const combinations = [];
    
    for (const workType of this.workTypes) {
      for (const mode of this.governanceModes) {
        for (const confidence of this.confidenceScores) {
          combinations.push({
            workType,
            policy: { mode, confidence_threshold: 0.7, require_validation: false },
            confidenceScore: confidence,
            expectedRouting: this.computeExpectedRouting(mode, confidence, 0.7)
          });
        }
      }
    }
    
    return combinations;
  },

  computeExpectedRouting(mode: string, confidence: number, threshold: number): string {
    switch (mode) {
      case 'auto':
        return 'auto_execute';
      case 'proposal':
        return 'create_proposal';
      case 'confidence':
        return confidence >= threshold ? 'auto_execute' : 'create_proposal';
      default:
        return 'create_proposal';
    }
  }
};