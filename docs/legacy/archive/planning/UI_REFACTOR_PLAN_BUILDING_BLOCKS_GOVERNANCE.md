# UI Refactoring Plan: Building Blocks & Governance Pages

**Date**: October 2, 2025
**Scope**: User-facing substrate management UX improvements
**Goal**: Meet users where they are - make substrate management intuitive without sacrificing power

---

## Problem Statement

### Current Issues

1. **Conceptual Overload**
   - "Building Blocks" shows dumps + blocks + context_items all mixed together
   - Users confused by unfamiliar terms ("blocks", "context items", "substrate")
   - No clear hierarchy: what's a file vs. what's extracted knowledge?

2. **Anchor Registry Isolation**
   - Anchors are a core concept but UI is scattered
   - "Manage anchors" link buried in building-blocks header
   - No visual distinction between anchored vs. free blocks

3. **Modal Information Gaps**
   - Block/context item modals lack:
     - Usefulness score (from new usage tracking)
     - Staleness indicator (from new staleness detection)
     - Provenance chain (which dump → which extraction)
     - Related anchors (if substrate is linked to anchor)
   - Can't see extraction quality metrics

4. **Governance Proposal Opacity**
   - Proposals don't show context-aware deduplication
   - No indication of "why this wasn't extracted" (dedup logic)
   - Missing confidence breakdown (agent_confidence vs. usefulness)

---

## Proposed Information Architecture

### New Page Structure

```
/baskets/[id]/
├── /timeline (Uploads tab) ← Dedicated raw_dumps panel (file explorer UX)
├── /building-blocks  ← Blocks + Context Items only (substrate workbench)
├── /governance       ← Proposals with enhanced context
├── /memory           ← Anchors + Memory management (existing)
```

### User Mental Model

**User Journey:**
1. **Upload** files/text → Creates `raw_dumps` (P0 - immutable)
2. **Extract** knowledge → Generates **proposals** for blocks/context items (P1 - governed)
3. **Review** proposals → Approve/reject in governance (decision point)
4. **Manage** building blocks → Anchor important knowledge, let rest evolve
5. **Compose** documents → Use substrate to create narratives

**Terminology Mapping:**
- **Files/Uploads** = raw_dumps (familiar)
- **Building Blocks** = blocks + context_items (manageable chunks)
- **Anchors** = locked canonical knowledge (important things)
- **Proposals** = pending changes (requires decision)

---

## Detailed Refactoring Plan

### 1. Uploads Page (Already Exists - Enhance)

**Current State:**
- `timeline/UploadsPanel.tsx` exists but may be basic

**Enhancements Needed:**
```tsx
// File explorer UX inspired by Finder/Windows Explorer
<UploadsPage>
  {/* Header with stats */}
  <StatsBar>
    <Stat icon="FileIcon">{totalUploads} files uploaded</Stat>
    <Stat icon="ClockIcon">{recentUploads} this week</Stat>
    <Stat icon="CheckIcon">{processedUploads} processed</Stat>
  </StatsBar>

  {/* File list with familiar columns */}
  <FileList>
    <Column name="Name" />         {/* body_md preview or file name */}
    <Column name="Date" />         {/* created_at */}
    <Column name="Size" />         {/* character count */}
    <Column name="Status" />       {/* processing_status: complete, pending, failed */}
    <Column name="Extracted" />    {/* derived_blocks + derived_context_items count */}
  </FileList>

  {/* Actions familiar to file managers */}
  <Actions>
    <Button>Upload New File</Button>
    <Button>Delete Selected</Button>
    <Button>View Extracted Knowledge</Button> {/* Links to building-blocks filtered by dump */}
  </Actions>

  {/* Detail panel when file selected */}
  <DetailPanel>
    <FilePreview /> {/* First 500 chars of body_md */}
    <ExtractionSummary>
      <Badge>{blocks_count} blocks extracted</Badge>
      <Badge>{context_items_count} entities identified</Badge>
      <Badge>Confidence: {avg_confidence}%</Badge>
    </ExtractionSummary>
    <ProvenanceChain>
      Shows: Upload → P0 Capture → P1 Extraction → P2 Relationships
    </ProvenanceChain>
  </DetailPanel>
</UploadsPage>
```

