# Domain Layer Implementation Plan

> **Status**: Draft
> **Created**: 2026-01-26
> **Purpose**: Implementation roadmap for transition-focused domain layer

---

## Executive Summary

This document outlines the implementation plan for transforming Chat Companion from a generic AI companion into a **transition-focused follow-up system**. The changes span three areas:

1. **Domain Layer** — Thread templates, classification, and priority weighting
2. **Onboarding Redesign** — Domain-first flow with immediate value delivery
3. **Frontend Surfacing** — Thread visibility in chat and memory pages

**Estimated Total Scope**: 3-4 weeks of focused development

---

## Design Decisions (Locked)

These decisions emerged from strategic analysis and are now fixed:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ICP | People in transition | High-power threads cluster around life changes |
| Template approach | Backend scaffolding, not user-facing constraints | Templates inform system, don't restrict user |
| Domain selection | Soft priority (C) | Context without rigidity |
| Multiple threads | Normal case (2-5 typical) | People in transition have overlapping situations |
| Thread display | Priority-ranked, top 3 visible | Manages cognitive load |
| Immediate value | Yes — Day 0 acknowledgment | Solves cold start problem |

---

## Part 1: Thread Templates & Domain Layer

### 1.1 Template Schema

```sql
-- New table: thread_templates
CREATE TABLE thread_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Classification
    domain TEXT NOT NULL,           -- "career", "location", "relationships", "health", "creative", "life_stage", "personal"
    template_key TEXT NOT NULL,     -- "job_search", "new_city", "breakup", etc.
    display_name TEXT NOT NULL,     -- "Job Search", "Moving to a New City"

    -- For LLM classification
    trigger_phrases TEXT[],         -- ["job", "interview", "career", "hired", "fired", "resume"]
    description TEXT,               -- Helps LLM understand when to apply

    -- Phases (optional — not all transitions have clear phases)
    has_phases BOOLEAN DEFAULT FALSE,
    phases JSONB,                   -- ["exploring", "applying", "interviewing", "waiting", "decided"]

    -- Follow-up configuration
    follow_up_prompts JSONB NOT NULL,
    -- {
    --   "initial": "Tell me more about the job search",
    --   "check_in": "How's the job search going?",
    --   "phase_specific": { "waiting": "Did you hear back?" }
    -- }

    typical_duration TEXT,          -- "days", "weeks", "months" — informs follow-up timing
    default_follow_up_days INTEGER DEFAULT 3,

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for classification
CREATE INDEX idx_templates_domain ON thread_templates(domain);
CREATE UNIQUE INDEX idx_templates_key ON thread_templates(template_key);
```

### 1.2 Thread Table Updates

```sql
-- Add domain layer fields to life_threads
ALTER TABLE life_threads ADD COLUMN domain TEXT;
ALTER TABLE life_threads ADD COLUMN template_id UUID REFERENCES thread_templates(id);
ALTER TABLE life_threads ADD COLUMN phase TEXT;
ALTER TABLE life_threads ADD COLUMN priority_weight NUMERIC(3,2) DEFAULT 1.0;

-- Index for priority queries
CREATE INDEX idx_threads_priority ON life_threads(user_id, priority_weight DESC, updated_at DESC);
```

### 1.3 User Domain Preferences

```sql
-- Add to users table (or users.preferences JSONB)
ALTER TABLE users ADD COLUMN domain_preferences JSONB DEFAULT '{}';
-- Structure:
-- {
--   "primary_domains": ["career", "location"],
--   "domain_weights": { "career": 1.5, "location": 1.2 },
--   "onboarding_selections": ["job_search", "new_city"]
-- }
```

### 1.4 Seed Templates

