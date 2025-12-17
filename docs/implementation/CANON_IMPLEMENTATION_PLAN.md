# Canon Implementation Plan

**Status:** ACTIVE - Authoritative Implementation Reference

**Scope:** Full implementation of CONTENT_ARCHITECTURE_CANON.md and EPISODE_DYNAMICS_CANON.md

**Created:** 2024-12-17

**Supersedes:**
- `IMPLEMENTATION_PLAN.md` (legacy phases)
- `EP-01_EPISODE_FIRST_IMPLEMENTATION.md` (merged)
- `SESSION_ENGAGEMENT_REFACTOR.md` (merged)
- `STUDIO_EPISODE_FIRST_REFACTOR.md` (merged)

---

## Executive Summary

This plan implements the full canon architecture in 5 phases:

1. **Database Schema** — Series table, episode dynamics columns, table renames
2. **Context Building** — Dramatic question, beat guidance, resolution space in LLM context
3. **API Layer** — Series CRUD, session state, resolution tracking
4. **Studio UI** — Hierarchical content management (World → Series → Character → Episode)
5. **Discovery UI** — Series-first browsing, session state display

**Approach:** Small → Big (foundation first, additive layers)

---

## Phase 1: Database Schema

### 1.1 Create Series Table

```sql
-- New table: series (narrative containers)
CREATE TABLE series (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    world_id UUID REFERENCES worlds(id),
    series_type VARCHAR(20) DEFAULT 'standalone',
    -- Values: 'standalone', 'serial', 'anthology', 'crossover'
    featured_characters JSONB DEFAULT '[]',
    episode_order JSONB DEFAULT '[]',
    total_episodes INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft',
    -- Values: 'draft', 'active', 'completed'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_series_world ON series(world_id);
CREATE INDEX idx_series_status ON series(status);
CREATE INDEX idx_series_slug ON series(slug);
```

### 1.2 Add Episode Dynamics Columns

```sql
-- Add to episode_templates
ALTER TABLE episode_templates ADD COLUMN IF NOT EXISTS series_id UUID REFERENCES series(id);
ALTER TABLE episode_templates ADD COLUMN IF NOT EXISTS dramatic_question TEXT;
ALTER TABLE episode_templates ADD COLUMN IF NOT EXISTS beat_guidance JSONB DEFAULT '{}';
ALTER TABLE episode_templates ADD COLUMN IF NOT EXISTS resolution_types TEXT[] DEFAULT '{"positive","neutral","negative"}';
ALTER TABLE episode_templates ADD COLUMN IF NOT EXISTS memory_triggers JSONB DEFAULT '[]';
ALTER TABLE episode_templates ADD COLUMN IF NOT EXISTS hooks_config JSONB DEFAULT '[]';
ALTER TABLE episode_templates ADD COLUMN IF NOT EXISTS target_length_messages INTEGER;

-- Indexes
CREATE INDEX idx_episode_templates_series ON episode_templates(series_id);
```

### 1.3 Add Session State Tracking

```sql
-- Add to sessions (currently 'episodes' table)
ALTER TABLE episodes ADD COLUMN IF NOT EXISTS session_state VARCHAR(20) DEFAULT 'active';
-- Values: 'active', 'paused', 'faded', 'complete'

ALTER TABLE episodes ADD COLUMN IF NOT EXISTS resolution_type VARCHAR(20);
-- Values: 'positive', 'neutral', 'negative', 'surprise', NULL

ALTER TABLE episodes ADD COLUMN IF NOT EXISTS episode_summary_generated TEXT;
-- For serial progression context
```

### 1.4 Add World Genre Field

```sql
-- Add genre to worlds
ALTER TABLE worlds ADD COLUMN IF NOT EXISTS genre VARCHAR(50);
-- Values: 'romantic_tension', 'psychological_thriller', etc.
```

### 1.5 Add Character Crossover Flag

```sql
-- Add crossover capability to characters
ALTER TABLE characters ADD COLUMN IF NOT EXISTS can_crossover BOOLEAN DEFAULT FALSE;
```

### 1.6 Rename Tables (Streamline Terminology)