**Key Features:**
- ✅ Familiar file manager UX (no technical jargon)
- ✅ Processing status clear (pending → complete → extracted)
- ✅ Bridge to substrate (click "View Extracted" → building-blocks filtered)

---

### 2. Building Blocks Page (Major Refactor)

**Current State:**
- Shows dumps + blocks + context_items mixed together
- Anchor integration exists but minimal

**New Structure:**

```tsx
<BuildingBlocksPage>
  {/* Header with clearer value prop */}
  <Header>
    <Title>Knowledge Workbench</Title>
    <Description>
      Manage the building blocks extracted from your uploads.
      Anchor important knowledge to lock it in place.
    </Description>
  </Header>

  {/* Stats with context-aware metrics */}
  <StatsBar>
    <Stat>{anchoredCount} Anchored</Stat>
    <Stat>{freeBlocksCount} Free Blocks</Stat>
    <Stat>{contextItemsCount} Entities</Stat>
    <Stat>{staleCount} Stale</Stat> {/* NEW: From staleness detection */}
    <Stat>{unusedCount} Unused</Stat> {/* NEW: From usage tracking */}
  </StatsBar>

  {/* Filter bar */}
  <FilterBar>
    <Tabs>
      <Tab>All Blocks</Tab>
      <Tab>Anchored Only</Tab>
      <Tab>Free Blocks</Tab>
      <Tab>Stale</Tab> {/* NEW */}
      <Tab>Unused</Tab> {/* NEW */}
      <Tab>Context Items</Tab>
    </Tabs>
    <Search placeholder="Search blocks, entities, or content..." />
    <Sort options={['Usefulness', 'Recency', 'Confidence', 'Staleness']} /> {/* NEW */}
  </FilterBar>

  {/* Anchored Section (prominent) */}
  <Section title="Anchored Knowledge" icon="AnchorIcon">
    <Description>
      Locked canonical knowledge. Won't change unless you explicitly update it.
    </Description>
    <BlockGrid>
      {anchoredBlocks.map(block => (
        <AnchoredBlockCard
          key={block.id}
          block={block}
          anchor={anchorMap.get(block.id)}
          onManageAnchor={() => navigate(`/memory#anchor-${anchor.id}`)}
          onViewDetails={() => openModal(block.id)}
        >
          {/* Show anchor label prominently */}
          <AnchorBadge>{anchor.label}</AnchorBadge>
          <AnchorStatus>{anchor.status}</AnchorStatus> {/* FRESH, STALE, NEEDS_REVIEW */}

          {/* NEW: Usefulness & Staleness indicators */}
          <MetricBar>
            <Metric icon="StarIcon" value={usefulness} label="Usefulness" />
            <Metric icon="ClockIcon" value={staleness_days} label="Days since validated" />
          </MetricBar>
        </AnchoredBlockCard>
      ))}
    </BlockGrid>
  </Section>

  {/* Free Blocks Section */}
  <Section title="Free Blocks" icon="BlocksIcon">
    <Description>
      Emerging knowledge that evolves with new uploads. Convert to anchors when ready.
    </Description>
    <BlockGrid>
      {freeBlocks.map(block => (
        <FreeBlockCard
          key={block.id}
          block={block}
          onConvertToAnchor={() => createAnchorFromBlock(block.id)}
          onViewDetails={() => openModal(block.id)}
        >
          <BlockHeader>
            <Title>{block.title}</Title>
            <SemanticTypeBadge>{block.semantic_type}</SemanticTypeBadge>
          </BlockHeader>

          {/* NEW: Context-aware indicators */}
          <Indicators>
            {block.staleness_days > 30 && <Badge variant="warning">Stale</Badge>}
            {block.usefulness_score === 0 && <Badge variant="secondary">Unused</Badge>}
            {block.confidence_score < 0.7 && <Badge variant="caution">Review Suggested</Badge>}
          </Indicators>

          {/* Quick actions */}
          <Actions>
            <Button size="sm" onClick={() => createAnchor(block.id)}>
              <AnchorIcon /> Make Anchor
            </Button>
            <Button size="sm" variant="ghost" onClick={() => openModal(block.id)}>
              Details
            </Button>
          </Actions>
        </FreeBlockCard>
      ))}
    </BlockGrid>
  </Section>

  {/* Context Items Section */}
  <Section title="Entities & Concepts" icon="BrainIcon">
    <Description>
      Named entities, concepts, and relationships extracted from your knowledge.
    </Description>
    <EntityGrid>
      {contextItems.map(item => (
        <EntityCard
          key={item.id}
          item={item}
          onViewDetails={() => openModal(item.id)}
        >
          <EntityLabel>{item.title}</EntityLabel>
          <SemanticMeaning>{item.semantic_meaning}</SemanticMeaning>
          <CategoryBadge>{item.semantic_category}</CategoryBadge>
        </EntityCard>
      ))}
    </EntityGrid>
  </Section>
