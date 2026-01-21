# Architecture Decision Records

This folder contains Architecture Decision Records (ADRs) documenting significant technical decisions.

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](ADR-001-memory-architecture.md) | Memory System Architecture | Draft | 2025-01 |
| [ADR-002](ADR-002-personalization-system.md) | Personalization System | Draft | 2025-01 |

## What is an ADR?

An ADR records a significant architectural decision along with its context and consequences. We use ADRs to:

- Document the "why" behind decisions
- Provide context for future developers
- Track the evolution of the system

## ADR Status

- **Draft**: Under discussion
- **Proposed**: Ready for review
- **Accepted**: Decision made, implementation pending or in progress
- **Implemented**: Fully deployed
- **Deprecated**: No longer applies
- **Superseded**: Replaced by another ADR

## Template

Use this template for new ADRs:

```markdown
# ADR-XXX: Title

**Status**: Draft | Proposed | Accepted | Implemented | Deprecated | Superseded
**Date**: YYYY-MM-DD
**Deciders**: [list of people involved]

## Context

What is the issue? What is motivating this decision?

## Decision

What is the change being proposed or decided?

## Consequences

### Positive
- Benefit 1
- Benefit 2

### Negative
- Tradeoff 1
- Tradeoff 2

### Neutral
- Side effect 1

## Alternatives Considered

### Option A: [Name]
Description and why rejected.

### Option B: [Name]
Description and why rejected.

## References

- Links to relevant docs, issues, or discussions
```

## Creating a New ADR

1. Copy the template above
2. Name the file `ADR-XXX-short-title.md`
3. Fill in all sections
4. Submit for review
5. Update the index above