```sql
-- Rename episodes → sessions
ALTER TABLE episodes RENAME TO sessions;

-- Rename relationships → engagements
ALTER TABLE relationships RENAME TO engagements;

-- Rename columns to match
ALTER TABLE sessions RENAME COLUMN relationship_id TO engagement_id;
ALTER TABLE engagements RENAME COLUMN total_episodes TO total_sessions;

-- Drop deprecated columns
ALTER TABLE engagements DROP COLUMN IF EXISTS stage;
ALTER TABLE engagements DROP COLUMN IF EXISTS stage_progress;
```

### 1.7 Update Indexes and Constraints

```sql
-- Rename indexes to match new table names
ALTER INDEX IF EXISTS episodes_pkey RENAME TO sessions_pkey;
ALTER INDEX IF EXISTS idx_episodes_active RENAME TO idx_sessions_active;
ALTER INDEX IF EXISTS idx_episodes_user_character RENAME TO idx_sessions_user_character;

ALTER INDEX IF EXISTS relationships_pkey RENAME TO engagements_pkey;
ALTER INDEX IF EXISTS idx_relationships_user RENAME TO idx_engagements_user;

-- Update FK constraint names
ALTER TABLE sessions
  DROP CONSTRAINT IF EXISTS episodes_relationship_id_fkey,
  ADD CONSTRAINT sessions_engagement_id_fkey
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE SET NULL;
```

### 1.8 Update RLS Policies

```sql
-- Sessions policies
DROP POLICY IF EXISTS episodes_insert_own ON sessions;
DROP POLICY IF EXISTS episodes_select_own ON sessions;
DROP POLICY IF EXISTS episodes_update_own ON sessions;

CREATE POLICY sessions_insert_own ON sessions FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY sessions_select_own ON sessions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY sessions_update_own ON sessions FOR UPDATE USING (auth.uid() = user_id);

-- Engagements policies
DROP POLICY IF EXISTS relationships_delete_own ON engagements;
DROP POLICY IF EXISTS relationships_insert_own ON engagements;
DROP POLICY IF EXISTS relationships_select_own ON engagements;
DROP POLICY IF EXISTS relationships_update_own ON engagements;

CREATE POLICY engagements_delete_own ON engagements FOR DELETE USING (auth.uid() = user_id);
CREATE POLICY engagements_insert_own ON engagements FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY engagements_select_own ON engagements FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY engagements_update_own ON engagements FOR UPDATE USING (auth.uid() = user_id);
```

---

## Phase 2: Context Building Enhancement

### 2.1 Update ConversationService Context Assembly

Location: `substrate-api/api/src/app/services/conversation.py`

**Current context layers:**
1. Character system prompt
2. Memory context
3. Session history

**Target context layers (per EPISODE_DYNAMICS_CANON.md § 6.5):**
1. Character system prompt (personality, genre doctrine)
2. Episode context:
   - Dramatic question
   - Beat guidance
   - Resolution space
   - Episode frame
3. Memory context (relevance-weighted, summarized if needed)
4. Series context (for serial series):
   - Previous episode summaries
   - Series-level arc awareness
5. Session history

### 2.2 Inject Dramatic Question

```python
# In context building
if episode_template and episode_template.dramatic_question:
    episode_context += f"\n\nDRAMATIC QUESTION FOR THIS EPISODE:\n{episode_template.dramatic_question}"
    episode_context += "\n(This is the tension you're exploring. Don't state it explicitly, inhabit it.)"
```

### 2.3 Inject Beat Guidance

```python
# Beat guidance for pacing
if episode_template and episode_template.beat_guidance:
    beats = episode_template.beat_guidance
    episode_context += f"\n\nNARRATIVE PACING GUIDANCE:"
    if 'establishment' in beats:
        episode_context += f"\n- Establishment: {beats['establishment']}"
    if 'complication' in beats:
        episode_context += f"\n- Complication: {beats['complication']}"
    if 'escalation' in beats:
        episode_context += f"\n- Escalation: {beats['escalation']}"
    if 'pivot_markers' in beats:
        episode_context += f"\n- Resolution signals: {beats['pivot_markers']}"
```