</BuildingBlocksPage>
```

**Key Improvements:**
- ✅ Clear hierarchy: Anchored (locked) > Free (evolving) > Entities (metadata)
- ✅ Usefulness & staleness visible at a glance
- ✅ Quick action: Convert free block → anchor (one click)
- ✅ Filtering by practical criteria (stale, unused, anchored)

---

### 3. Enhanced Substrate Detail Modal

**Current State:**
- Basic modal shows title, content, metadata
- Missing context-aware metrics

**New Modal Structure:**

```tsx
<SubstrateDetailModal substrate={selected}>
  {/* Header with type and status */}
  <ModalHeader>
    <TypeBadge>{substrate.type}</TypeBadge> {/* block | context_item */}
    <SemanticTypeBadge>{substrate.semantic_type}</SemanticTypeBadge>
    {isAnchored && <AnchorBadge>{anchor.label}</AnchorBadge>}
  </ModalHeader>

  {/* Tab navigation */}
  <Tabs>
    <Tab>Overview</Tab>
    <Tab>Provenance</Tab> {/* NEW */}
    <Tab>Usage</Tab> {/* NEW */}
    <Tab>Quality</Tab> {/* NEW */}
    {isAnchored && <Tab>Anchor</Tab>}
  </Tabs>

  {/* Tab: Overview */}
  <TabPanel name="Overview">
    <Section>
      <Label>Title</Label>
      <EditableField value={substrate.title} onSave={updateTitle} />
    </Section>

    <Section>
      <Label>Content</Label>
      <EditableField
        multiline
        value={substrate.content}
        onSave={updateContent}
        disabled={isAnchored} {/* Anchors update via governance */}
      />
    </Section>

    <Section>
      <Label>Semantic Type</Label>
      <Select value={substrate.semantic_type} onChange={updateType}>
        <Option>goal</Option>
        <Option>constraint</Option>
        <Option>metric</Option>
        <Option>insight</Option>
        {/* ... */}
      </Select>
    </Section>

    {/* NEW: Context-aware metrics */}
    <MetricsSection>
      <Metric
        icon="StarIcon"
        label="Usefulness"
        value={substrate.usefulness_score}
        description={`Referenced ${substrate.times_referenced} times`}
      />
      <Metric
        icon="ClockIcon"
        label="Freshness"
        value={substrate.staleness_days}
        description={`Last validated ${formatDate(substrate.last_validated_at)}`}
        warning={substrate.staleness_days > 30}
      />
      <Metric
        icon="TargetIcon"
        label="Confidence"
        value={substrate.confidence_score}
        description="Extraction confidence from P1 agent"
      />
    </MetricsSection>
  </TabPanel>

  {/* Tab: Provenance (NEW) */}
  <TabPanel name="Provenance">
    <ProvenanceChain>
      <Step icon="FileIcon">
        <Label>Source Upload</Label>
        <Link to={`/timeline?view=uploads&highlight=${substrate.raw_dump_id}`}>
          {dumpPreview} (uploaded {formatDate(dump.created_at)})
        </Link>
      </Step>

      <Step icon="BrainIcon">
        <Label>Extracted by</Label>
        <Badge>{extractionMethod}</Badge>
        <Details>
          Agent: {agent_version}
          Confidence: {extraction_confidence}
          Processing Time: {processing_time_ms}ms
        </Details>
      </Step>

      <Step icon="CheckIcon">
        <Label>Approved</Label>
        <Details>
          Proposal: {proposal_id}
          Approved by: {approved_by}
          Date: {formatDate(approved_at)}
        </Details>
      </Step>

      {relatedBlocks.length > 0 && (
        <Step icon="NetworkIcon">
          <Label>Related Substrate</Label>
          <RelatedList>
            {relatedBlocks.map(related => (
              <RelatedItem key={related.id} onClick={() => openModal(related.id)}>
                {related.title}
              </RelatedItem>
            ))}
          </RelatedList>
        </Step>
      )}
    </ProvenanceChain>
  </TabPanel>

  {/* Tab: Usage (NEW) */}
  <TabPanel name="Usage">
    <UsageTimeline>
      {usageEvents.map(event => (
        <TimelineEvent key={event.id}>
          <Icon>{getEventIcon(event.type)}</Icon>
          <Description>
            {event.type === 'referenced' && `Referenced in document "${event.document_title}"`}
            {event.type === 'searched' && `Appeared in search results for "${event.query}"`}
            {event.type === 'context_provided' && `Provided as context for new extraction`}
          </Description>
          <Timestamp>{formatDate(event.timestamp)}</Timestamp>
        </TimelineEvent>
      ))}
    </UsageTimeline>

    <UsageStats>
      <Stat label="Total References" value={substrate.times_referenced} />
      <Stat label="Last Used" value={formatDate(substrate.last_used_at)} />
      <Stat label="Documents" value={documentsReferencing.length} />
    </UsageStats>
  </TabPanel>

  {/* Tab: Quality (NEW) */}
  <TabPanel name="Quality">
    <QualityMetrics>
      <Metric
        label="Extraction Quality"
        value={extraction_confidence}
        description="How confident the P1 agent was when extracting this"
      />

      <Metric
        label="Deduplication"
        value={was_deduplicated ? 'Yes' : 'No'}
        description={was_deduplicated
          ? `Similar to existing block: ${duplicate_of_title}`
          : 'Unique extraction - no duplicates found'
        }
      />

      <Metric
        label="Context Awareness"
        value={had_basket_context ? 'Yes' : 'No'}
        description={had_basket_context
          ? `Extracted with awareness of ${context_blocks_count} existing blocks`
          : 'First extraction in basket - no prior context'
        }
      />
    </QualityMetrics>

    {/* Show extraction_quality_metrics entry */}
    <ExtractionDetails>
      <Label>Extraction Run Details</Label>
      <Details>
        Agent Version: {agent_version}
        Method: {extraction_method}
        Processing Time: {processing_time_ms}ms
        Blocks Created (same run): {blocks_created}
        Context Items Created: {context_items_created}
      </Details>
    </ExtractionDetails>
  </TabPanel>

  {/* Tab: Anchor (if anchored) */}
  {isAnchored && (
    <TabPanel name="Anchor">
      <AnchorDetails anchor={anchor}>
        <Field label="Anchor Label" value={anchor.label} />
        <Field label="Status" value={anchor.status} />
        <Field label="Last Refreshed" value={formatDate(anchor.last_refreshed_at)} />
        <Field label="Refresh Policy" value={anchor.refresh_policy} />

        <Actions>
          <Button onClick={() => refreshAnchor(anchor.id)}>
            <RefreshIcon /> Refresh Now
          </Button>
          <Button onClick={() => unlinkAnchor(anchor.id)} variant="danger">
            <UnlinkIcon /> Unlink Anchor
          </Button>
          <Button onClick={() => navigate(`/memory#anchor-${anchor.id}`)}>
            <LinkIcon /> Manage in Memory Page
          </Button>
        </Actions>
      </AnchorDetails>
    </TabPanel>
  )}

  {/* Footer actions */}
  <ModalFooter>
    {!isAnchored && (
      <Button onClick={() => createAnchorFromSubstrate(substrate.id)}>
        <AnchorIcon /> Convert to Anchor
      </Button>
    )}
    <Button onClick={() => archiveSubstrate(substrate.id)} variant="secondary">
      <ArchiveIcon /> Archive
    </Button>
    <Button onClick={closeModal} variant="ghost">
      Close
    </Button>
  </ModalFooter>
