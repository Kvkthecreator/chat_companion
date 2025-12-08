# YARNNN_GRAPH_CANON.md
Version: 1.0
Status: Canon — Graph Vocabulary & Rules

## Purpose
Define the **thread-first** substrate vocabulary and graph semantics Yarnnn uses to relate memory atoms across the basket scope.

---

## context_item.kind (closed set)
- `entity` — org/person/product/place; normalized by canonical name
- `topic` — theme/category; normalized taxonomy label
- `intent` — expressed goal/aim; active/passive
- `source_ref` — URL/file handle/ref
- `cue` — salient phrase, quote, or question seed
- `task` — light actionable memory (not a task manager)

**Required fields:** `kind`, `label`, `normalized_label`, `origin_ref`, `confidence`, `meta`  
**Normalization:** lowercase, strip punctuation/stopwords; custom merge table for aliases.

---

## Relationship Semantics

### rel_type (closed set, directional unless noted)
- `mentions` — src mentions dst (dump→entity, block→entity)
- `about` — src is about dst (doc→entity/topic)
- `supports` — src supports/strengthens dst (block→doc, block→block)
- `contrasts` — src opposes/counters dst (block→block)
- `derived_from` — src interpretation derived from dst capture (block→dump)
- `links_to` — src references dst (source_ref links)
- `duplicates` — symmetric; equivalence hint

**Uniqueness:** `(src_type, src_id, rel_type, dst_type, dst_id)` composite unique.  
**Direction:** `duplicates` is symmetric; others are directional.

---

## Projection Patterns (read)

### Windowing (basket-scoped)
- Default window: last N dumps or last T days
- Include context_items across window; include edges touching included nodes

### Example query goals
- "Entities most mentioned in the last 7 days"
- "Topics with rising mentions (week-over-week)"
- "Blocks with ≥ K supports relationships"
- "Dump clusters by shared entities/topics"

---

## Acceptance
`rg -n "context_item.kind|rel_type|composite unique|Projection Patterns" docs/YARNNN_GRAPH_CANON.md`

---

## Commit
docs: add YARNNN_GRAPH_CANON with context_item taxonomy, rel_type, and projection patterns