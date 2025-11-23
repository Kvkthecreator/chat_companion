'use client'

import Link from 'next/link'
import { Clock, DollarSign } from 'lucide-react'
import type { Recipe } from '@/lib/types/recipes'

interface RecipeCardProps {
  recipe: Recipe
  projectId: string
  agentType: string
}

export function RecipeCard({ recipe, projectId, agentType }: RecipeCardProps) {
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
      href={`/projects/${projectId}/agents/${agentType}/recipes/${recipe.slug}`}
      className="block p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-lg transition-shadow"
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{recipe.name}</h3>
        <span className="px-2 py-1 text-xs font-medium text-blue-600 bg-blue-50 dark:bg-blue-900/30 dark:text-blue-400 rounded">
          {recipe.category}
        </span>
      </div>

      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{recipe.description}</p>

      <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-900/50 rounded">
        <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Purpose</p>
        <p className="text-sm text-gray-700 dark:text-gray-300">{recipe.deliverable_intent.purpose}</p>
      </div>

      <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
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