```typescript
const SEED_TEMPLATES = [
  // CAREER DOMAIN
  {
    domain: "career",
    template_key: "job_search",
    display_name: "Looking for a job",
    trigger_phrases: ["job search", "looking for work", "applying", "interview", "resume", "hired", "job hunt"],
    has_phases: true,
    phases: ["exploring", "applying", "interviewing", "waiting", "decided"],
    follow_up_prompts: {
      initial: "Tell me about the job search — what kind of role are you looking for?",
      check_in: "How's the job search going?",
      phase_specific: {
        applying: "How are the applications going?",
        interviewing: "How did the interview go?",
        waiting: "Did you hear back yet?"
      }
    },
    typical_duration: "weeks_to_months",
    default_follow_up_days: 3
  },
  {
    domain: "career",
    template_key: "new_job",
    display_name: "Starting a new job",
    trigger_phrases: ["new job", "started work", "first day", "new role", "onboarding"],
    has_phases: true,
    phases: ["preparing", "first_week", "settling_in", "established"],
    follow_up_prompts: {
      initial: "Congrats on the new role! How are you feeling about it?",
      check_in: "How's the new job going?",
      phase_specific: {
        first_week: "How was your first week?",
        settling_in: "Starting to feel more settled?"
      }
    },
    typical_duration: "months",
    default_follow_up_days: 7
  },
  {
    domain: "career",
    template_key: "leaving_job",
    display_name: "Leaving a job",
    trigger_phrases: ["quitting", "leaving job", "last day", "giving notice", "laid off", "fired"],
    follow_up_prompts: {
      initial: "That's a big change. How are you feeling about leaving?",
      check_in: "How are you doing with the job transition?"
    },
    typical_duration: "weeks",
    default_follow_up_days: 3
  },

  // LOCATION DOMAIN
  {
    domain: "location",
    template_key: "moving",
    display_name: "Moving to a new place",
    trigger_phrases: ["moving", "relocating", "new apartment", "new city", "packing"],
    has_phases: true,
    phases: ["planning", "packing", "moving_day", "unpacking", "settling"],
    follow_up_prompts: {
      initial: "Where are you moving to? What's prompting the move?",
      check_in: "How's the move going?",
      phase_specific: {
        moving_day: "How did moving day go?",
        settling: "Starting to feel at home?"
      }
    },
    typical_duration: "weeks_to_months",
    default_follow_up_days: 5
  },
  {
    domain: "location",
    template_key: "new_city",
    display_name: "Settling into a new city",
    trigger_phrases: ["new city", "just moved", "don't know anyone", "finding my way", "exploring"],
    has_phases: true,
    phases: ["arrival", "exploring", "building_routine", "feeling_home"],
    follow_up_prompts: {
      initial: "What brought you to the new city? How long have you been there?",
      check_in: "How are you finding the new city?",
      phase_specific: {
        exploring: "Discovered any good spots yet?",
        building_routine: "Starting to build a routine?"
      }
    },
    typical_duration: "months",
    default_follow_up_days: 7
  },

  // RELATIONSHIPS DOMAIN
  {
    domain: "relationships",
    template_key: "breakup",
    display_name: "Going through a breakup",
    trigger_phrases: ["breakup", "broke up", "ended relationship", "ex", "single again"],
    follow_up_prompts: {
      initial: "I'm sorry to hear that. How are you holding up?",
      check_in: "How are you doing with everything?"
    },
    typical_duration: "weeks_to_months",
    default_follow_up_days: 3
  },
  {
    domain: "relationships",
    template_key: "new_relationship",
    display_name: "Starting a new relationship",
    trigger_phrases: ["dating", "new relationship", "met someone", "seeing someone"],
    follow_up_prompts: {
      initial: "That's exciting! How did you meet?",
      check_in: "How are things going with them?"
    },
    typical_duration: "months",
    default_follow_up_days: 7
  },
  {
    domain: "relationships",
    template_key: "relationship_tension",
    display_name: "Working through relationship issues",
    trigger_phrases: ["fighting", "argument", "tension", "not getting along", "relationship problems"],
    follow_up_prompts: {
      initial: "That sounds stressful. What's been going on?",
      check_in: "How are things between you two?"
    },
    typical_duration: "days_to_weeks",
    default_follow_up_days: 2
  },

  // HEALTH DOMAIN
  {
    domain: "health",
    template_key: "personal_health",
    display_name: "Dealing with a health situation",
    trigger_phrases: ["health issue", "diagnosis", "doctor", "treatment", "symptoms", "medical"],
    follow_up_prompts: {
      initial: "I hope you're okay. What's going on health-wise?",
      check_in: "How are you feeling?"
    },
    typical_duration: "varies",
    default_follow_up_days: 3
  },
  {
    domain: "health",
    template_key: "caregiver",
    display_name: "Caring for someone",
    trigger_phrases: ["taking care of", "caregiver", "mom's health", "dad's health", "family member sick"],
    follow_up_prompts: {
      initial: "That's a lot to carry. How is the person you're caring for doing?",
      check_in: "How are you holding up with everything?"
    },
    typical_duration: "months",
    default_follow_up_days: 5
  },
  {
    domain: "health",
    template_key: "lifestyle_change",
    display_name: "Making a lifestyle change",
    trigger_phrases: ["diet", "exercise", "quit smoking", "sobriety", "sleep", "habit"],
    has_phases: true,
    phases: ["starting", "first_week", "building_habit", "maintaining"],
    follow_up_prompts: {
      initial: "What motivated this change?",
      check_in: "How's the lifestyle change going?"
    },
    typical_duration: "weeks_to_months",
    default_follow_up_days: 3
  },

  // CREATIVE DOMAIN
  {
    domain: "creative",
    template_key: "launching",
    display_name: "Launching something",
    trigger_phrases: ["launching", "shipping", "release", "going live", "product launch"],
    has_phases: true,
    phases: ["preparing", "launch_day", "post_launch"],
    follow_up_prompts: {
      initial: "Exciting! What are you launching?",
      check_in: "How's the launch prep going?",
      phase_specific: {
        launch_day: "How did the launch go?",
        post_launch: "How's the reception been?"
      }
    },
    typical_duration: "weeks",
    default_follow_up_days: 2
  },
  {
    domain: "creative",
    template_key: "building",
    display_name: "Building a project",
    trigger_phrases: ["building", "working on", "side project", "creating", "making"],
    follow_up_prompts: {
      initial: "What are you building?",
      check_in: "How's the project coming along?"
    },
    typical_duration: "months",
    default_follow_up_days: 7
  },

  // LIFE STAGE DOMAIN
  {
    domain: "life_stage",
    template_key: "graduation",
    display_name: "Graduating / finishing school",
    trigger_phrases: ["graduating", "finished school", "degree", "diploma"],
    follow_up_prompts: {
      initial: "Congratulations! What's next for you?",
      check_in: "How are you feeling about the transition?"
    },
    typical_duration: "months",
    default_follow_up_days: 7
  },
  {
    domain: "life_stage",
    template_key: "parenthood",
    display_name: "Becoming a parent",
    trigger_phrases: ["pregnant", "expecting", "baby", "new parent", "newborn"],
    follow_up_prompts: {
      initial: "That's huge! How are you feeling about it?",
      check_in: "How's everything going with the little one?"
    },
    typical_duration: "months",
    default_follow_up_days: 7
  },

  // PERSONAL DOMAIN (catch-all for important but uncategorized)
  {
    domain: "personal",
    template_key: "grief",
    display_name: "Processing a loss",
    trigger_phrases: ["loss", "died", "passed away", "grieving", "funeral"],
    follow_up_prompts: {
      initial: "I'm so sorry for your loss. I'm here if you want to talk.",
      check_in: "How are you doing?"
    },
    typical_duration: "months",
    default_follow_up_days: 5
  },
  {
    domain: "personal",
    template_key: "finances",
    display_name: "Financial situation",
    trigger_phrases: ["money", "debt", "budget", "saving", "financial stress"],
    follow_up_prompts: {
      initial: "Money stuff can be stressful. What's going on?",
      check_in: "How's the financial situation?"
    },
    typical_duration: "months",
    default_follow_up_days: 7
  }
];
```

