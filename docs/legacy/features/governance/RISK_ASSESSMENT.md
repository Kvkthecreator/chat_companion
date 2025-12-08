# Risk Assessment

**Multi-Factor Risk Calculation for Work Artifacts**

**Version**: 4.0
**Date**: 2025-10-31
**Status**: ✅ Canonical
**Layer**: 3 (Unified Governance)
**Category**: Feature Specification

---

## 🎯 Overview

Risk assessment calculates the risk level (low/medium/high) for each work artifact using multiple factors. Risk informs review prioritization and auto-approval eligibility.

**Key Concepts**:
- Risk is calculated per artifact, not per session
- Multiple factors contribute to final risk
- Base risk from artifact type + modifiers from context
- Risk guides user attention, not binary gates

---

## 📊 Risk Levels

```typescript
type RiskLevel = 'low' | 'medium' | 'high'

interface RiskCalculation {
  finalRisk: RiskLevel
  baseRisk: RiskLevel
  modifiers: RiskModifier[]
  reasoning: string
}

interface RiskModifier {
  factor: string              // confidence | context_impact | track_record | novelty
  direction: 'increase' | 'decrease' | 'none'
  magnitude: number           // 0-2
  reason: string
}
```

---

## 🧮 Risk Calculation Algorithm

### Overall Formula

```
Final Risk = Base Risk + Sum(Modifiers)

Where:
- Base Risk determined by artifact type
- Modifiers can increase/decrease risk
- Final risk clamped to [low, medium, high]
```

### Numeric Scale

```typescript
const RISK_SCALE = {
  low: 1,
  medium: 2,
  high: 3
}

// Apply modifiers
let riskValue = RISK_SCALE[baseRisk]

for (modifier of modifiers) {
  if (modifier.direction === 'increase') {
    riskValue += modifier.magnitude
  } else if (modifier.direction === 'decrease') {
    riskValue -= modifier.magnitude
  }
}

// Clamp to valid range
riskValue = Math.max(1, Math.min(3, riskValue))

// Convert back to level
finalRisk = {1: 'low', 2: 'medium', 3: 'high'}[riskValue]
```

---

## 1️⃣ Factor 1: Base Risk (Mutation Type)

**Purpose**: Different artifact types have inherently different risk profiles.

### Risk by Artifact Type

```python
def get_mutation_type_risk(artifact_type: str) -> RiskLevel:
    """
    Base risk from artifact type
    """

    risk_map = {
        # Adding new knowledge
        'block_proposal': 'medium',

        # Replacing existing knowledge (high stakes)
        'block_update_proposal': 'high',
        'block_lock_proposal': 'high',

        # Composition (no new facts)
        'document_creation': 'low',
        'document_update': 'low',

        # No substrate impact
        'insight': 'low',
        'external_deliverable': 'low',

        # Graph modifications
        'relationship_proposal': 'medium',
        'entity_extraction': 'low'
    }

    return risk_map.get(artifact_type, 'medium')
```

### Rationale

| Artifact Type | Base Risk | Rationale |
|--------------|-----------|-----------|
| **block_proposal** | Medium | Adding new knowledge - could be wrong, but reversible |
| **block_update_proposal** | High | Replacing existing knowledge - may lose important data |
| **block_lock_proposal** | High | Restricting future changes - hard to undo |
| **document_creation** | Low | Composition only, references existing blocks |
| **insight** | Low | No substrate impact, informational only |
| **relationship_proposal** | Medium | Affects knowledge graph structure |

---

## 2️⃣ Factor 2: Agent Confidence

**Purpose**: Agent's self-reported confidence correlates with correctness.

### Confidence Modifier

```python
def calculate_confidence_modifier(
    confidence: Optional[float]
) -> RiskModifier:
    """
    High confidence → Lower risk
    Low confidence → Higher risk
    """

    if confidence is None:
        return RiskModifier(
            factor='confidence',
            direction='none',
            magnitude=0,
            reason='No confidence score provided'
        )

    if confidence > 0.9:
        # Very confident → Reduce risk
        return RiskModifier(
            factor='confidence',
            direction='decrease',
            magnitude=1,
            reason=f'High confidence ({confidence:.2f})'
        )

    elif confidence < 0.7:
        # Not confident → Increase risk
        return RiskModifier(
            factor='confidence',
            direction='increase',
            magnitude=1,
            reason=f'Low confidence ({confidence:.2f})'
        )

    else:
        # Medium confidence → No change
        return RiskModifier(
            factor='confidence',
            direction='none',
            magnitude=0,
            reason=f'Medium confidence ({confidence:.2f})'
        )
```

