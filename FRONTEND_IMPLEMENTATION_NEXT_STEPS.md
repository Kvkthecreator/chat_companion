# Frontend Implementation: Next Steps

**Status**: Backend Complete ✅ | Frontend Ready to Start 📋
**Date**: 2025-11-23

---

## Summary

The work recipes backend is fully implemented and tested. This document provides the exact steps to implement the frontend components for the recipes-only workflow.

### Architecture Confirmed:
- **Single Entry Point**: "+ New Work" button (top-right of dashboard)
- **No Free-Form Path**: Users must select a recipe
- **Flow**: Gallery → Configuration → Execution → Results

---

## Implementation Sequence

### Phase 1: Shared Components (Start Here)

#### 1.1 Create Types Definition
**File**: `work-platform/web/lib/types/recipes.ts`

```typescript
export interface Recipe {
  id: string
  slug: string
  name: string
  description: string
  category: string
  agent_type: 'research' | 'content' | 'reporting'
  deliverable_intent: {
    purpose: string
    audience: string
    expected_outcome: string
  }
  configurable_parameters: Record<string, ParameterSchema>
  estimated_duration_seconds: [number, number]
  estimated_cost_cents: [number, number]
}

export interface ParameterSchema {
  type: 'range' | 'text' | 'multi-select'
  label: string
  optional?: boolean
  default?: any
  min?: number  // for range
  max?: number  // for range
  max_length?: number  // for text
  options?: string[]  // for multi-select
}

export interface RecipeExecutionRequest {
  basket_id: string
  task_description: string
  recipe_id: string
  recipe_parameters: Record<string, any>
  reference_asset_ids?: string[]
}

export interface RecipeExecutionResponse {
  work_request_id: string
  work_ticket_id: string
  agent_session_id: string
  status: 'completed' | 'failed'
  outputs: Array<{
    id: string
    content: any
    format: string
    metadata: object
  }>
  execution_time_ms: number
  message: string
  recipe_used: string
}
```

#### 1.2 Create ParameterInput Component
**File**: `work-platform/web/components/recipes/ParameterInput.tsx`

```typescript
'use client'

import { Label } from '@/components/ui/Label'
import type { ParameterSchema } from '@/lib/types/recipes'

interface ParameterInputProps {
  name: string
  schema: ParameterSchema
  value: any
  onChange: (value: any) => void
  error?: string
}

export function ParameterInput({ name, schema, value, onChange, error }: ParameterInputProps) {
  const renderInput = () => {
    switch (schema.type) {
      case 'range':
        return (
          <div className="space-y-2">
            <input
              type="range"
              min={schema.min}
              max={schema.max}
              value={value ?? schema.default ?? schema.min}
              onChange={(e) => onChange(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-sm text-gray-600">
              <span>{schema.min}</span>
              <strong className="text-gray-900">{value ?? schema.default ?? schema.min}</strong>
              <span>{schema.max}</span>
            </div>
          </div>
        )

      case 'text':
        return (
          <div className="space-y-1">
            <input
              type="text"
              value={value ?? schema.default ?? ''}
              onChange={(e) => onChange(e.target.value)}
              maxLength={schema.max_length}
              placeholder={schema.optional ? 'Optional' : 'Required'}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {schema.max_length && (
              <div className="text-xs text-gray-500 text-right">
                {(value?.length ?? 0)} / {schema.max_length}
              </div>
            )}
          </div>
        )

      case 'multi-select':
        return (
          <div className="space-y-2">
            {schema.options?.map((option) => (
              <label key={option} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={value?.includes(option) ?? false}
                  onChange={(e) => {
                    const currentValues = value ?? []
                    if (e.target.checked) {
                      onChange([...currentValues, option])
                    } else {
                      onChange(currentValues.filter((v: string) => v !== option))
                    }
                  }}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">{option}</span>
              </label>
            ))}
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="space-y-2">
      <Label>
        {schema.label}
        {!schema.optional && <span className="text-red-500 ml-1">*</span>}
      </Label>
      {renderInput()}
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  )
}
```

### Phase 2: Recipe Gallery Page

