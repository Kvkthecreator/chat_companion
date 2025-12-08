# Integration Test Plan: Phase 4 - Agent Metadata Flow

**Date**: 2025-01-14
**Phase**: Phase 4 - Agent Execution with Enhanced Context
**Objective**: Validate end-to-end flow of reference_assets + agent_config → SDK agents

---

## Prerequisites

✅ **Infrastructure Ready**:
- Claude Agent SDK v0.2.0 (commit 0b25551) installed
- Substrate-API service running
- Work-platform API service running
- Supabase database with agent_catalog schemas populated
- Storage bucket configured

✅ **Code Complete**:
- `substrate_client.get_reference_assets()` implemented
- `SubstrateMemoryAdapter` enhanced with asset + config injection
- Agent factory functions updated to pass `project_id` + `work_session_id`
- Agent orchestration routes updated to query `project_id`
- SDK agents enhanced to consume metadata

---

## Test Scenarios

### Test 1: Asset Upload and Retrieval
**Objective**: Validate asset upload via Context → Assets page and retrieval via API

**Setup**:
```bash
# Create test project
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Project - Asset Flow",
    "basket_id": "<your_basket_id>",
    "workspace_id": "<your_workspace_id>"
  }'
```

**Steps**:
1. Navigate to Context → Assets page in UI
2. Upload a test asset (e.g., `brand_guidelines.pdf`)
   - **Asset Type**: `brand_voice`
   - **Agent Scope**: `content`
   - **Permanence**: `permanent`
3. Verify asset appears in assets list
4. Check database:
   ```sql
   SELECT id, file_name, asset_type, agent_scope, permanence, storage_path
   FROM reference_assets
   WHERE basket_id = '<your_basket_id>';
   ```
5. Verify storage bucket contains file

**Expected Result**:
- ✅ Asset uploaded successfully
- ✅ Database record created with correct metadata
- ✅ File exists in Supabase Storage at `<bucket_name>/<workspace_id>/<basket_id>/<asset_id>.<ext>`

---

### Test 2: Agent Config Setup
**Objective**: Validate agent config schema and data structure

**Steps**:
1. Check agent_catalog schemas are populated:
   ```sql
   SELECT agent_type, name, jsonb_pretty(config_schema)
   FROM agent_catalog
   ORDER BY agent_type;
   ```
2. Insert test config for content agent:
   ```sql
   INSERT INTO project_agents (project_id, agent_type, config, is_active)
   VALUES (
     '<your_project_id>',
     'content',
     '{
       "brand_voice": {
         "tone": "professional",
         "voice_guidelines": "We are a technical AI company. Be clear, concise, and helpful.",
         "avoid_keywords": ["disrupt", "synergy", "paradigm shift"]
       },
       "platforms": {
         "linkedin": {
           "enabled": true,
           "max_length": 3000,
           "include_hashtags": true,
           "hashtag_count": 3
         }
       },
       "content_rules": {
         "require_call_to_action": true,
         "emoji_usage": "minimal"
       }
     }'::jsonb,
     true
   );
   ```
3. Verify config is retrievable:
   ```sql
   SELECT config
   FROM project_agents
   WHERE project_id = '<your_project_id>'
     AND agent_type = 'content'
     AND is_active = true;
   ```

**Expected Result**:
- ✅ Agent config schemas exist for research, content, reporting
- ✅ Test config inserted successfully
- ✅ Config structure matches schema

---

### Test 3: Memory Adapter Asset Injection
**Objective**: Validate that `SubstrateMemoryAdapter.query()` injects assets into Context.metadata

**Setup**:
```python
# Create test script: test_memory_adapter.py
import asyncio
from adapters.memory_adapter import SubstrateMemoryAdapter

async def test_asset_injection():
    adapter = SubstrateMemoryAdapter(
        basket_id="<your_basket_id>",
        workspace_id="<your_workspace_id>",
        agent_type="content",
        project_id="<your_project_id>",
        work_session_id=None
    )

    contexts = await adapter.query("test query", limit=5)

    print(f"Retrieved {len(contexts)} contexts")

    # Check first context for metadata
    if contexts:
        first_context = contexts[0]
        print(f"First context content: {first_context.content[:50]}...")
        print(f"Metadata keys: {list(first_context.metadata.keys())}")

        if "reference_assets" in first_context.metadata:
            assets = first_context.metadata["reference_assets"]
            print(f"✅ Found {len(assets)} reference assets")
            for asset in assets:
                print(f"  - {asset['file_name']} ({asset['asset_type']})")

        if "agent_config" in first_context.metadata:
            config = first_context.metadata["agent_config"]
            print(f"✅ Found agent config with keys: {list(config.keys())}")

if __name__ == "__main__":
    asyncio.run(test_asset_injection())
```

**Steps**:
1. Run test script: `python3 test_memory_adapter.py`
2. Check logs for asset loading messages
3. Verify metadata is populated