### Confidence Calibration

Track agent's claimed confidence vs. actual approval rate:

```python
async def calculate_confidence_calibration_error(
    agent_id: str
) -> float:
    """
    How well does agent's confidence predict approval?

    Perfect calibration: claimed 0.9 → 90% approval rate
    Over-confident: claimed 0.9 → 70% approval rate (error: 0.2)
    Under-confident: claimed 0.9 → 95% approval rate (error: -0.05)
    """

    metrics = await get_agent_performance(agent_id)

    return abs(
        metrics.avgClaimedConfidence - metrics.avgActualApprovalRate
    )
```

**Future Enhancement**: Adjust confidence modifier based on calibration error.

---

## 3️⃣ Factor 3: Context Impact

**Purpose**: More related blocks affected → Higher risk.

### Context Impact Modifier

```python
async def calculate_context_impact_modifier(
    artifact: WorkArtifact,
    session: WorkSession
) -> RiskModifier:
    """
    Measure how many related blocks would be affected
    """

    # Semantic search for related blocks
    if artifact.artifact_type == 'block_proposal':
        query = artifact.content['block_content']['text']
    elif artifact.artifact_type == 'block_update_proposal':
        query = artifact.content['new_content']['text']
    else:
        return RiskModifier(
            factor='context_impact',
            direction='none',
            magnitude=0,
            reason='Not applicable for this artifact type'
        )

    # Find semantically related blocks
    related_blocks = await semantic_search(
        workspace_id=session.workspace_id,
        basket_id=session.basket_id,
        query_text=query,
        min_similarity=0.7,
        limit=20
    )

    count = len(related_blocks)

    if count <= 2:
        return RiskModifier(
            factor='context_impact',
            direction='none',
            magnitude=0,
            reason=f'Low context impact ({count} related blocks)'
        )

    elif count <= 5:
        return RiskModifier(
            factor='context_impact',
            direction='increase',
            magnitude=1,
            reason=f'Medium context impact ({count} related blocks)'
        )

    else:
        return RiskModifier(
            factor='context_impact',
            direction='increase',
            magnitude=2,
            reason=f'High context impact ({count} related blocks)'
        )
```

### Rationale

- **Low impact (≤2 blocks)**: Isolated knowledge, low ripple effect
- **Medium impact (3-5 blocks)**: Moderate integration, careful review needed
- **High impact (>5 blocks)**: Central to knowledge graph, scrutinize carefully

---

## 4️⃣ Factor 4: Agent Track Record

**Purpose**: Proven agents earn trust, reducing risk.

### Track Record Modifier

```python
async def calculate_track_record_modifier(
    agent_id: Optional[str]
) -> RiskModifier:
    """
    High approval rate → Lower risk (trust earned)
    Low approval rate → Higher risk (needs scrutiny)
    """

    if not agent_id:
        return RiskModifier(
            factor='track_record',
            direction='none',
            magnitude=0,
            reason='No agent tracking'
        )

    # Fetch agent performance metrics
    metrics = await get_agent_performance(agent_id)

    # Require minimum sample size
    if metrics.totalSessions < 10:
        return RiskModifier(
            factor='track_record',
            direction='none',
            magnitude=0,
            reason=f'Insufficient history ({metrics.totalSessions} sessions)'
        )

    if metrics.approvalRate > 0.9:
        # Excellent track record → Reduce risk
        return RiskModifier(
            factor='track_record',
            direction='decrease',
            magnitude=1,
            reason=f'Excellent track record ({metrics.approvalRate:.0%} approval)'
        )

    elif metrics.approvalRate < 0.7:
        # Poor track record → Increase risk
        return RiskModifier(
            factor='track_record',
            direction='increase',
            magnitude=1,
            reason=f'Poor track record ({metrics.approvalRate:.0%} approval)'
        )

    else:
        # Average track record → No change
        return RiskModifier(
            factor='track_record',
            direction='none',
            magnitude=0,
            reason=f'Average track record ({metrics.approvalRate:.0%} approval)'
        )
```

### Track Record Metrics

```typescript
interface AgentPerformanceMetrics {
  agentId: string
  totalSessions: number
  approvalRate: number              // sessionsApproved / totalSessions
  artifactApprovalRate: number
  avgIterations: number
  confidenceCalibrationError: number
}
```

---

## 5️⃣ Factor 5: Novelty Detection

**Purpose**: Novel/contradictory content requires more scrutiny than confirmatory content.

### Novelty Modifier