### 1.5 Classification Service

```python
# api/src/app/services/domain_classifier.py

class DomainClassifier:
    """Classifies user input into domains and templates."""

    async def classify_situation(
        self,
        user_input: str,
        templates: List[ThreadTemplate]
    ) -> ClassificationResult:
        """
        Classify free-text situation into domain and template.
        Returns best match or None if no confident match.
        """
        prompt = f"""
        Given the following situation a user described, classify it into one of these categories.

        User's situation: "{user_input}"

        Available templates:
        {self._format_templates(templates)}

        Return JSON:
        {{
            "template_key": "best_matching_template_key or null",
            "domain": "domain if matched, or 'personal' if unclear",
            "confidence": 0.0-1.0,
            "extracted_details": {{
                "summary": "one sentence summary",
                "key_entities": ["specific names, dates, places mentioned"],
                "phase_hint": "if applicable, which phase they seem to be in"
            }}
        }}

        If the situation doesn't clearly match any template, set template_key to null
        and domain to "personal". Still extract details.
        """

        response = await self.llm.generate(prompt)
        return ClassificationResult.parse(response)

    async def classify_from_conversation(
        self,
        messages: List[Message],
        existing_threads: List[Thread],
        templates: List[ThreadTemplate]
    ) -> List[ThreadUpdate]:
        """
        Extract and classify threads from conversation.
        Updates existing threads or creates new ones.
        """
        # Implementation for ongoing extraction
        pass
```

