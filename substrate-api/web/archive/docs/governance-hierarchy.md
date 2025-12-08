# Governance Hierarchy - Canon Documentation

## Overview
This document clarifies the hierarchical relationship between user governance settings and automated systems to prevent future confusion.

## Governance Settings Hierarchy

### Level 1: User Settings (`/governance/settings`)
**Authority**: Workspace Owner Only
**Interface**: `GovernanceSettingsClient.tsx`
**Storage**: `workspace_governance_settings` table

User selects between two modes:
- **"Review everything"** (`mode: 'proposal'`) - All changes require manual approval
- **"Smart review"** (`mode: 'hybrid'`) - Safe changes auto-approved, risky changes reviewed

### Level 2: Flags Translation (`flagsServer.ts`)
**Authority**: System (Server-side)
**Function**: Converts user settings into technical `WorkspaceFlags`

```typescript
const flags = await getWorkspaceFlags(supabase, workspace_id);
// flags.ep.manual_edit === 'proposal' | 'hybrid'
// flags.ep.graph_action === 'proposal' | 'hybrid'
```

### Level 3: Decision Gateway (`decisionGateway.ts`)
**Authority**: System (Governance Engine)
**Function**: Routes operations based on user settings

#### Proposal Batching (Priority 1)
- **Always Active** when `governance_enabled: true`
- Reduces proposal volume for BOTH "proposal" and "hybrid" modes
- Governance optimization, not user-controlled

#### Smart Auto-Approval (Priority 2) 
- **Only Active** when user selects "Smart review" (`hybrid` mode)
- **Completely Disabled** when user selects "Review everything" (`proposal` mode)
- Respects user's explicit governance preference

## Critical Enforcement Points

### ✅ Correct Implementation
```typescript
// In decisionGateway.ts
const entryPointPolicy = flags.ep[entry_point] || 'proposal';
const isHybridMode = entryPointPolicy === 'hybrid';

if (isHybridMode) {
  // Only run auto-approval if user enabled "Smart review"
  const autoApprovalResult = await evaluateAutoApproval(...);
} else {
  console.log('Auto-approval disabled - user selected "Review everything"');
}
```

### ❌ Wrong Implementation 
```typescript
// This would bypass user settings - NEVER DO THIS
if (decision.route === 'governance') {
  // Auto-approval runs regardless of user preference - WRONG!
  const autoApprovalResult = await evaluateAutoApproval(...);
}
```

## Entry Point Policy Mapping

| User Setting | Entry Point Policy | Batching | Auto-Approval |
|-------------|-------------------|----------|---------------|
| "Review everything" | `proposal` | ✅ Active | ❌ Disabled |
| "Smart review" | `hybrid` | ✅ Active | ✅ Active |

## Special Cases

### P0 Capture (`onboarding_dump`)
- **Always** `direct` route (Canon compliance)
- No governance - immediate substrate creation
- Neither batching nor auto-approval applies

### Timeline Restore (`timeline_restore`)
- **Always** `proposal` route (safety)  
- Batching applies, auto-approval does not

## Validation Checklist

Before deploying governance changes:

1. ✅ Auto-approval only runs in `hybrid` mode
2. ✅ Batching runs in both `proposal` and `hybrid` modes  
3. ✅ User can disable auto-approval by selecting "Review everything"
4. ✅ P0 capture remains `direct` regardless of settings
5. ✅ Timeline restore always requires review

## Future Development Notes

- **Never add governance automation** without checking user mode preference
- **Always document** new automation hierarchy relationships here
- **Test both modes** when implementing governance changes
- **Respect user choice** - governance settings are not suggestions

## Canon Compliance

This hierarchy ensures:
- **Substrate Equality**: All substrate types follow same governance rules
- **User Sovereignty**: User retains ultimate control over governance strictness  
- **Governance Integrity**: Automation enhances but never bypasses user decisions