### 2.4 Inject Resolution Space

```python
# Resolution awareness
if episode_template and episode_template.resolution_types:
    types = episode_template.resolution_types
    episode_context += f"\n\nVALID RESOLUTION TYPES: {', '.join(types)}"
    episode_context += "\n(Let the conversation flow naturally toward one of these.)"
```

### 2.5 Series Context for Serial Progression

```python
# For serial series, inject previous episode summaries
if series and series.series_type == 'serial':
    previous_summaries = await get_previous_episode_summaries(
        user_id, character_id, series_id, current_episode_number
    )
    if previous_summaries:
        series_context = "\n\nPREVIOUS EPISODES IN THIS SERIES:"
        for summary in previous_summaries:
            series_context += f"\n- Episode {summary.episode_number}: {summary.summary}"
```

### 2.6 Token Budget Management

```python
# Context budget allocation
TOKEN_BUDGETS = {
    'character_prompt': 800,    # Critical, never truncated
    'episode_context': 500,     # Critical, defines the episode
    'memory_context': 1000,     # High priority, summarize if needed
    'series_context': 400,      # Medium, for serial only
    'session_history': None,    # Remaining tokens
}

# Summarization logic for memory if exceeds budget
if memory_token_count > TOKEN_BUDGETS['memory_context']:
    memories = summarize_memories(memories, TOKEN_BUDGETS['memory_context'])
```

---

## Phase 3: API Layer Updates

### 3.1 New Endpoints: Series CRUD

```python
# routes/series.py

@router.get("/series")
async def list_series(
    world_id: Optional[str] = None,
    status: Optional[str] = None,
    series_type: Optional[str] = None
) -> List[SeriesResponse]:
    """List all series, optionally filtered."""
    pass

@router.get("/series/{series_id}")
async def get_series(series_id: str) -> SeriesDetailResponse:
    """Get series with ordered episodes."""
    pass

@router.post("/series")
async def create_series(data: SeriesCreateRequest) -> SeriesResponse:
    """Create a new series."""
    pass

@router.patch("/series/{series_id}")
async def update_series(series_id: str, data: SeriesUpdateRequest) -> SeriesResponse:
    """Update series details or episode order."""
    pass

@router.get("/series/{series_id}/episodes")
async def get_series_episodes(series_id: str) -> List[EpisodeTemplateResponse]:
    """Get episodes in series order."""
    pass
```

### 3.2 Session State Management

```python
# routes/sessions.py (rename from episodes.py)

@router.patch("/sessions/{session_id}/state")
async def update_session_state(
    session_id: str,
    state: Literal['active', 'paused', 'faded', 'complete'],
    resolution_type: Optional[Literal['positive', 'neutral', 'negative', 'surprise']] = None
) -> SessionResponse:
    """Update session state and optionally set resolution type."""
    pass

@router.post("/sessions/{session_id}/resume")
async def resume_session(session_id: str) -> SessionResponse:
    """Resume a paused or faded session."""
    pass

@router.post("/sessions/{session_id}/generate-summary")
async def generate_episode_summary(session_id: str) -> SessionSummaryResponse:
    """Generate summary for serial progression."""
    pass
```

### 3.3 Resolution Detection Integration

```python
# In conversation response handling
async def process_llm_response(response: str, session: Session) -> ProcessedResponse:
    """Process LLM response and detect resolution hints."""

    # LLM includes resolution_hint in structured output
    resolution_hint = extract_resolution_hint(response)

    if resolution_hint == 'natural_pause':
        # Suggest continuation option to frontend
        return ProcessedResponse(
            content=response,
            resolution_hint='natural_pause',
            suggested_action='offer_continue'
        )
    elif resolution_hint == 'approaching_closure':
        # Prepare for memory extraction
        return ProcessedResponse(
            content=response,
            resolution_hint='approaching_closure',
            suggested_action='suggest_next_episode'
        )

    return ProcessedResponse(content=response)
```

### 3.4 Summary Bridge for Soft-Gated Serial Episodes

