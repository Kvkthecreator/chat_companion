/**
 * Canon Test Setup
 * 
 * Provides test environment configuration for YARNNN canon compliance testing.
 * Ensures proper mocking and environment setup for sacred principles validation.
 */

import { vi } from 'vitest';

// Mock environment variables for canon testing
export const setupCanonTestEnvironment = () => {
  // Agent API configuration
  process.env.AGENT_API_URL = 'http://mock-agent-api';
  process.env.AGENT_API_KEY = 'mock-agent-key';
  
  // Governance configuration
  process.env.GOVERNANCE_ENABLED = 'true';
  process.env.GOVERNANCE_VALIDATOR_REQUIRED = 'true';
  process.env.GOVERNANCE_DIRECT_WRITES = 'false';
  process.env.GOVERNANCE_UI_ENABLED = 'true';
  
  // Pipeline configuration
  process.env.PIPELINE_BOUNDARIES_ENFORCED = 'true';
  process.env.SUBSTRATE_EQUALITY_ENFORCED = 'true';
  
  // Sacred principles enforcement
  process.env.ENFORCE_SACRED_PRINCIPLES = 'true';
  process.env.CAPTURE_IMMUTABILITY = 'true';
  process.env.AGENT_INTELLIGENCE_MANDATORY = 'true';
  process.env.NARRATIVE_DELIBERATION_REQUIRED = 'true';
};

// Mock Supabase client for canon testing
export const createMockSupabaseClient = () => ({
  from: vi.fn().mockReturnThis(),
  select: vi.fn().mockReturnThis(),
  insert: vi.fn().mockReturnThis(),
  update: vi.fn().mockReturnThis(),
  delete: vi.fn().mockReturnThis(),
  eq: vi.fn().mockReturnThis(),
  neq: vi.fn().mockReturnThis(),
  gt: vi.fn().mockReturnThis(),
  lt: vi.fn().mockReturnThis(),
  gte: vi.fn().mockReturnThis(),
  lte: vi.fn().mockReturnThis(),
  like: vi.fn().mockReturnThis(),
  ilike: vi.fn().mockReturnThis(),
  in: vi.fn().mockReturnThis(),
  contains: vi.fn().mockReturnThis(),
  order: vi.fn().mockReturnThis(),
  limit: vi.fn().mockReturnThis(),
  offset: vi.fn().mockReturnThis(),
  single: vi.fn().mockResolvedValue({ data: null, error: null }),
  rpc: vi.fn().mockResolvedValue({ data: null, error: null })
});

// Mock governance services for canon testing
export const mockGovernanceServices = () => {
  // Mock workspace flags
  vi.mock('@/lib/governance/flagsServer', () => ({
    getWorkspaceFlags: vi.fn().mockResolvedValue({
      governance_enabled: true,
      validator_required: true,
      direct_substrate_writes: false,
      governance_ui_enabled: true,
      ep: {
        onboarding_dump: 'proposal',
        manual_edit: 'proposal',
        document_edit: 'proposal',
        reflection_suggestion: 'direct',
        graph_action: 'proposal',
        timeline_restore: 'proposal'
      },
      default_blast_radius: 'Scoped',
      source: 'workspace_database'
    }),
    shouldUseGovernance: vi.fn().mockResolvedValue(true),
    isValidatorRequired: vi.fn().mockResolvedValue(true),
    allowDirectSubstrateWrites: vi.fn().mockResolvedValue(false),
    isGovernanceUIEnabled: vi.fn().mockResolvedValue(true)
  }));

  // Mock policy decider
  vi.mock('@/lib/governance/policyDecider', () => ({
    decide: vi.fn().mockReturnValue({
      route: 'proposal',
      require_validator: true,
      validator_mode: 'strict',
      effective_blast_radius: 'Scoped',
      reason: 'canon_testing_mode'
    })
  }));

  // Mock Supabase client
  vi.mock('@/lib/supabase/server', () => ({
    createSupabaseServerClient: vi.fn().mockResolvedValue(createMockSupabaseClient())
  }));
};

// Validate sacred principles compliance in test context
export const validateSacredPrinciplesCompliance = (testContext: any) => {
  const compliance = {
    capture_is_sacred: !!testContext.immutable_dumps,
    substrates_are_peers: !!testContext.equal_substrate_treatment,
    narrative_is_deliberate: !!testContext.authored_narrative,
    agent_intelligence_mandatory: !!testContext.agent_processing_required
  };

  const violations = Object.entries(compliance)
    .filter(([_, compliant]) => !compliant)
    .map(([principle]) => principle);

  return {
    compliant: violations.length === 0,
    violations,
    compliance
  };
};

// Canon test utilities
export const canonTestUtils = {
  setupCanonTestEnvironment,
  createMockSupabaseClient,
  mockGovernanceServices,
  validateSacredPrinciplesCompliance,
  
  // Test data factories aligned with canon
  createTestRawDump: (workspace_id: string, content: string) => ({
    id: `dump-${Math.random().toString(36).substr(2, 9)}`,
    content,
    workspace_id,
    content_type: 'text/plain',
    immutable: true,
    created_at: new Date().toISOString()
  }),
  
  createTestContextBlock: (workspace_id: string, content: string, semantic_type: string) => ({
    id: `block-${Math.random().toString(36).substr(2, 9)}`,
    content,
    semantic_type,
    workspace_id,
    agent_processed: true,
    created_at: new Date().toISOString()
  }),
  
  createTestDocument: (workspace_id: string, title: string, narrative: string, substrate_refs: any[]) => ({
    id: `doc-${Math.random().toString(36).substr(2, 9)}`,
    title,
    narrative_content: narrative,
    substrate_references: substrate_refs,
    workspace_id,
    deliberate_composition: true,
    created_at: new Date().toISOString()
  })
};

export default canonTestUtils;