#### 2.1 Create Recipe Card Component
**File**: `work-platform/web/components/recipes/RecipeCard.tsx`

```typescript
'use client'

import Link from 'next/link'
import { Clock, DollarSign } from 'lucide-react'
import type { Recipe } from '@/lib/types/recipes'

interface RecipeCardProps {
  recipe: Recipe
}

export function RecipeCard({ recipe }: RecipeCardProps) {
  const [minDuration, maxDuration] = recipe.estimated_duration_seconds
  const [minCost, maxCost] = recipe.estimated_cost_cents

  const formatDuration = (seconds: number) => {
    const minutes = Math.ceil(seconds / 60)
    return `${minutes}min`
  }

  const formatCost = (cents: number) => {
    return `$${(cents / 100).toFixed(2)}`
  }

  return (
    <Link
      href={`/work/new/${recipe.slug}`}
      className="block p-6 bg-white border border-gray-200 rounded-lg hover:shadow-lg transition-shadow"
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900">{recipe.name}</h3>
        <span className="px-2 py-1 text-xs font-medium text-blue-600 bg-blue-50 rounded">
          {recipe.category}
        </span>
      </div>

      <p className="text-sm text-gray-600 mb-4">{recipe.description}</p>

      <div className="mb-4 p-3 bg-gray-50 rounded">
        <p className="text-xs font-medium text-gray-500 mb-1">Purpose</p>
        <p className="text-sm text-gray-700">{recipe.deliverable_intent.purpose}</p>
      </div>

      <div className="flex items-center justify-between text-sm text-gray-600">
        <div className="flex items-center space-x-1">
          <Clock className="w-4 h-4" />
          <span>{formatDuration(minDuration)}-{formatDuration(maxDuration)}</span>
        </div>
        <div className="flex items-center space-x-1">
          <DollarSign className="w-4 h-4" />
          <span>{formatCost(minCost)}-{formatCost(maxCost)}</span>
        </div>
      </div>
    </Link>
  )
}
```

#### 2.2 Create Recipe Gallery Page
**File**: `work-platform/web/app/work/new/page.tsx`

```typescript
'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { RecipeCard } from '@/components/recipes/RecipeCard'
import type { Recipe } from '@/lib/types/recipes'

export default function RecipeGalleryPage() {
  const [agentTypeFilter, setAgentTypeFilter] = useState<string | null>(null)

  const { data: recipes, isLoading } = useQuery({
    queryKey: ['recipes', { agent_type: agentTypeFilter }],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (agentTypeFilter) params.append('agent_type', agentTypeFilter)

      const response = await fetch(`/api/work/recipes?${params}`)
      if (!response.ok) throw new Error('Failed to fetch recipes')
      return response.json() as Promise<Recipe[]>
    }
  })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Choose a Work Recipe</h1>
        <p className="text-gray-600">Select a template to create structured work deliverables</p>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Type</label>
        <select
          value={agentTypeFilter ?? ''}
          onChange={(e) => setAgentTypeFilter(e.target.value || null)}
          className="px-3 py-2 border border-gray-300 rounded-md"
        >
          <option value="">All Types</option>
          <option value="research">Research</option>
          <option value="content">Content</option>
          <option value="reporting">Reporting</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-gray-500">Loading recipes...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recipes?.map((recipe) => (
            <RecipeCard key={recipe.id} recipe={recipe} />
          ))}
        </div>
      )}
    </div>
  )
}
```

### Phase 3: Recipe Configuration Page

**File**: `work-platform/web/app/work/new/[slug]/page.tsx`

