# Work Recipes - Integrated Architecture Implementation

**Date**: 2025-11-23
**Status**: ✅ BACKEND COMPLETE - Frontend Implementation Starting
**Commit**: 69070103 (pushed to main)

**Architecture**: Recipes-Only, Fully Integrated into Work Requests

---

## ✅ COMPLETED

### 1. Database Schema & Migration
**File**: `supabase/migrations/20251123_work_recipes_dynamic_scaffolding.sql`

- Created `work_recipes` table with full JSONB schema for dynamic execution
- Extended `work_requests` table with recipe linkage columns:
  - `recipe_id` (UUID, references work_recipes)
  - `recipe_parameters` (JSONB, validated user parameters)
  - `reference_asset_ids` (UUID[], user-uploaded context assets)
- **Migration Applied Successfully** (1 active recipe seeded)

**Seed Data**: "Executive Summary Deck" recipe
- Parameterized: `slide_count` (3-7 range), `focus_area` (optional text)
- Output: PPTX format with validation rules
- Estimated: 3-6 minutes, $3-5

### 2. RecipeLoader Service
**File**: `work-platform/api/src/services/recipe_loader.py`

**Features**:
- Load recipes by ID or slug
- Validate user parameters against configurable_parameters schema
- Support for parameter types: range, text, multi-select
- Generate execution context with parameter interpolation
- List active recipes for frontend

**Key Methods**:
```python
loader = RecipeLoader()
recipe = await loader.load_recipe(slug="executive-summary-deck")
validated = loader.validate_parameters(recipe, user_parameters)
context = loader.generate_execution_context(recipe, validated)
recipes = await loader.list_active_recipes(agent_type="reporting")
```

### 3. Recipe Discovery API
**File**: `work-platform/api/src/app/routes/work_recipes.py`

**Endpoints** (Discovery Only):
1. `GET /api/work/recipes` - List active recipes (with filters)
2. `GET /api/work/recipes/{slug}` - Get recipe details

**Purpose**: Frontend recipe gallery and parameter form generation

### 4. Integrated Workflow Endpoint
**File**: `work-platform/api/src/app/routes/workflow_reporting.py`

**Endpoint**: `POST /api/work/reporting/execute`

**Execution Flow** (Recipe-Driven):
1. Load recipe by ID/slug + validate parameters (RecipeLoader)
2. Generate execution context from recipe template
3. Create work_request with recipe linkage
4. Load WorkBundle (substrate_blocks + reference_assets)
5. Execute ReportingAgentSDK.execute_recipe() with context
6. Return structured outputs

**Request Format**:
```json
{
  "basket_id": "uuid",
  "task_description": "Brief description",
  "recipe_id": "executive-summary-deck",
  "recipe_parameters": {
    "slide_count": 5,
    "focus_area": "Q4 highlights"
  },
  "reference_asset_ids": []
}
```

### 5. ReportingAgentSDK Integration ✅
**File**: `work-platform/api/src/agents_sdk/reporting_agent_sdk.py`

**Implemented**: `execute_recipe()` method

**Purpose**: Executes recipe-driven report generation with parameter-interpolated instructions

---

## 🎯 NEXT: FRONTEND IMPLEMENTATION

**Architecture Decision**: Recipes-Only, No Free-Form Path

### Frontend Implementation Plan

**1. Overview Page Redesign**
- Remove individual action buttons from agent cards
- Add single top-right "+ New Work" button
- Purpose: Simplify entry point, direct users to recipe gallery

**2. Recipe Gallery Page**
- **Route**: `/work/new` (opened by "+ New Work" button)
- **API**: `GET /api/work/recipes`
- **Display**: Recipe cards with:
  - Recipe name, description, category
  - Estimated duration & cost
  - Agent type icon
  - "Configure" button
- **Filters**: By agent_type, category

**3. Recipe Configuration Page**
- **Route**: `/work/new/recipe/:slug`
- **API**: `GET /api/work/recipes/:slug` (fetch recipe details)
- **Dynamic Parameter Form**: Render inputs based on `configurable_parameters`:
  - `type: "range"` → Slider with min/max labels
  - `type: "text"` → Text input with character counter
  - `type: "multi-select"` → Checkbox group
- **Optional**: Reference asset upload (drag-drop)
- **Submit**: `POST /api/work/reporting/execute` with recipe_id + parameters

**4. Execution & Results**
- Show real-time work_ticket status
- Display work_outputs when complete
- Link to work request history

---

## 📦 FILES CREATED/MODIFIED

**Backend Complete**:
1. `supabase/migrations/20251123_work_recipes_dynamic_scaffolding.sql` - Database schema ✅
2. `work-platform/api/src/services/recipe_loader.py` - Recipe validation & context generation ✅
3. `work-platform/api/src/app/routes/work_recipes.py` - Discovery API (streamlined to 132 lines) ✅
4. `work-platform/api/src/app/routes/workflow_reporting.py` - Integrated execution endpoint ✅
5. `work-platform/api/src/agents_sdk/reporting_agent_sdk.py` - execute_recipe() method ✅
6. `work-platform/api/src/app/agent_server.py` - Router registration ✅

**Frontend TODO**:
1. Recipe gallery component
2. Dynamic parameter form component
3. Overview page redesign (single "+ New Work" button)
4. Recipe execution flow integration

---

## 💡 ARCHITECTURE DECISIONS

**Why Integrated (Not Separate Domain)**:
- ✅ Single execution path = simpler mental model
- ✅ Recipes enhance workflows, don't replace them
- ✅ Less code to maintain (no duplicate logic)
- ✅ Recipe-only commitment = clear user experience

**Why Recipes-Only (No Free-Form Path)**:
- ✅ Bounded costs & time = predictable user experience
- ✅ Quality floor via validation
- ✅ Easier to scale (template approach)
- ✅ Room to grow = add more recipes over time

**Why JSONB Over Separate Tables**:
- ✅ Faster iteration (no migration per recipe tweak)
- ✅ Flexible schema evolution
- ✅ Single source of truth per recipe

**Why Recipe-First UX (Not Agent-First)**:
- ✅ User selects WHAT they want (outcome-focused)
- ✅ System determines HOW to execute (agent abstracted)
- ✅ Future: Multi-agent recipes (research → reporting flow)