```python
@router.post("/series/{series_id}/episodes/{episode_number}/summary-bridge")
async def get_summary_bridge(
    series_id: str,
    episode_number: int,
    user_id: str
) -> SummaryBridgeResponse:
    """Get summary of skipped episodes for soft-gate catch-up."""

    # Get all completed sessions for earlier episodes
    previous_sessions = await get_user_sessions_before(
        user_id, series_id, episode_number
    )

    # Generate or retrieve summaries
    summaries = []
    for ep_num in range(0, episode_number):
        session = find_session_for_episode(previous_sessions, ep_num)
        if session and session.episode_summary_generated:
            summaries.append(session.episode_summary_generated)
        else:
            # Generate from episode template description
            template = await get_episode_template(series_id, ep_num)
            summaries.append(f"In Episode {ep_num}: {template.situation[:200]}...")

    return SummaryBridgeResponse(
        episode_summaries=summaries,
        catch_up_text="\n".join(summaries)
    )
```

### 3.5 Rename Endpoints

| Old Endpoint | New Endpoint |
|--------------|--------------|
| `/relationships` | `/engagements` |
| `/episodes` | `/sessions` |
| `/episodes/{id}` | `/sessions/{id}` |
| `/characters/{id}/relationship` | `/characters/{id}/engagement` |

---

## Phase 4: Studio UI (Hierarchical)

### 4.1 New Page Structure

```
/studio
├── /worlds                    # World management (top level)
│   ├── page.tsx               # World list
│   ├── create/page.tsx        # Create world
│   └── [worldId]/
│       ├── page.tsx           # World detail (shows series + characters)
│       └── edit/page.tsx      # Edit world
│
├── /series                    # Series management
│   ├── page.tsx               # Series list (all)
│   ├── create/page.tsx        # Create series
│   └── [seriesId]/
│       ├── page.tsx           # Series detail (ordered episodes)
│       └── edit/page.tsx      # Edit series + reorder episodes
│
├── /characters                # Character management
│   ├── page.tsx               # Character list
│   ├── create/page.tsx        # Create character (simplified)
│   └── [characterId]/
│       ├── page.tsx           # Character detail + episodes
│       └── edit/page.tsx      # Edit character
│
└── /episodes                  # Episode template management
    ├── page.tsx               # Episode list (all)
    ├── create/page.tsx        # Create episode (episode-first)
    └── [episodeId]/
        ├── page.tsx           # Episode detail
        └── edit/page.tsx      # Edit episode template
```

### 4.2 Studio Home (Hierarchical Dashboard)

```tsx
// /studio/page.tsx
<StudioDashboard>
  {/* Quick Actions */}
  <QuickActions>
    <Button href="/studio/worlds/create">+ New World</Button>
    <Button href="/studio/series/create">+ New Series</Button>
    <Button href="/studio/episodes/create">+ New Episode</Button>
  </QuickActions>

  {/* Hierarchical View */}
  <ContentHierarchy>
    {worlds.map(world => (
      <WorldCard key={world.id} world={world}>
        <SeriesList worldId={world.id} />
        <CharacterList worldId={world.id} />
      </WorldCard>
    ))}
  </ContentHierarchy>
</StudioDashboard>
```

### 4.3 World Detail Page

```tsx
// /studio/worlds/[worldId]/page.tsx
<WorldDetail>
  <WorldHeader>
    <h1>{world.name}</h1>
    <Badge>{world.genre}</Badge>
    <Badge>{world.tone}</Badge>
  </WorldHeader>

  <Tabs>
    <Tab label="Series">
      <SeriesGrid worldId={world.id} />
      <CreateSeriesButton worldId={world.id} />
    </Tab>
    <Tab label="Characters">
      <CharacterGrid worldId={world.id} />
      <CreateCharacterButton worldId={world.id} />
    </Tab>
    <Tab label="World Bible">
      <WorldBibleEditor world={world} />
    </Tab>
  </Tabs>
</WorldDetail>
```

### 4.4 Series Detail Page (Episode Ordering)