---

## Part 2: Onboarding Redesign

### 2.1 New Onboarding Flow

The key insight: **Domain selection comes first and frames everything else.**

```
┌─────────────────────────────────────────────────────────────────┐
│                    ONBOARDING FLOW (REVISED)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STEP 1: WELCOME + PATH CHOICE                                  │
│  "Let's get to know each other."                                │
│  [Start with Chat] [Quick Setup]                                │
│                                                                  │
│  ───────────────────────────────────────────────────────────────│
│                                                                  │
│  STEP 2: PRIMARY TRANSITION (Domain First)                      │
│  "What's the main thing on your mind right now?"                │
│                                                                  │
│  [ ] Looking for a job                    [career]              │
│  [ ] Starting a new job                   [career]              │
│  [ ] Moving to a new place                [location]            │
│  [ ] Going through a breakup              [relationships]       │
│  [ ] Building or launching something      [creative]            │
│  [ ] Health situation                     [health]              │
│  [ ] Something else → [free text]         [personal]            │
│                                                                  │
│  ───────────────────────────────────────────────────────────────│
│                                                                  │
│  STEP 3: SITUATION DETAILS                                      │
│  "Tell me a bit more about [selection]"                         │
│  [Free text input — seeds the first thread]                     │
│                                                                  │
│  ───────────────────────────────────────────────────────────────│
│                                                                  │
│  STEP 4: SECONDARY TRANSITIONS (Optional)                       │
│  "Anything else you're navigating right now?"                   │
│                                                                  │
│  [Same options as Step 2, multi-select]                         │
│  [That's the main thing]  ← Skip option                         │
│                                                                  │
│  ───────────────────────────────────────────────────────────────│
│                                                                  │
│  STEP 5: PREFERENCES                                            │
│  "A few quick things so I can reach you right..."               │
│                                                                  │
│  • What should I call you? [name]                               │
│  • What time works for daily check-ins? [time picker]           │
│  • (Timezone auto-detected)                                     │
│                                                                  │
│  ───────────────────────────────────────────────────────────────│
│                                                                  │
│  STEP 6: COMPANION IDENTITY                                     │
│  "What would you like to call me?"                              │
│  [Name input, default "Aria"]                                   │
│                                                                  │
│  ───────────────────────────────────────────────────────────────│
│                                                                  │
│  STEP 7: IMMEDIATE VALUE (New!)                                 │
│  Generate and display first acknowledgment message              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ARIA                                                     │   │
│  │                                                          │   │
│  │ "I hear you're looking for a new job and figuring out   │   │
│  │ the interview process. That's a lot to navigate.        │   │
│  │                                                          │   │
│  │ I'll check in with you about this. You mentioned the    │   │
│  │ interview at TechCorp on Friday — I'll ask how it went. │   │
│  │                                                          │   │
│  │ For now, is there anything specific on your mind?"      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  [Continue to Chat] [Go to Dashboard]                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
User selects "Looking for a job"
    ↓
template_key = "job_search"
domain = "career"
    ↓
User provides details: "I have an interview at TechCorp on Friday"
    ↓
Classify and extract:
    - summary: "Interview at TechCorp on Friday"
    - phase: "interviewing"
    - follow_up_date: Friday + 1 day
    - key_entities: ["TechCorp", "Friday"]
    ↓
Create thread:
    life_threads.insert({
        user_id,
        topic: "job_search",
        domain: "career",
        template_id: [job_search template UUID],
        phase: "interviewing",
        summary: "Interview at TechCorp on Friday",
        follow_up_date: "2026-01-28",
        priority_weight: 1.5  // User-declared primary domain
    })
    ↓
Set user domain preferences:
    users.domain_preferences = {
        primary_domains: ["career"],
        domain_weights: { career: 1.5 },
        onboarding_selections: ["job_search"]
    }
    ↓
Generate immediate acknowledgment:
    Use template.follow_up_prompts.initial
    + extracted details
    + set expectation for follow-up
    ↓
Display in Step 7
```

