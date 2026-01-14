# Episode 0 Activation Fix Timeline

> **Status**: Fixed as of Jan 14, 2026
> **Summary**: Two separate fixes were needed, not one

---

## Jan 12, 2026 - Partial Fix (Commit 627d4734)

### What Was Fixed:
1. ✅ **Opening messages displayed as chat bubbles** (removed static EpisodeOpeningCard)
2. ✅ **Added starter prompts to database** (10 Episode 0s got 3 prompts each)
3. ✅ **Extended short opening lines** (from 75-165 chars to 500-800 chars)

### What Was Claimed:
- "All 3 critical UX gaps fixed"
- "Expected: Activation rate 0% → 30-50% within 48 hours"

### What Actually Happened:
- Opening messages worked ✅
- **Starter prompts did NOT show** ❌
- Activation remained low (0-25%)

---

## Jan 14, 2026 - Complete Fix (Commit 84d3a268)

### Root Cause Discovered:
Starter prompts were rendered in `<EmptyState>` component, which only shows when `chatItems.length === 0`. But backend auto-injects opening message, so `chatItems.length === 1`, causing EmptyState to never render.

### The Actual Fix:
Added conditional rendering to show starter prompts **below opening message** when:
- Messages exist (chat not empty)
- User hasn't sent any messages yet
- Episode template has starter_prompts

### Database Verification (Jan 14):
```sql
-- All Episode 0s have 3 prompts
SELECT s.slug, array_length(et.starter_prompts, 1)
FROM episode_templates et
JOIN series s ON s.id = et.series_id
WHERE et.episode_number = 0;

-- Result: 3 prompts each for death-flag-deleted, seventeen-days, villainess-survives
```

---

## What Users See Now (After Both Fixes):

```
┌─────────────────────────────────────┐
│  [Opening Message - 992 chars]      │
│  *Detective Yoon doesn't look up..* │
│  "Close the door."                  │
│                                     │
│  Try one of these openers:          │
│  ┌──────────────────────────────┐   │
│  │ "I'm sorry for your loss"    │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │ "I'd like to help more"      │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │ "What did her friends say?"  │   │
│  └──────────────────────────────┘   │
│                                     │
│ [Input field]                       │
└─────────────────────────────────────┘
```

---

## Expected Impact:

**Jan 12 fix alone:** Minimal (prompts didn't show)
**Jan 14 complete fix:** Activation rate should increase to 40-60%

---

## Lessons Learned:

1. **Verify fixes in production**, not just code review
2. **Test the actual user flow**, not just database state
3. **Backend working ≠ Frontend working**
4. **EmptyState logic was a hidden footgun**

---

## Files Changed:

**Jan 12:**
- `web/src/components/chat/ChatContainer.tsx` - Removed EpisodeOpeningCard
- `scripts/add_starter_prompts.sql` - Added prompts to DB
- `scripts/extend_opening_lines.sql` - Extended opening lines

**Jan 14:**
- `web/src/components/chat/ChatContainer.tsx` - Added prompts after messages

---

## Related Metrics:

**Before fixes:**
- Reddit campaigns: 3 signups, 0 activated (oi-deathflag-v2)
- Reddit campaigns: 1 signup, 1 activated (manhwa-regressor-v2)
- Overall: 4 paid users, 1 engaged (25%)

**After complete fix (pending data):**
- Expected: 40-60% activation
- Will track in admin dashboard

---

**Status:** Both fixes deployed. Monitoring activation metrics.