```python
async def calculate_novelty_modifier(
    artifact: WorkArtifact,
    session: WorkSession
) -> RiskModifier:
    """
    Confirms existing knowledge → Lower risk
    Introduces new entities/topics → Higher risk
    Contradicts existing knowledge → Much higher risk
    """

    # Extract content for comparison
    if artifact.artifact_type == 'block_proposal':
        content = artifact.content['block_content']['text']
    elif artifact.artifact_type == 'block_update_proposal':
        content = artifact.content['new_content']['text']
    else:
        return RiskModifier(
            factor='novelty',
            direction='none',
            magnitude=0,
            reason='Not applicable for this artifact type'
        )

    # Semantic similarity check against existing blocks
    existing_blocks = await semantic_search(
        workspace_id=session.workspace_id,
        basket_id=session.basket_id,
        query_text=content,
        min_similarity=0.6,
        limit=10
    )

    if not existing_blocks:
        # Completely new topic
        return RiskModifier(
            factor='novelty',
            direction='increase',
            magnitude=1,
            reason='Introduces new topic (no related blocks found)'
        )

    # Analyze similarity distribution
    similarity_scores = [b.similarity for b in existing_blocks]
    max_similarity = max(similarity_scores)

    if max_similarity > 0.9:
        # Highly similar → Confirms existing knowledge
        return RiskModifier(
            factor='novelty',
            direction='none',
            magnitude=0,
            reason='Confirms existing knowledge (high similarity)'
        )

    elif max_similarity > 0.7:
        # Moderate similarity → Related but novel
        return RiskModifier(
            factor='novelty',
            direction='increase',
            magnitude=1,
            reason='Extends existing knowledge (moderate similarity)'
        )

    else:
        # Low similarity → Potentially contradictory or novel angle
        contradiction_detected = await detect_contradiction(
            content, existing_blocks
        )

        if contradiction_detected:
            return RiskModifier(
                factor='novelty',
                direction='increase',
                magnitude=2,
                reason='Potentially contradicts existing knowledge'
            )
        else:
            return RiskModifier(
                factor='novelty',
                direction='increase',
                magnitude=1,
                reason='Novel perspective on existing topic'
            )
```

### Contradiction Detection

```python
async def detect_contradiction(
    new_content: str,
    existing_blocks: List[Block]
) -> bool:
    """
    Use LLM to detect semantic contradiction
    """

    prompt = f"""
    New content: {new_content}

    Existing knowledge:
    {chr(10).join([b.content['text'] for b in existing_blocks[:3]])}

    Does the new content contradict or conflict with existing knowledge?
    Answer: yes/no with reasoning.
    """

    response = await llm.complete(prompt)

    # Parse response
    return response.lower().startswith('yes')
```

---

## 🎯 Complete Risk Assessment

### Main Function

```python
class RiskAssessmentEngine:
    async def assess_artifact_risk(
        self,
        artifact: WorkArtifact,
        session: WorkSession
    ) -> RiskCalculation:
        """
        Calculate final risk using all factors
        """

        # Factor 1: Base risk
        base_risk = self._get_mutation_type_risk(artifact.artifact_type)

        # Factor 2: Confidence
        confidence_modifier = self._calculate_confidence_modifier(
            artifact.agent_confidence
        )

        # Factor 3: Context impact
        context_modifier = await self._calculate_context_impact_modifier(
            artifact, session
        )

        # Factor 4: Track record
        track_record_modifier = await self._calculate_track_record_modifier(
            session.executed_by_agent_id
        )

        # Factor 5: Novelty
        novelty_modifier = await self._calculate_novelty_modifier(
            artifact, session
        )

        # Apply all modifiers
        modifiers = [
            confidence_modifier,
            context_modifier,
            track_record_modifier,
            novelty_modifier
        ]

        final_risk = self._apply_risk_modifiers(base_risk, modifiers)

        return RiskCalculation(
            finalRisk=final_risk,
            baseRisk=base_risk,
            modifiers=modifiers,
            reasoning=self._generate_risk_reasoning(
                base_risk, final_risk, modifiers
            )
        )

    def _apply_risk_modifiers(
        self,
        base_risk: RiskLevel,
        modifiers: List[RiskModifier]
    ) -> RiskLevel:
        """
        Apply modifiers to base risk
        """

        # Convert to numeric
        risk_value = {'low': 1, 'medium': 2, 'high': 3}[base_risk]

        # Apply each modifier
        for modifier in modifiers:
            if modifier.direction == 'increase':
                risk_value += modifier.magnitude
            elif modifier.direction == 'decrease':
                risk_value -= modifier.magnitude

        # Clamp to valid range [1, 3]
        risk_value = max(1, min(3, risk_value))

        # Convert back
        return {1: 'low', 2: 'medium', 3: 'high'}[risk_value]

    def _generate_risk_reasoning(
        self,
        base_risk: RiskLevel,
        final_risk: RiskLevel,
        modifiers: List[RiskModifier]
    ) -> str:
        """
        Generate human-readable risk explanation
        """

        reasoning_parts = [
            f"Base risk: {base_risk} (artifact type)"
        ]

        for modifier in modifiers:
            if modifier.direction != 'none':
                reasoning_parts.append(
                    f"{modifier.factor}: {modifier.reason}"
                )

        reasoning_parts.append(f"Final risk: {final_risk}")

        return "\n".join(reasoning_parts)
```