```tsx
// /studio/series/[seriesId]/page.tsx
<SeriesDetail>
  <SeriesHeader>
    <h1>{series.title}</h1>
    <Badge>{series.series_type}</Badge>
    <Badge>{series.status}</Badge>
  </SeriesHeader>

  <EpisodeOrderList>
    {/* Drag-and-drop reordering */}
    <DraggableList
      items={orderedEpisodes}
      onReorder={handleReorder}
      renderItem={(episode, index) => (
        <EpisodeOrderCard
          episode={episode}
          episodeNumber={index}
          onEdit={() => editEpisode(episode.id)}
        />
      )}
    />
    <AddEpisodeButton seriesId={series.id} />
  </EpisodeOrderList>
</SeriesDetail>
```

### 4.5 Episode Create (Episode-First Flow)

```tsx
// /studio/episodes/create/page.tsx
<EpisodeCreateWizard>
  <Step title="Episode Concept">
    <Input label="Title" name="title" />
    <Select label="Episode Type" name="episode_type"
      options={['entry', 'core', 'expansion', 'special']} />
    <Select label="Series (Optional)" name="series_id"
      options={seriesOptions} />
  </Step>

  <Step title="Dramatic Question">
    <Textarea label="Dramatic Question" name="dramatic_question"
      placeholder="What tension does this episode explore? e.g., 'Will she let you stay after closing?'" />
    <GenerateButton onClick={generateDramaticQuestion} />
  </Step>

  <Step title="Opening">
    <Textarea label="Episode Frame" name="episode_frame"
      placeholder="Platform stage direction (italic, atmospheric)" />
    <Textarea label="Opening Line" name="opening_line"
      placeholder="Character's first message" />
    <GenerateButton onClick={generateOpeningBeat} />
  </Step>

  <Step title="Beat Guidance">
    <BeatGuidanceEditor name="beat_guidance" />
    {/* Structured editor for establishment, complication, escalation, pivot */}
  </Step>

  <Step title="Character Assignment">
    <CharacterSelect name="character_id" required />
    {/* Or create new character inline */}
  </Step>

  <Step title="Review & Save">
    <EpisodePreview data={formData} />
    <SaveButton />
  </Step>
</EpisodeCreateWizard>
```

### 4.6 Character Create (Simplified)

```tsx
// /studio/characters/create/page.tsx
// REMOVED: Opening beat step (now in episode creation)
<CharacterCreateWizard>
  <Step title="Core Identity">
    <Input label="Name" name="name" />
    <Select label="World" name="world_id" options={worldOptions} />
    <Select label="Archetype" name="archetype"
      options={archetypeOptions} />
    <Select label="Genre" name="genre"
      options={['romantic_tension', 'psychological_thriller']} />
  </Step>

  <Step title="Personality">
    <PersonalityPresetSelector name="baseline_personality" />
    <BoundariesEditor name="boundaries" />
    <ContentRatingSelector name="content_rating" />
  </Step>

  <Step title="Visual Identity">
    <AvatarGenerator characterData={formData} />
  </Step>

  <Step title="Review & Save">
    <CharacterPreview data={formData} />
    <SaveButton />
    <Note>After saving, create episodes for this character.</Note>
  </Step>
</CharacterCreateWizard>
```

---

## Phase 5: Discovery UI Refactor

### 5.1 New Page Structure

```
/discover                      # Main browse page (series-first)
/series/[seriesSlug]           # Series detail with episodes
/characters/[characterSlug]    # Character detail (secondary)
/chat/[characterSlug]          # Chat interface (unchanged)

/dashboard                     # User's home
├── page.tsx                   # Continue sessions, recommendations
├── /sessions                  # Chat history (renamed from /chats)
└── /memories                  # Memory viewer
```

### 5.2 Discover Page (Series-First)

