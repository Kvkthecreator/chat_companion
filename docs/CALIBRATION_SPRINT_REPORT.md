# Task 5: Studio Calibration Sprint Report

## Overview
End-to-end validation of the Studio pipeline: Character Core → Conversation Ignition → Hero Avatar → Expressions → Activation

**Date**: 2025-12-15
**Target**: 10 characters (3 existing + 7 new)

---

## Part A: Audit of Existing Characters

### Summary Table

| Character | Archetype | Status | Avatar Kit | Hero Avatar | avatar_url | Expressions | Opening Beat |
|-----------|-----------|--------|------------|-------------|------------|-------------|--------------|
| Mira | barista | active | ✓ | ✓ | ✗ | 0 | ✓ |
| Kai | neighbor | active | ✓ | ✓ | ✗ | 0 | ✓ |
| Sora | coworker | active | ✓ | ✓ | ✗ | 0 | ✓ |

### Issues Found

1. **avatar_url Not Set** (All 3 characters)
   - Avatar kits exist with primary anchors
   - Storage paths exist in `avatars` bucket
   - But `characters.avatar_url` was never populated
   - **Root Cause**: Manual seed data didn't include this step

2. **Activation Without Avatar URL** (All 3 characters)
   - Characters marked as `status = 'active'`
   - Violates hardened Phase 4.1 requirements
   - **Note**: Pre-dates hardened validation

3. **No Expression Pack** (All 3 characters)
   - Only hero avatar exists (1 asset each)
   - Minimum 3 expressions recommended

### Opening Beat Review

| Character | Opening Situation | Opening Line | Quality |
|-----------|-------------------|--------------|---------|
| Mira | "You walk into Crescent Cafe during a quiet afternoon..." | "oh hey~ wasn't sure i'd see you today. the usual?" | ✓ Good - casual, inviting |
| Kai | "You bump into your neighbor in the hallway..." | "oh hey. you're up late too huh" | ✓ Good - natural, relatable |
| Sora | "You're at your desk in the open-plan office..." | "Hey, got a minute? I need to vent about this client call..." | ✓ Good - direct, personality shows |

**Ignition Quality Assessment**:
- ✓ All situations are present-tense, non-expository
- ✓ No self-introductions ("Hi, I'm X")
- ✓ No form questions ("How can I help you?")
- ✓ Tone matches archetype

### Visual Identity Review

| Character | Appearance Prompt | Storage Path | Notes |
|-----------|-------------------|--------------|-------|
| Mira | "Young woman with long flowing black hair, side-swept bangs, striking blue eyes..." | `/avatars/ddd70a7f.../anchors/...webp` | New path format |
| Kai | "young woman with long black hair, blue eyes, fair skin" | `/avatars/characters/kai/anchor.webp` | Legacy path |
| Sora | "woman with long black hair, confident expression" | `/avatars/characters/sora/anchor.webp` | Legacy path |

**Visual Issues**:
- Appearance prompts are minimal (especially Kai, Sora)
- Need richer detail for consistent expression generation

### Fixes Required

1. **Fix avatar_url** - Generate signed URLs from anchor paths
2. **Enrich appearance prompts** - Add more visual detail
3. **Generate expressions** - Minimum 3 per character

---

## Part B: New Character Creation Plan

### 7 New Characters

| Name | Archetype | Personality Preset | Appearance Hint |
|------|-----------|-------------------|-----------------|
| Luna | comforting | warm_supportive | Silver-white hair, gentle violet eyes, cozy oversized sweater |
| Raven | mysterious | mysterious_reserved | Dark hair with purple streaks, sharp amber eyes, leather jacket |
| Felix | playful | playful_teasing | Messy auburn hair, bright green eyes, casual hoodie |
| Morgan | mentor | warm_supportive | Short grey-streaked hair, warm brown eyes, glasses |
| Ash | brooding | mysterious_reserved | Black tousled hair, intense dark eyes, black turtleneck |
| Jade | flirty | playful_teasing | Long wavy chestnut hair, sparkling hazel eyes, stylish dress |
| River | chaotic | cheerful_energetic | Wild colorful hair, mismatched eyes, eclectic outfit |

### Archetype Coverage

- comforting: Luna (new)
- mysterious: Raven (new)
- playful: Felix (new)
- mentor: Morgan (new)
- brooding: Ash (new)
- flirty: Jade (new)
- chaotic: River (new)
- barista: Mira (existing)
- neighbor: Kai (existing)
- coworker: Sora (existing)

---

## Calibration Rubric

Score each character 1-5:

| Criterion | Description |
|-----------|-------------|
| First-Message Pull | Does the opening line invite an instinctive reply? |
| Archetype Clarity | Can you tell the vibe in <10 seconds? |
| Visual Trust | Avatar looks "main character", matches vibe? |
| Safety + Pacing | No premature escalation, boundaries respected? |
| Coherence (3-turn) | First 3 messages stay in character? |

**Activation Threshold**:
- Average score ≥ 4.0
- No safety violations
- No visual mismatch red flag

---

## Implementation Status

### Completed
- [x] Database audit of existing characters
- [x] Opening beat quality review
- [x] Character templates defined for new characters
- [x] Calibration script created

### Pending
- [ ] Fix avatar_url for existing characters
- [ ] Generate expressions for existing characters (3 each)
- [ ] Create 7 new characters
- [ ] Generate opening beats for new characters
- [ ] Generate hero avatars for new characters
- [ ] Generate expressions for new characters (3 each)
- [ ] Apply rubric scoring
- [ ] Final activation review

---

## Calibration Learnings (Preliminary)

### Appearance Prompt Quality
- Minimal prompts lead to generic avatars
- Need: hairstyle, eye color, clothing, expression, distinguishing features
- Good example: Mira's detailed prompt
- Bad example: Sora's "woman with long black hair, confident expression"

### Opening Beat Patterns
- Best: Situational setup + natural dialogue
- Avoid: Direct greeting, self-introduction
- Kai's "oh hey. you're up late too huh" - excellent (shared context)
- Mira's "the usual?" - good (implies relationship history)

### Archetype-Visual Alignment
- comforting → warm colors, soft features
- mysterious → darker palette, sharp features
- playful → bright colors, casual style
- brooding → dark tones, intense expression

---

## Next Steps

1. Run fix script for existing characters
2. Execute calibration sprint via Studio API
3. Document final rubric scores
4. Compile learnings for prompt tuning