### 2.3 API Changes

```python
# New endpoint: POST /onboarding/complete-v2
@router.post("/onboarding/complete-v2")
async def complete_onboarding_v2(
    request: OnboardingCompleteV2Request,
    user_id: UUID = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """
    Complete onboarding with domain-first flow.
    Creates typed threads and generates immediate acknowledgment.
    """
    # 1. Save user preferences
    await save_user_preferences(db, user_id, request.preferences)

    # 2. Set domain preferences
    await save_domain_preferences(db, user_id, request.domain_selections)

    # 3. Create threads from selections
    threads = []
    for selection in request.domain_selections:
        thread = await create_thread_from_template(
            db, user_id,
            template_key=selection.template_key,
            details=selection.details,
            is_primary=selection.is_primary
        )
        threads.append(thread)

    # 4. Generate immediate acknowledgment message
    acknowledgment = await generate_acknowledgment_message(
        user_id=user_id,
        threads=threads,
        companion_name=request.preferences.companion_name
    )

    # 5. Save acknowledgment as first message in new conversation
    conversation = await create_conversation(db, user_id)
    await save_message(db, conversation.id, role="assistant", content=acknowledgment)

    # 6. Mark onboarding complete
    await mark_onboarding_complete(db, user_id, path="v2_domain_first")

    return OnboardingCompleteV2Response(
        success=True,
        acknowledgment_message=acknowledgment,
        conversation_id=conversation.id,
        threads_created=[t.id for t in threads]
    )


# Request/Response models
class DomainSelection(BaseModel):
    template_key: str           # "job_search"
    details: str                # "Interview at TechCorp on Friday"
    is_primary: bool = False    # First selection = primary

class OnboardingCompleteV2Request(BaseModel):
    domain_selections: List[DomainSelection]  # 1-3 selections
    preferences: UserPreferences              # name, time, timezone, companion_name

class OnboardingCompleteV2Response(BaseModel):
    success: bool
    acknowledgment_message: str
    conversation_id: UUID
    threads_created: List[UUID]
```

---

## Part 3: Frontend Surfacing

### 3.1 Chat Thread Context Header

```typescript
// New component: ThreadContextHeader.tsx

interface ThreadContextHeaderProps {
  threads: ThreadSummary[];
  maxVisible?: number;  // Default 3
  onThreadClick?: (threadId: string) => void;
}

export function ThreadContextHeader({
  threads,
  maxVisible = 3,
  onThreadClick
}: ThreadContextHeaderProps) {
  const [expanded, setExpanded] = useState(false);

  const visibleThreads = expanded ? threads : threads.slice(0, maxVisible);
  const hiddenCount = threads.length - maxVisible;

  if (threads.length === 0) return null;

  return (
    <div className="border-b border-gray-100 bg-gray-50 px-4 py-2">
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <span className="font-medium">Tracking:</span>
        <div className="flex flex-wrap gap-2">
          {visibleThreads.map(thread => (
            <ThreadChip
              key={thread.id}
              thread={thread}
              onClick={() => onThreadClick?.(thread.id)}
            />
          ))}
          {!expanded && hiddenCount > 0 && (
            <button
              onClick={() => setExpanded(true)}
              className="text-blue-600 hover:text-blue-800"
            >
              +{hiddenCount} more
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function ThreadChip({ thread, onClick }: { thread: ThreadSummary; onClick?: () => void }) {
  const domainIcon = DOMAIN_ICONS[thread.domain] || '📌';
  const phaseLabel = thread.phase ? ` (${formatPhase(thread.phase)})` : '';

  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-1 px-2 py-1 bg-white border border-gray-200 rounded-full text-xs hover:bg-gray-100"
    >
      <span>{domainIcon}</span>
      <span>{thread.display_name}{phaseLabel}</span>
    </button>
  );
}

const DOMAIN_ICONS: Record<string, string> = {
  career: '💼',
  location: '📍',
  relationships: '💕',
  health: '🏥',
  creative: '🚀',
  life_stage: '🎓',
  personal: '💭'
};
```

### 3.2 Chat Page Integration