**Expected Result**:
```
Retrieved 6 contexts
First context content: [AGENT EXECUTION CONTEXT]...
Metadata keys: ['reference_assets', 'agent_config']
✅ Found 1 reference assets
  - brand_guidelines.pdf (brand_voice)
✅ Found agent config with keys: ['brand_voice', 'platforms', 'content_rules']
```

---

### Test 4: End-to-End Agent Execution
**Objective**: Validate complete flow from API request → agent execution with metadata

**Setup**:
1. Ensure Test 1-3 are passing
2. Start work-platform API: `uvicorn app.main:app --reload`
3. Obtain valid JWT token

**Steps**:
1. **Trigger Content Agent**:
   ```bash
   curl -X POST http://localhost:8000/api/agents/run \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "basket_id": "<your_basket_id>",
       "agent_type": "content",
       "task_type": "create",
       "parameters": {
         "platform": "linkedin",
         "topic": "The benefits of Claude Agent SDK for AI development",
         "content_type": "article"
       }
     }'
   ```

2. **Monitor Logs** (key checkpoints):
   ```
   [INFO] Creating ContentCreatorAgent for basket <basket_id>
   [INFO] Initialized SubstrateMemoryAdapter with agent_type=content, project_id=<project_id>
   [INFO] Loaded 1 reference assets for content agent
   [INFO] Loaded config for content agent
   [INFO] Injected 1 reference assets into context
   [INFO] Injected agent config into context
   [DEBUG] Retrieved 6 context items from substrate
   [INFO] ContentCreatorAgent: Extracted metadata with 1 assets and config
   [INFO] ContentCreatorAgent: Using brand voice tone: professional
   [INFO] ContentCreatorAgent: Generated content with enhanced context
   ```

3. **Validate Response**:
   ```json
   {
     "status": "success",
     "agent_type": "content",
     "result": {
       "content": "...",
       "platform": "linkedin",
       "enhanced_with_metadata": true,
       "metadata_used": {
         "assets_count": 1,
         "config_applied": true
       }
     }
   }
   ```

4. **Check Generated Content**:
   - ✅ Content reflects brand voice guidelines
   - ✅ Avoids keywords from `avoid_keywords` list
   - ✅ Includes call-to-action (per config)
   - ✅ Uses minimal emojis (per config)
   - ✅ Stays within LinkedIn max_length limit

**Expected Result**:
- ✅ API request succeeds (200 OK)
- ✅ Logs show asset + config injection
- ✅ SDK agent consumes metadata
- ✅ Generated content uses brand guidelines
- ✅ Response includes `enhanced_with_metadata: true`

---

### Test 5: Graceful Degradation
**Objective**: Validate agents work without metadata (backward compatibility)

**Steps**:
1. **Test without project_id** (no config):
   ```bash
   # Create basket without project
   curl -X POST http://localhost:8000/api/agents/run \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "basket_id": "<basket_without_project>",
       "agent_type": "content",
       "task_type": "create",
       "parameters": {
         "platform": "twitter",
         "topic": "AI development update"
       }
     }'
   ```

2. **Check Logs**:
   ```
   [DEBUG] No project_id or agent_type, skipping config fetch
   [DEBUG] No agent_type specified, skipping asset fetch
   [INFO] ContentCreatorAgent: No metadata found, using defaults
   ```

3. **Verify Response**:
   ```json
   {
     "status": "success",
     "result": {
       "content": "...",
       "enhanced_with_metadata": false
     }
   }
   ```

**Expected Result**:
- ✅ Agent executes successfully without metadata
- ✅ No errors or crashes
- ✅ Uses SDK default configurations
- ✅ Response indicates no metadata used

---

### Test 6: Research Agent with Watchlist Config
**Objective**: Validate research agent uses config-driven monitoring

**Setup**:
```sql
INSERT INTO project_agents (project_id, agent_type, config, is_active)
VALUES (
  '<your_project_id>',
  'research',
  '{
    "watchlist": {
      "competitors": ["Anthropic", "OpenAI", "Google DeepMind"],
      "topics": ["Claude AI", "AI agents", "LLM orchestration"],
      "data_sources": ["web", "news", "social_media"]
    },
    "alert_rules": {
      "confidence_threshold": 0.8,
      "priority_keywords": ["breakthrough", "release", "acquisition"]
    },
    "output_preferences": {
      "synthesis_mode": "detailed",
      "include_sources": true
    }
  }'::jsonb,
  true
);
```

**Steps**:
1. Trigger research agent:
   ```bash
   curl -X POST http://localhost:8000/api/agents/run \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "basket_id": "<your_basket_id>",
       "agent_type": "research",
       "task_type": "monitor",
       "parameters": {}
     }'
   ```