</SubstrateDetailModal>
```

**Key Enhancements:**
- ✅ **Provenance tab**: Full chain from upload → extraction → approval
- ✅ **Usage tab**: Timeline of where/when this substrate was used
- ✅ **Quality tab**: Extraction metrics, deduplication info, context awareness
- ✅ **Anchor integration**: If substrate is anchored, show anchor management UI

---

### 4. Governance Page Enhancements

**Current State:**
- Shows proposals for review
- Missing context-aware insights

**Enhancements Needed:**

```tsx
<GovernancePage>
  {/* Header */}
  <Header>
    <Title>Change Requests</Title>
    <Description>
      Review substrate proposals generated from your uploads.
      Context-aware extraction prevents duplicates and links to existing knowledge.
    </Description>
  </Header>

  {/* Stats */}
  <StatsBar>
    <Stat>{pendingCount} Pending</Stat>
    <Stat>{autoApprovedToday} Auto-approved Today</Stat> {/* NEW */}
    <Stat>{deduplicatedToday} Deduplicated</Stat> {/* NEW: How many avoided duplicates */}
  </StatsBar>

  {/* Proposal list */}
  <ProposalList>
    {proposals.map(proposal => (
      <ProposalCard key={proposal.id}>
        <ProposalHeader>
          <Title>{proposal.title}</Title>
          <ProposalKindBadge>{proposal.kind}</ProposalKindBadge> {/* Extraction, Edit, Merge */}
          <ConfidenceBadge>{proposal.confidence}</ConfidenceBadge>
        </ProposalHeader>

        {/* NEW: Context-aware insights */}
        <ContextInsights>
          {proposal.deduplication_info && (
            <Insight icon="FilterIcon" variant="info">
              Deduplicated: {proposal.deduplication_info.similar_blocks_count} similar blocks already exist.
              Only extracting NEW information.
            </Insight>
          )}

          {proposal.basket_context_used && (
            <Insight icon="BrainIcon" variant="success">
              Context-aware: Extracted with awareness of {proposal.basket_context_used.blocks_count} existing blocks
              and {proposal.basket_context_used.entities_count} entities.
            </Insight>
          )}

          {proposal.staleness_triggered && (
            <Insight icon="ClockIcon" variant="warning">
              Staleness update: This proposal updates stale substrate from {formatDate(proposal.staleness_triggered.original_date)}.
            </Insight>
          )}
        </ContextInsights>

        {/* Operations */}
        <OperationsList>
          {proposal.ops.map(op => (
            <Operation key={op.id}>
              <OperationTypeBadge>{op.type}</OperationTypeBadge>
              <OperationSummary>
                {op.type === 'CreateBlock' && `Create block: ${op.data.title}`}
                {op.type === 'UpdateBlock' && `Update block: ${op.data.title}`}
                {op.type === 'MergeBlocks' && `Merge ${op.data.source_ids.length} blocks`}
              </OperationSummary>

              {/* NEW: Show why this operation matters */}
              <OperationRationale>
                {op.rationale || 'Extracted from recent upload'}
              </OperationRationale>

              {/* NEW: Show extraction quality */}
              <OperationMetrics>
                <Metric label="Confidence" value={op.data.confidence} />
                {op.data.was_deduplicated && (
                  <Badge variant="info">Deduplicated from similar content</Badge>
                )}
              </OperationMetrics>
            </Operation>
          ))}
        </OperationsList>

        {/* Actions */}
        <ProposalActions>
          <Button onClick={() => approveProposal(proposal.id)} variant="success">
            <CheckIcon /> Approve
          </Button>
          <Button onClick={() => rejectProposal(proposal.id)} variant="danger">
            <XIcon /> Reject
          </Button>
          <Button onClick={() => viewDetails(proposal.id)} variant="ghost">
            View Full Details
          </Button>
        </ProposalActions>
      </ProposalCard>
    ))}
  </ProposalList>