```typescript
// In chat/[id]/page.tsx

export default function ChatPage({ params }: { params: { id: string } }) {
  const { data: threads } = useQuery(['threads', 'active'],
    () => api.memory.getActiveThreads()
  );

  return (
    <div className="flex flex-col h-full">
      {/* Thread context header - NEW */}
      <ThreadContextHeader
        threads={threads || []}
        onThreadClick={(id) => {
          // Could scroll to relevant message or show thread details
        }}
      />

      {/* Existing chat content */}
      <div className="flex-1 overflow-y-auto">
        <MessageList messages={messages} />
      </div>

      <ChatInput onSend={handleSend} />
    </div>
  );
}
```

### 3.3 Memory Page Reorganization

```typescript
// Companion page Memory tab - reorganized by domain

interface DomainGroup {
  domain: string;
  display_name: string;
  icon: string;
  threads: ThreadSummary[];
}

function MemoryTab() {
  const { data: memory } = useQuery(['memory', 'full'], () => api.memory.getFull());

  // Group threads by domain
  const domainGroups = useMemo(() => {
    if (!memory?.threads) return [];

    const grouped = groupBy(memory.threads, 'domain');
    return Object.entries(grouped).map(([domain, threads]) => ({
      domain,
      display_name: DOMAIN_LABELS[domain] || domain,
      icon: DOMAIN_ICONS[domain] || '📌',
      threads: threads.sort((a, b) => b.priority_weight - a.priority_weight)
    }));
  }, [memory?.threads]);

  return (
    <div className="space-y-6">
      {/* Primary: Transitions you're tracking */}
      <section>
        <h3 className="text-lg font-semibold mb-3">What I'm Following</h3>

        {domainGroups.length === 0 ? (
          <EmptyState message="No active threads yet. Tell me what's going on!" />
        ) : (
          <div className="space-y-4">
            {domainGroups.map(group => (
              <DomainGroupCard key={group.domain} group={group} />
            ))}
          </div>
        )}
      </section>

      {/* Secondary: Facts and patterns */}
      <section>
        <h3 className="text-lg font-semibold mb-3">Things I Know</h3>
        <FactsList facts={memory?.facts || {}} />
      </section>

      {memory?.patterns && memory.patterns.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold mb-3">Patterns I've Noticed</h3>
          <PatternsList patterns={memory.patterns} />
        </section>
      )}
    </div>
  );
}

function DomainGroupCard({ group }: { group: DomainGroup }) {
  return (
    <div className="bg-white border rounded-lg p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xl">{group.icon}</span>
        <h4 className="font-medium">{group.display_name}</h4>
        <span className="text-sm text-gray-500">({group.threads.length})</span>
      </div>

      <div className="space-y-2">
        {group.threads.map(thread => (
          <ThreadCard key={thread.id} thread={thread} compact />
        ))}
      </div>
    </div>
  );
}
```

### 3.4 Onboarding Page Updates

```typescript
// Simplified — key changes to onboarding/page.tsx

const TRANSITION_OPTIONS = [
  { key: 'job_search', label: 'Looking for a job', domain: 'career', icon: '💼' },
  { key: 'new_job', label: 'Starting a new job', domain: 'career', icon: '🎉' },
  { key: 'moving', label: 'Moving to a new place', domain: 'location', icon: '📦' },
  { key: 'new_city', label: 'Settling into a new city', domain: 'location', icon: '🏙️' },
  { key: 'breakup', label: 'Going through a breakup', domain: 'relationships', icon: '💔' },
  { key: 'launching', label: 'Building or launching something', domain: 'creative', icon: '🚀' },
  { key: 'personal_health', label: 'Health situation', domain: 'health', icon: '🏥' },
];

function PrimaryTransitionStep({ onSelect }: { onSelect: (key: string) => void }) {
  const [customInput, setCustomInput] = useState('');
  const [showCustom, setShowCustom] = useState(false);

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">
        What's the main thing on your mind right now?
      </h2>

      <div className="grid gap-2">
        {TRANSITION_OPTIONS.map(option => (
          <button
            key={option.key}
            onClick={() => onSelect(option.key)}
            className="flex items-center gap-3 p-4 text-left border rounded-lg hover:bg-gray-50"
          >
            <span className="text-2xl">{option.icon}</span>
            <span>{option.label}</span>
          </button>
        ))}

        <button
          onClick={() => setShowCustom(true)}
          className="flex items-center gap-3 p-4 text-left border rounded-lg hover:bg-gray-50 text-gray-600"
        >
          <span className="text-2xl">💭</span>
          <span>Something else...</span>
        </button>
      </div>

      {showCustom && (
        <div className="mt-4">
          <textarea
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            placeholder="Tell me what's going on..."
            className="w-full p-3 border rounded-lg"
            rows={3}
          />
          <button
            onClick={() => onSelect(`custom:${customInput}`)}
            disabled={!customInput.trim()}
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg"
          >
            Continue
          </button>
        </div>
      )}
    </div>
  );
}
```

