# Character Philosophy & Technical Architecture

This folder contains the foundational decisions for how Fantazy characters work—from creative philosophy to technical implementation.

## Documents

1. **[PHILOSOPHY.md](./PHILOSOPHY.md)** - Overarching creative philosophy and emotional design principles
2. **[LLM_STRATEGY.md](./LLM_STRATEGY.md)** - LLM provider analysis, selection criteria, and implementation approach
3. **[VISUAL_STRATEGY.md](./VISUAL_STRATEGY.md)** - Image generation strategy, interaction modes, and cost considerations
4. **[CHARACTER_TEMPLATE.md](./CHARACTER_TEMPLATE.md)** - Template for creating new characters (system prompts, personality, boundaries)

## Development Approach

We're taking a **depth-first** approach:
- One character, fully realized, under scalable architecture
- Iterate on feel/stickiness before expanding
- Each decision should scale to N characters without rework

## Open Questions (Living List)

- [ ] LLM provider selection (see LLM_STRATEGY.md)
- [ ] Image generation approach and trigger points
- [ ] Memory retrieval strategy (semantic vs recency vs importance)
- [ ] Relationship progression mechanics
- [ ] Notification/hook delivery strategy