```typescript
'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { ParameterInput } from '@/components/recipes/ParameterInput'
import type { Recipe } from '@/lib/types/recipes'

export default function RecipeConfigurationPage() {
  const params = useParams()
  const router = useRouter()
  const slug = params?.slug as string

  const [parameters, setParameters] = useState<Record<string, any>>({})
  const [taskDescription, setTaskDescription] = useState('')

  // Fetch recipe details
  const { data: recipe, isLoading } = useQuery({
    queryKey: ['recipe', slug],
    queryFn: async () => {
      const response = await fetch(`/api/work/recipes/${slug}`)
      if (!response.ok) throw new Error('Failed to fetch recipe')
      return response.json() as Promise<Recipe>
    }
  })

  // Execute recipe mutation
  const executeMutation = useMutation({
    mutationFn: async () => {
      // TODO: Get actual basket_id from context
      const basketId = 'YOUR_BASKET_ID' // Replace with actual basket ID from context

      const response = await fetch('/api/work/reporting/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          basket_id: basketId,
          task_description: taskDescription || recipe?.name,
          recipe_id: slug,
          recipe_parameters: parameters,
          reference_asset_ids: []
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Execution failed')
      }

      return response.json()
    },
    onSuccess: (data) => {
      toast.success('Recipe executed successfully!')
      router.push(`/work/results/${data.work_request_id}`)
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  if (isLoading) return <div className="p-8">Loading...</div>
  if (!recipe) return <div className="p-8">Recipe not found</div>

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-2">{recipe.name}</h1>
      <p className="text-gray-600 mb-8">{recipe.description}</p>

      <form onSubmit={(e) => { e.preventDefault(); executeMutation.mutate() }} className="space-y-6">
        {Object.entries(recipe.configurable_parameters).map(([name, schema]) => (
          <ParameterInput
            key={name}
            name={name}
            schema={schema}
            value={parameters[name]}
            onChange={(value) => setParameters(prev => ({ ...prev, [name]: value }))}
          />
        ))}

        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Task Description (optional)
          </label>
          <input
            type="text"
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
            placeholder={`e.g., ${recipe.name} for Q4 review`}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <button
          type="submit"
          disabled={executeMutation.isPending}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {executeMutation.isPending ? 'Executing...' : 'Execute Recipe'}
        </button>
      </form>
    </div>
  )
}
```

### Phase 4: Dashboard Integration

**File**: `work-platform/web/app/dashboard/page.tsx` (Update)

Add "+ New Work" button to the dashboard header:

```typescript
// Add import at top
import Link from 'next/link'
import { Plus } from 'lucide-react'

// In the JSX, add this near the top of the page (before the main content):
<div className="flex justify-between items-center mb-6">
  <h1 className="text-2xl font-bold">Dashboard</h1>
  <Link
    href="/work/new"
    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
  >
    <Plus className="w-4 h-4 mr-2" />
    New Work
  </Link>
</div>
```

---

## Testing Checklist

- [ ] Recipe gallery loads and displays recipes
- [ ] Filter by agent_type works
- [ ] Recipe cards navigate to configuration page
- [ ] Configuration page loads recipe details
- [ ] Parameter inputs render correctly (range, text, multi-select)
- [ ] Form validation works
- [ ] Recipe execution succeeds
- [ ] Navigation to results page works
- [ ] "+ New Work" button appears on dashboard
- [ ] Button navigates to recipe gallery

---

## API Proxy Setup (If Needed)

If the API is on a different domain, create Next.js API routes to proxy requests:

**File**: `work-platform/web/app/api/work/recipes/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:10000'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const agent_type = searchParams.get('agent_type')

  const params = new URLSearchParams()
  if (agent_type) params.append('agent_type', agent_type)

  const response = await fetch(`${API_URL}/api/work/recipes?${params}`)
  const data = await response.json()

  return NextResponse.json(data)
}
```

---

## Next Actions

1. **Create type definitions** (recipes.ts)
2. **Implement ParameterInput** component
3. **Create RecipeCard** component
4. **Build Recipe Gallery** page
5. **Build Recipe Configuration** page
6. **Update Dashboard** with "+ New Work" button
7. **Test end-to-end flow**
8. **Deploy and validate**

**Estimated Time**: 3-4 hours for complete frontend implementation

---

## Notes

- All backend APIs are ready and tested
- Use existing UI components from `@/components/ui/*`
- Follow existing patterns in dashboard for consistency
- Parameter validation happens on backend (RecipeLoader)
- Toast notifications use `sonner` library
- Query state management uses `@tanstack/react-query`

