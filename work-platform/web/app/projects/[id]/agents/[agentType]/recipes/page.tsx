'use client'

import { use } from 'react'
import { useQuery } from '@tanstack/react-query'
import { RecipeCard } from '@/components/recipes/RecipeCard'
import type { Recipe } from '@/lib/types/recipes'
import { Badge } from '@/components/ui/Badge'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'

interface PageProps {
  params: Promise<{ id: string; agentType: string }>
}

export default function AgentRecipeGalleryPage({ params }: PageProps) {
  const { id: projectId, agentType } = use(params)

  const { data: recipes, isLoading } = useQuery({
    queryKey: ['recipes', agentType],
    queryFn: async () => {
      const response = await fetch(`/api/work/recipes?agent_type=${agentType}`)
      if (!response.ok) throw new Error('Failed to fetch recipes')
      return response.json() as Promise<Recipe[]>
    }
  })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back button */}
      <Link
        href={`/projects/${projectId}/overview`}
        className="inline-flex items-center text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 mb-6"
      >
        <ArrowLeft className="w-4 h-4 mr-1" />
        Back to Project
      </Link>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white capitalize">
            {agentType} Recipes
          </h1>
          <Badge variant="secondary">{recipes?.length || 0} available</Badge>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          Select a recipe template for {agentType} work deliverables
        </p>
      </div>

      {/* Recipe grid */}
      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">Loading recipes...</p>
        </div>
      ) : recipes && recipes.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recipes.map((recipe) => (
            <RecipeCard
              key={recipe.id}
              recipe={recipe}
              projectId={projectId}
              agentType={agentType}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            No recipes available for {agentType}
          </p>
        </div>
      )}
    </div>
  )
}