---

## Part 4: Implementation Phases

### Phase 1: Foundation (Week 1)

**Goal**: Database schema and seed data ready

| Task | Effort | Owner |
|------|--------|-------|
| Create `thread_templates` table migration | 2h | Backend |
| Add domain fields to `life_threads` | 1h | Backend |
| Add `domain_preferences` to users | 1h | Backend |
| Seed 15-20 starter templates | 3h | Backend |
| Create DomainClassifier service stub | 2h | Backend |

**Deliverable**: Schema deployed, templates seeded, classification service skeleton

### Phase 2: Onboarding V2 (Week 1-2)

**Goal**: Domain-first onboarding with immediate value

| Task | Effort | Owner |
|------|--------|-------|
| Design onboarding UI flow | 4h | Design/Frontend |
| Build PrimaryTransitionStep component | 4h | Frontend |
| Build SituationDetailsStep component | 3h | Frontend |
| Build SecondaryTransitionsStep component | 2h | Frontend |
| Create `/onboarding/complete-v2` endpoint | 4h | Backend |
| Generate acknowledgment message logic | 4h | Backend |
| Build ImmediateValueStep (shows first message) | 3h | Frontend |
| Wire up full onboarding flow | 4h | Frontend |
| Test end-to-end | 4h | QA |

**Deliverable**: New onboarding live, users get typed threads + immediate acknowledgment

### Phase 3: Chat Integration (Week 2)

**Goal**: Thread context visible in chat

| Task | Effort | Owner |
|------|--------|-------|
| Build ThreadContextHeader component | 3h | Frontend |
| Build ThreadChip component | 1h | Frontend |
| Add `/threads/active` endpoint | 2h | Backend |
| Integrate header into chat page | 2h | Frontend |
| Style and polish | 2h | Frontend |

**Deliverable**: Chat shows "Tracking: Job Search, Moving to Austin" header

### Phase 4: Memory Reorganization (Week 2-3)

**Goal**: Memory page organized by domain

| Task | Effort | Owner |
|------|--------|-------|
| Build DomainGroupCard component | 3h | Frontend |
| Refactor MemoryTab for domain grouping | 4h | Frontend |
| Update ThreadCard with phase badge | 2h | Frontend |
| Update API to return domain-grouped data | 2h | Backend |
| Style and polish | 2h | Frontend |

**Deliverable**: Memory page shows threads grouped by life domain

### Phase 5: Classification Integration (Week 3)

**Goal**: Ongoing extraction classifies into domains

| Task | Effort | Owner |
|------|--------|-------|
| Implement DomainClassifier with LLM | 6h | Backend |
| Integrate into thread extraction flow | 4h | Backend |
| Add phase detection to extraction | 4h | Backend |
| Backfill existing threads (migration) | 3h | Backend |
| Test classification accuracy | 4h | QA |

**Deliverable**: New threads from conversation get domain + phase classification

### Phase 6: Polish & Validation (Week 3-4)

**Goal**: Ready for user validation

| Task | Effort | Owner |
|------|--------|-------|
| Landing page copy update | 4h | Marketing |
| Error states and edge cases | 4h | Frontend |
| Analytics events for domain tracking | 3h | Backend |
| Performance optimization | 3h | Full stack |
| Documentation update | 2h | All |
| Recruit 10 test users | - | Founder |

**Deliverable**: Production-ready for user validation

---

## Part 5: Migration Strategy

### Existing Users