```tsx
// /discover/page.tsx
<DiscoverPage>
  {/* Featured Content */}
  <FeaturedSection>
    <FeaturedSeriesCarousel series={featuredSeries} />
  </FeaturedSection>

  {/* Browse by World */}
  <WorldBrowser>
    {worlds.map(world => (
      <WorldSection key={world.id}>
        <h2>{world.name}</h2>
        <Badge>{world.genre}</Badge>
        <SeriesRow series={world.series} />
        <CharacterRow characters={world.characters} />
      </WorldSection>
    ))}
  </WorldBrowser>

  {/* Browse by Mood/Genre */}
  <GenreBrowser>
    <GenreFilter
      options={['romantic_tension', 'psychological_thriller']}
      onChange={setGenreFilter}
    />
    <FilteredResults genre={genreFilter} />
  </GenreBrowser>
</DiscoverPage>
```

### 5.3 Series Detail Page

```tsx
// /series/[seriesSlug]/page.tsx
<SeriesDetailPage>
  <SeriesHeader>
    <h1>{series.title}</h1>
    <p>{series.description}</p>
    <Badge>{series.series_type}</Badge>
    <FeaturedCharacters characters={series.featured_characters} />
  </SeriesHeader>

  <EpisodeList>
    {orderedEpisodes.map((episode, index) => (
      <EpisodeCard
        key={episode.id}
        episode={episode}
        episodeNumber={index}
        userProgress={userProgress[episode.id]}
        onStart={() => startEpisode(episode.id)}
      />
    ))}
  </EpisodeList>

  {/* Soft Gate for Serial */}
  {series.series_type === 'serial' && !hasCompletedEpisode0 && (
    <SoftGateModal
      onStartFromBeginning={() => startEpisode(episode0.id)}
      onQuickCatchUp={() => showSummaryBridge()}
      onJumpAnyway={() => startEpisode(selectedEpisode.id)}
    />
  )}
</SeriesDetailPage>
```

### 5.4 Dashboard (Sessions-Focused)

```tsx
// /dashboard/page.tsx
<DashboardPage>
  {/* Continue Sessions */}
  <ContinueSection>
    <h2>Continue</h2>
    <SessionCardList sessions={activeSessions}>
      {session => (
        <SessionCard
          session={session}
          state={session.session_state}
          onResume={() => resumeSession(session.id)}
        />
      )}
    </SessionCardList>
  </ContinueSection>

  {/* For You (Recommendations) */}
  <ForYouSection>
    <h2>For You</h2>
    <RecommendedEpisodes
      basedOn={userEngagements}
      excludeCompleted
    />
  </ForYouSection>

  {/* Recent Characters */}
  <RecentCharactersSection>
    <h2>Recent Characters</h2>
    <CharacterCardList engagements={recentEngagements} />
  </RecentCharactersSection>
</DashboardPage>
```

### 5.5 Chat Interface Updates

```tsx
// /chat/[characterSlug]/page.tsx
<ChatPage>
  <ChatHeader>
    <CharacterAvatar />
    <CharacterName />
    <SessionStateBadge state={session.session_state} />
    {session.resolution_type && (
      <ResolutionBadge type={session.resolution_type} />
    )}
  </ChatHeader>

  <ChatMessages>
    {/* Episode Frame (opening scene card) */}
    {session.isOpening && episodeTemplate.episode_frame && (
      <SceneCard frame={episodeTemplate.episode_frame} />
    )}

    {/* Message list */}
    <MessageList messages={messages} />
  </ChatMessages>

  <ChatInput
    onSend={sendMessage}
    disabled={session.session_state === 'complete'}
  />

  {/* Resolution UI */}
  {resolutionHint === 'natural_pause' && (
    <ContinuePrompt
      onContinue={() => continueSession()}
      onEnd={() => endSession()}
      onNextEpisode={() => startNextEpisode()}
    />
  )}
</ChatPage>
```

---

## Backend File Changes Summary

### Files to Rename

| Old Path | New Path |
|----------|----------|
| `models/relationship.py` | `models/engagement.py` |
| `models/episode.py` | `models/session.py` |
| `routes/relationships.py` | `routes/engagements.py` |
| `routes/episodes.py` | `routes/sessions.py` |

### Files to Create

| Path | Purpose |
|------|---------|
| `models/series.py` | Series model |
| `routes/series.py` | Series CRUD endpoints |
| `services/series_service.py` | Series business logic |
| `services/context_builder.py` | Enhanced context assembly |