---

## 📈 Risk Examples

### Example 1: Low Risk Artifact

```python
# Artifact: Insight (no substrate impact)
artifact = WorkArtifact(
    artifact_type='insight',
    content={'insight_type': 'observation', ...},
    agent_confidence=0.88
)

# Risk calculation
risk = await assess_artifact_risk(artifact, session)

# Result:
RiskCalculation(
    finalRisk='low',
    baseRisk='low',  # Insight type
    modifiers=[
        RiskModifier('confidence', 'none', 0, 'Medium confidence (0.88)'),
        RiskModifier('context_impact', 'none', 0, 'Not applicable'),
        RiskModifier('track_record', 'decrease', 1, 'Excellent track record (92% approval)'),
        RiskModifier('novelty', 'none', 0, 'Not applicable')
    ],
    reasoning="Base risk: low (artifact type)\ntrack_record: Excellent track record (92% approval)\nFinal risk: low"
)
```

### Example 2: High Risk Artifact

```python
# Artifact: Block update (contradicts existing)
artifact = WorkArtifact(
    artifact_type='block_update_proposal',
    content={
        'supersedes_block_id': 'block-123',
        'new_content': {'text': 'Competitor pricing actually increased...'}
    },
    agent_confidence=0.75
)

# Risk calculation
risk = await assess_artifact_risk(artifact, session)

# Result:
RiskCalculation(
    finalRisk='high',
    baseRisk='high',  # Update proposal
    modifiers=[
        RiskModifier('confidence', 'none', 0, 'Medium confidence (0.75)'),
        RiskModifier('context_impact', 'increase', 1, 'Medium context impact (4 related blocks)'),
        RiskModifier('track_record', 'none', 0, 'Average track record (82% approval)'),
        RiskModifier('novelty', 'increase', 2, 'Potentially contradicts existing knowledge')
    ],
    reasoning="Base risk: high (artifact type)\ncontext_impact: Medium context impact (4 related blocks)\nnovelty: Potentially contradicts existing knowledge\nFinal risk: high"
)
```

---

## 🎯 Risk-Based Actions

### Auto-Approval Eligibility

```python
# Only low-risk artifacts eligible for auto-approval
if risk.finalRisk == 'low' and agent_track_record.approvalRate > 0.9:
    eligible_for_auto_approval = True
```

### Review Prioritization

```python
# High-risk artifacts shown first in review UI
artifacts_sorted = sorted(
    artifacts,
    key=lambda a: {'high': 3, 'medium': 2, 'low': 1}[a.risk_level],
    reverse=True
)
```

### Risk-Based Notifications

```python
# High-risk artifacts trigger immediate notifications
if risk.finalRisk == 'high':
    await notify_high_risk_artifact_created(artifact, risk)
```

---

## 📊 Risk Distribution Metrics

```typescript
interface RiskDistributionMetrics {
  workspace_id: UUID
  time_range: string

  // Distribution
  lowRiskArtifacts: number
  mediumRiskArtifacts: number
  highRiskArtifacts: number

  // Outcomes by risk level
  approvalRateByRisk: Record<RiskLevel, number>

  // Accuracy
  highRiskRevertRate: number      // % of high-risk approved work later reverted
  lowRiskRevertRate: number       // Should be very low
}
```

---

## 📎 See Also

- [ARTIFACT_TYPES_AND_HANDLING.md](../work-management/ARTIFACT_TYPES_AND_HANDLING.md) - Artifact types
- [WORKSPACE_POLICIES.md](./WORKSPACE_POLICIES.md) - Auto-approval rules
- [APPROVAL_WORKFLOWS.md](./APPROVAL_WORKFLOWS.md) - Review flows
- [YARNNN_UNIFIED_GOVERNANCE.md](../../architecture/YARNNN_UNIFIED_GOVERNANCE.md) - Governance layer

---

**5 factors. Base risk + 4 modifiers. Low/medium/high. Risk guides attention, not binary gates.**