2. **Check Logs**:
   ```
   [INFO] ResearchAgent: Extracted metadata with config
   [INFO] ResearchAgent: Monitoring 3 competitors, 3 topics
   [INFO] ResearchAgent: Using confidence threshold: 0.8
   [INFO] ResearchAgent: Priority keywords: ['breakthrough', 'release', 'acquisition']
   ```

3. **Validate Response** includes:
   - Findings for configured competitors
   - Monitoring data from configured sources
   - Detailed synthesis mode applied
   - Source links included

**Expected Result**:
- ✅ Research agent uses watchlist from config
- ✅ Alert rules applied (confidence threshold)
- ✅ Output preferences respected (detailed mode)

---

## Integration Checklist

### Phase 1+2: Reference Assets + Agent Configuration
- [ ] **Asset Upload**: Upload test assets via Context → Assets page
- [ ] **Asset Storage**: Verify files in Supabase Storage
- [ ] **Database Records**: Check `reference_assets` table
- [ ] **Agent Config**: Insert test configs for all 3 agent types
- [ ] **Config Schema**: Verify `agent_catalog.config_schema` populated

### Phase 3: Substrate Client Enhancement
- [ ] **get_reference_assets()**: Test asset fetching with filters
- [ ] **Signed URLs**: Verify signed URL generation
- [ ] **Error Handling**: Test graceful degradation when substrate-api unavailable

### Phase 4: Memory Adapter Enhancement
- [ ] **Asset Injection**: Verify assets in Context.metadata
- [ ] **Config Injection**: Verify config in Context.metadata
- [ ] **Caching**: Verify assets + config fetched once per session
- [ ] **Filtering**: Test agent_type, work_session_id, permanence filters

### Phase 4: Agent Factory + Orchestration
- [ ] **project_id Resolution**: Verify basket_id → project_id mapping
- [ ] **Factory Functions**: Test all 3 agent creation functions
- [ ] **Orchestration Routes**: Test all 3 agent execution routes

### SDK Integration
- [ ] **SDK Version**: Verify v0.2.0 installed
- [ ] **Metadata Consumption**: Verify agents extract metadata
- [ ] **Enhanced Prompts**: Verify agents use assets in prompts
- [ ] **Config Application**: Verify agents apply config settings

---

## Success Criteria

**Must Have** (Blocking):
1. ✅ Asset upload working end-to-end
2. ✅ Agent config stored and retrieved correctly
3. ✅ Memory adapter injects metadata into first Context
4. ✅ SDK agents extract and use metadata
5. ✅ Generated content reflects brand guidelines and config
6. ✅ Graceful degradation works (agents run without metadata)

**Should Have** (Important):
1. Proper error handling and logging at all layers
2. Signed URLs generated for all assets
3. Metadata caching prevents redundant fetches
4. All 3 agent types tested (research, content, reporting)

**Nice to Have** (Enhancement):
1. Performance metrics (latency, memory usage)
2. Work-session scoped asset testing
3. Multiple asset types per agent
4. Config versioning/migration testing

---

## Troubleshooting

### Common Issues

**Issue**: Assets not injected into Context.metadata
- **Check**: `agent_type` passed to `SubstrateMemoryAdapter`
- **Check**: Assets exist with matching `agent_scope`
- **Check**: Substrate-API service is running

**Issue**: Agent config not found
- **Check**: `project_id` passed to memory adapter
- **Check**: `project_agents` table has active config
- **Check**: Database connection working

**Issue**: SDK agents not using metadata
- **Check**: SDK version is v0.2.0
- **Check**: Agents call `extract_metadata_from_contexts()`
- **Check**: Logs show "Extracted metadata" messages

**Issue**: Signed URL generation fails
- **Check**: Supabase Storage bucket exists
- **Check**: Storage RLS policies allow access
- **Check**: File path correct: `<workspace_id>/<basket_id>/<asset_id>.<ext>`

---

## Next Steps (Post-Integration)

1. **Phase 7**: Work-request scoped asset upload (temporary assets)
2. **Phase 8**: Context page refinement for long-term assets
3. **Phase 9**: Asset lifecycle management service
4. **Phase 11**: Dynamic UI forms powered by `config_schema`
5. **Performance Optimization**: Asset prefetching, CDN caching
6. **Monitoring**: Add metrics for metadata usage, asset downloads

---

## References

- [Substrate Client Implementation](../../work-platform/api/src/clients/substrate_client.py)
- [Memory Adapter Implementation](../../work-platform/api/src/adapters/memory_adapter.py)
- [Agent Factory Implementation](../../work-platform/api/src/agents/factory.py)
- [Agent Orchestration Routes](../../work-platform/api/src/app/routes/agent_orchestration.py)
- [Agent Config Schemas Migration](../../supabase/migrations/20250114_agent_config_schemas_v1.sql)
- [SDK Metadata Pattern](https://github.com/Kvkthecreator/claude-agentsdk-opensource/blob/main/docs/METADATA_PATTERN.md)