```sql
-- Backfill domain for existing threads
UPDATE life_threads
SET domain = CASE
    WHEN topic ILIKE '%job%' OR topic ILIKE '%interview%' OR topic ILIKE '%career%' THEN 'career'
    WHEN topic ILIKE '%mov%' OR topic ILIKE '%city%' OR topic ILIKE '%apartment%' THEN 'location'
    WHEN topic ILIKE '%relationship%' OR topic ILIKE '%breakup%' OR topic ILIKE '%dating%' THEN 'relationships'
    WHEN topic ILIKE '%health%' OR topic ILIKE '%doctor%' OR topic ILIKE '%medical%' THEN 'health'
    WHEN topic ILIKE '%launch%' OR topic ILIKE '%build%' OR topic ILIKE '%project%' THEN 'creative'
    ELSE 'personal'
END
WHERE domain IS NULL;

-- Set default priority weight
UPDATE life_threads SET priority_weight = 1.0 WHERE priority_weight IS NULL;
```

### Feature Flags

```typescript
const FEATURE_FLAGS = {
  DOMAIN_ONBOARDING_V2: false,      // Enable new onboarding flow
  CHAT_THREAD_HEADER: false,        // Show thread context in chat
  MEMORY_DOMAIN_GROUPING: false,    // Group memory by domain
  DOMAIN_CLASSIFICATION: false,     // Classify ongoing extractions
};
```

Roll out progressively:
1. DOMAIN_ONBOARDING_V2 → new users only
2. CHAT_THREAD_HEADER → all users
3. MEMORY_DOMAIN_GROUPING → all users
4. DOMAIN_CLASSIFICATION → all users (after validation)

---

## Part 6: Success Metrics

### Primary Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Day 0 engagement** | >80% continue to chat | % who click "Continue to Chat" after acknowledgment |
| **Thread creation rate** | >90% users have typed thread | % with domain != null after onboarding |
| **Day 3 retention** | >40% return | % who open app on Day 3+ |
| **Follow-up response rate** | >50% respond to follow-ups | % who reply to domain-specific follow-up messages |

### Secondary Metrics

| Metric | Purpose |
|--------|---------|
| Template distribution | Which domains are most common |
| Multi-thread rate | % with 2+ active threads |
| Phase progression | Do users move through phases |
| Classification accuracy | Manual review of domain assignments |

---

## Part 7: Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Templates feel constraining | Medium | High | "Something else" always available; soft priority, not hard filter |
| Classification errors | Medium | Medium | Confidence threshold; fallback to "personal" domain |
| Onboarding too long | Low | Medium | Skip options; can complete in <2 min |
| Multiple threads = cognitive overload | Medium | Low | Priority ranking; max 3 visible by default |
| Existing users confused by changes | Low | Medium | Feature flags; gradual rollout |

---

## Appendix: Files to Create/Modify

### New Files

```
api/
├── src/app/
│   ├── models/
│   │   └── domain.py                    # ThreadTemplate, DomainPreferences models
│   ├── services/
│   │   └── domain_classifier.py         # Classification service
│   └── routes/
│       └── templates.py                 # Thread templates API

web/
├── src/
│   ├── components/
│   │   ├── ThreadContextHeader.tsx      # Chat header with threads
│   │   ├── ThreadChip.tsx               # Individual thread chip
│   │   └── DomainGroupCard.tsx          # Memory page domain group
│   └── app/(onboarding)/
│       └── onboarding-v2/               # New onboarding flow
│           └── page.tsx

supabase/
└── migrations/
    └── XXX_domain_layer.sql             # Schema changes
```

### Modified Files

```
api/
├── src/app/
│   ├── services/
│   │   └── threads.py                   # Add domain to extraction
│   └── routes/
│       └── onboarding.py                # Add complete-v2 endpoint
│       └── memory.py                    # Add domain-grouped response

web/
├── src/
│   ├── app/
│   │   ├── chat/[id]/page.tsx           # Add thread header
│   │   └── (dashboard)/companion/page.tsx  # Reorganize memory tab
│   └── lib/api/
│       └── client.ts                    # Add new endpoints
```

---

## Next Steps

1. **Review this plan** — Any gaps or concerns?
2. **Prioritize** — Which phases are must-have vs nice-to-have for first validation?
3. **Assign** — Who owns what?
4. **Start** — Begin with Phase 1 (schema + seeds)

---

**Document Status**: Draft for review
**Last Updated**: 2026-01-26
