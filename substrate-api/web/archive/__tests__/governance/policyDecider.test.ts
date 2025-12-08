import { describe, it, expect } from 'vitest';
import { decide, shouldRequireApproval, canBypassGovernance } from '@/lib/governance/policyDecider';
import { WorkspaceFlags } from '@/lib/governance/flagsServer';
import { ChangeDescriptor } from '@/lib/governance/changeDescriptor';

describe('PolicyDecider', () => {
  const baseWorkspaceFlags: WorkspaceFlags = {
    governance_enabled: true,
    validator_required: false,
    direct_substrate_writes: true,
    governance_ui_enabled: true,
    ep: {
      onboarding_dump: 'proposal',
      manual_edit: 'proposal',
      graph_action: 'proposal',
      timeline_restore: 'proposal'
    },
    default_blast_radius: 'Scoped',
    source: 'workspace_database'
  };

  const baseChangeDescriptor: ChangeDescriptor = {
    entry_point: 'manual_edit',
    actor_id: 'user-123',
    workspace_id: 'workspace-456',
    basket_id: 'basket-789',
    ops: [{
      type: 'CreateBlock',
      data: { content: 'Test content', semantic_type: 'goal' }
    }]
  };

  describe('Governance disabled scenarios', () => {
    it('should route to direct when governance disabled and direct writes allowed', () => {
      const flags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        governance_enabled: false,
        direct_substrate_writes: true
      };

      const decision = decide(flags, baseChangeDescriptor);

      expect(decision.route).toBe('direct');
      expect(decision.reason).toBe('governance_disabled');
      expect(decision.require_validator).toBe(false);
    });

    it('should route to proposal when governance disabled but direct writes blocked', () => {
      const flags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        governance_enabled: false,
        direct_substrate_writes: false
      };

      const decision = decide(flags, baseChangeDescriptor);

      expect(decision.route).toBe('proposal');
      expect(decision.reason).toBe('governance_disabled');
    });
  });

  describe('Entry point policy routing', () => {
    it('should respect direct policy for entry point', () => {
      const flags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        ep: { ...baseWorkspaceFlags.ep, manual_edit: 'direct' }
      };

      const decision = decide(flags, baseChangeDescriptor);

      expect(decision.route).toBe('direct');
      expect(decision.reason).toBe('ep_policy_direct:manual_edit');
    });

    it('should respect proposal policy for entry point', () => {
      const flags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        ep: { ...baseWorkspaceFlags.ep, manual_edit: 'proposal' }
      };

      const decision = decide(flags, baseChangeDescriptor);

      expect(decision.route).toBe('proposal');
      expect(decision.reason).toBe('ep_policy_proposal:manual_edit');
    });

    it('should force proposal when direct writes disabled', () => {
      const flags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        direct_substrate_writes: false,
        ep: { ...baseWorkspaceFlags.ep, manual_edit: 'direct' }
      };

      const decision = decide(flags, baseChangeDescriptor);

      expect(decision.route).toBe('proposal');
      expect(decision.reason).toBe('ep_policy_direct:manual_edit:forced_proposal_no_direct_writes');
    });
  });

  describe('Hybrid policy risk assessment', () => {
    it('should route low-risk hybrid changes to direct', () => {
      const flags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        ep: { ...baseWorkspaceFlags.ep, manual_edit: 'hybrid' }
      };

      const lowRiskHints = {
        confidence: 0.9,
        conflicts: 0,
        complexity_score: 0.2
      };

      const decision = decide(flags, baseChangeDescriptor, lowRiskHints);

      expect(decision.route).toBe('direct');
      expect(decision.reason).toContain('ep_policy_hybrid:manual_edit:low_risk_assessment');
    });

    it('should route high-risk hybrid changes to proposal', () => {
      const flags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        ep: { ...baseWorkspaceFlags.ep, manual_edit: 'hybrid' }
      };

      const highRiskHints = {
        confidence: 0.4,
        conflicts: 5,
        complexity_score: 0.9
      };

      const decision = decide(flags, baseChangeDescriptor, highRiskHints);

      expect(decision.route).toBe('proposal');
      expect(decision.reason).toContain('ep_policy_hybrid:manual_edit:low_confidence');
    });

    it('should route global blast radius to proposal in hybrid mode', () => {
      const flags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        ep: { ...baseWorkspaceFlags.ep, manual_edit: 'hybrid' }
      };

      const globalChange: ChangeDescriptor = {
        ...baseChangeDescriptor,
        blast_radius: 'Global'
      };

      const decision = decide(flags, globalChange);

      expect(decision.route).toBe('proposal');
      expect(decision.reason).toContain('global_blast_radius');
    });
  });

  describe('Validator requirements', () => {
    it('should require validator when globally required', () => {
      const flags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        validator_required: true
      };

      const decision = decide(flags, baseChangeDescriptor);

      expect(decision.require_validator).toBe(true);
      expect(decision.validator_mode).toBe('strict');
    });

    it('should require validator for high-risk proposals', () => {
      const globalChange: ChangeDescriptor = {
        ...baseChangeDescriptor,
        blast_radius: 'Global'
      };

      const decision = decide(baseWorkspaceFlags, globalChange);

      expect(decision.require_validator).toBe(true);
    });

    it('should not require validator for low-risk direct commits', () => {
      const flags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        ep: { ...baseWorkspaceFlags.ep, manual_edit: 'direct' }
      };

      const decision = decide(flags, baseChangeDescriptor);

      expect(decision.require_validator).toBe(false);
    });
  });

  describe('Blast radius computation', () => {
    it('should use explicit blast radius when provided', () => {
      const explicitChange: ChangeDescriptor = {
        ...baseChangeDescriptor,
        blast_radius: 'Global'
      };

      const decision = decide(baseWorkspaceFlags, explicitChange);

      expect(decision.effective_blast_radius).toBe('Global');
    });

    it('should use workspace default when not specified', () => {
      const decision = decide(baseWorkspaceFlags, baseChangeDescriptor);

      expect(decision.effective_blast_radius).toBe('Scoped');
    });

    it('should infer from operation types when neither provided', () => {
      const flags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        default_blast_radius: 'Local'
      };

      const highImpactChange: ChangeDescriptor = {
        ...baseChangeDescriptor,
        ops: [{
          type: 'PromoteScope',
          data: { block_id: 'block-123', to_scope: 'GLOBAL' }
        }]
      };

      const decision = decide(flags, highImpactChange);

      expect(decision.effective_blast_radius).toBe('Global');
    });
  });

  describe('Convenience functions', () => {
    it('shouldRequireApproval should match decision route', () => {
      const proposalFlags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        ep: { ...baseWorkspaceFlags.ep, manual_edit: 'proposal' }
      };

      const directFlags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        ep: { ...baseWorkspaceFlags.ep, manual_edit: 'direct' }
      };

      expect(shouldRequireApproval(proposalFlags, baseChangeDescriptor)).toBe(true);
      expect(shouldRequireApproval(directFlags, baseChangeDescriptor)).toBe(false);
    });

    it('canBypassGovernance should respect flags and entry point', () => {
      const disabledFlags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        governance_enabled: false
      };

      const directFlags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        ep: { ...baseWorkspaceFlags.ep, manual_edit: 'direct' }
      };

      const proposalFlags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        ep: { ...baseWorkspaceFlags.ep, manual_edit: 'proposal' }
      };

      expect(canBypassGovernance(disabledFlags, 'manual_edit')).toBe(true);
      expect(canBypassGovernance(directFlags, 'manual_edit')).toBe(true);
      expect(canBypassGovernance(proposalFlags, 'manual_edit')).toBe(false);
    });
  });

  describe('Complex scenarios', () => {
    it('should handle multiple operations with mixed risk', () => {
      const complexChange: ChangeDescriptor = {
        ...baseChangeDescriptor,
        ops: [
          { type: 'CreateBlock', data: { content: 'Goal 1', semantic_type: 'goal' } },
          { type: 'CreateContextItem', data: { label: 'Context 1' } },
          { type: 'PromoteScope', data: { block_id: 'block-123', to_scope: 'WORKSPACE' } },
          { type: 'MergeContextItems', data: { from_ids: ['a', 'b'], canonical_id: 'c' } }
        ]
      };

      const hybridFlags: WorkspaceFlags = {
        ...baseWorkspaceFlags,
        ep: { ...baseWorkspaceFlags.ep, manual_edit: 'hybrid' }
      };

      const decision = decide(hybridFlags, complexChange);

      expect(decision.route).toBe('proposal');
      expect(decision.reason).toContain('high_scope_impact');
      expect(decision.effective_blast_radius).toBe('Global');
    });

    it('should escalate validator mode for high-impact operations', () => {
      const highImpactChange: ChangeDescriptor = {
        ...baseChangeDescriptor,
        blast_radius: 'Global',
        ops: [
          { type: 'PromoteScope', data: { block_id: 'block-123', to_scope: 'GLOBAL' } }
        ]
      };

      const decision = decide(baseWorkspaceFlags, highImpactChange);

      expect(decision.require_validator).toBe(true);
      expect(decision.effective_blast_radius).toBe('Global');
    });
  });
});