### Files to Update

| Path | Changes |
|------|---------|
| `models/character.py` | Add `can_crossover`, remove deprecated fields |
| `models/episode_template.py` | Add `series_id`, `dramatic_question`, `beat_guidance`, etc. |
| `models/world.py` | Add `genre` field |
| `services/conversation.py` | Enhanced context building |
| `routes/chat.py` | Session state handling |

---

## Frontend File Changes Summary

### Files to Remove (Legacy)

| Path | Reason |
|------|--------|
| (none - prefer updating over removing) | |

### Files to Create

| Path | Purpose |
|------|---------|
| `app/(dashboard)/discover/page.tsx` | Series-first discover |
| `app/studio/worlds/*` | World management pages |
| `app/studio/series/*` | Series management pages |
| `app/series/[seriesSlug]/page.tsx` | Public series detail |
| `components/series/*` | Series components |
| `components/studio/WorldEditor.tsx` | World editing |
| `components/studio/SeriesEditor.tsx` | Series editing |
| `components/studio/BeatGuidanceEditor.tsx` | Beat guidance UI |

### Files to Update

| Path | Changes |
|------|---------|
| `types/index.ts` | Add Series, update Session/Engagement types |
| `lib/api/client.ts` | Add series endpoints, rename episode→session |
| `app/(dashboard)/dashboard/page.tsx` | Sessions focus |
| `app/chat/[characterSlug]/page.tsx` | Session state display |
| `app/studio/characters/[id]/page.tsx` | Remove opening beat |
| `app/studio/characters/create/page.tsx` | Simplified flow |

---

## Migration Checklist

### Phase 1 Pre-checks
- [ ] Database backup
- [ ] Verify no active users (low-traffic window)
- [ ] Pre-migration record counts

### Phase 1 Execution
- [ ] Create series table
- [ ] Add episode dynamics columns
- [ ] Add session state columns
- [ ] Add world genre column
- [ ] Add character crossover flag
- [ ] Rename tables (episodes→sessions, relationships→engagements)
- [ ] Update indexes and constraints
- [ ] Update RLS policies
- [ ] Verify post-migration

### Phase 2 Execution
- [ ] Update ConversationService context building
- [ ] Add dramatic question injection
- [ ] Add beat guidance injection
- [ ] Add resolution space injection
- [ ] Add series context for serial
- [ ] Add token budget management
- [ ] Test LLM context output

### Phase 3 Execution
- [ ] Rename route files
- [ ] Update endpoint paths
- [ ] Create series CRUD endpoints
- [ ] Add session state endpoints
- [ ] Add resolution detection
- [ ] Add summary bridge endpoint
- [ ] Update API client

### Phase 4 Execution
- [ ] Create Studio world pages
- [ ] Create Studio series pages
- [ ] Update Studio episode pages
- [ ] Simplify character creation
- [ ] Add hierarchical navigation
- [ ] Test content creation flow

### Phase 5 Execution
- [ ] Refactor discover page
- [ ] Create series detail page
- [ ] Update dashboard
- [ ] Update chat interface
- [ ] Add session state display
- [ ] Add soft gate UI
- [ ] Test user flows

---

## Success Criteria

1. **Schema:** All tables/columns per canon exist
2. **Context:** LLM receives dramatic question, beats, resolution space
3. **API:** Series CRUD works, session states tracked
4. **Studio:** Hierarchical content creation (World → Series → Episode)
5. **Discovery:** Series-first browsing, soft gates for serial
6. **Chat:** Session state visible, resolution prompts work
7. **No Regressions:** Existing conversations and memories preserved

---

## Related Documents

- `docs/CONTENT_ARCHITECTURE_CANON.md` — Content taxonomy (source of truth)
- `docs/EPISODE_DYNAMICS_CANON.md` — Episode mechanics (source of truth)
- `docs/EP-01_pivot_CANON.md` — Episode-first philosophy
- `docs/GLOSSARY.md` — Terminology reference
- `docs/DATABASE_ACCESS.md` — Database connection guide