</GovernancePage>
```

**Key Enhancements:**
- ✅ **Context insights**: Show when deduplication prevented duplicates
- ✅ **Operation rationale**: Explain why each change is proposed
- ✅ **Extraction quality**: Display confidence and deduplication status
- ✅ **Staleness indicators**: Highlight when proposals update stale substrate

---

## Implementation Phases

### Phase 1: Uploads Page Polish (1-2 days)
- ✅ Enhance timeline uploads panel with file manager UX
- ✅ Add extraction summary to detail panel
- ✅ Bridge to building-blocks (click "View Extracted" filters by dump)

### Phase 2: Building Blocks Refactor (3-4 days)
- ✅ Split into Anchored / Free / Entities sections
- ✅ Add filtering by usefulness, staleness, anchored status
- ✅ Integrate anchor actions (convert to anchor, manage anchor)
- ✅ Update stats bar with context-aware metrics

### Phase 3: Enhanced Substrate Modal (2-3 days)
- ✅ Add Provenance tab (upload → extraction → approval chain)
- ✅ Add Usage tab (timeline of references)
- ✅ Add Quality tab (extraction metrics, deduplication info)
- ✅ Integrate anchor management if substrate is anchored

### Phase 4: Governance Enhancements (2-3 days)
- ✅ Add context-aware insights to proposals
- ✅ Show deduplication rationale
- ✅ Display extraction quality metrics
- ✅ Highlight staleness-triggered updates

### Phase 5: Integration & Testing (2-3 days)
- ✅ End-to-end user flows: Upload → Extract → Review → Manage
- ✅ Ensure anchor registry deeply integrated (not isolated)
- ✅ Verify all new metrics are displayed (usefulness, staleness, quality)
- ✅ Polish UI/UX based on user testing

---

## Success Criteria

### User Experience
- [ ] Users understand "Uploads" = raw files (familiar)
- [ ] Users understand "Building Blocks" = extracted knowledge (manageable)
- [ ] Users can convert free blocks → anchors in one click
- [ ] Users see usefulness & staleness at a glance
- [ ] Users understand governance proposals (context-aware insights)

### Technical
- [ ] All new substrate quality metrics displayed (usefulness, staleness)
- [ ] Provenance chain visible (upload → extraction → approval)
- [ ] Anchor registry integrated into building-blocks workflow (not isolated)
- [ ] Governance shows deduplication insights
- [ ] No information loss (all existing data still accessible)

### Performance
- [ ] Building-blocks page loads in <2s with 100+ blocks
- [ ] Modal opens instantly (<100ms)
- [ ] Search/filter responsive (<500ms)

---

## Next Steps

**Would you like me to:**
1. **Start with Phase 1** (Polish Uploads page)?
2. **Jump to Phase 2** (Refactor Building Blocks)?
3. **Create wire frames** for the new layouts?
4. **Audit anchor registry integration** first?

Let me know where you'd like to begin!
