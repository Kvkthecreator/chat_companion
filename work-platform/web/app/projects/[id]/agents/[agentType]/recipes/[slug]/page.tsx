'use client'

import { use, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { ParameterInput } from '@/components/recipes/ParameterInput'
import type { Recipe } from '@/lib/types/recipes'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'

interface PageProps {
  params: Promise<{ id: string; agentType: string; slug: string }>
}

export default function RecipeConfigurationPage({ params }: PageProps) {
  const { id: projectId, agentType, slug } = use(params)
  const router = useRouter()

  const [parameters, setParameters] = useState<Record<string, any>>({})
  const [taskDescription, setTaskDescription] = useState('')

  // Fetch project to get basket_id
  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      const response = await fetch(`/api/projects/${projectId}`)
      if (!response.ok) throw new Error('Failed to fetch project')
      return response.json()
    }
  })

  // Fetch recipe details
  const { data: recipe, isLoading } = useQuery({
    queryKey: ['recipe', slug],
    queryFn: async () => {
      const response = await fetch(`/api/work/recipes/${slug}`)
      if (!response.ok) throw new Error('Failed to fetch recipe')
      return response.json() as Promise<Recipe>
    }
  })

  // Execute recipe mutation (agent-specific endpoint)
  const executeMutation = useMutation({
    mutationFn: async () => {
      if (!project?.basket_id) throw new Error('Project not loaded')

      const response = await fetch(`/api/work/${agentType}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          basket_id: project.basket_id,
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
      // Navigate to agent dashboard or work session
      router.push(`/projects/${projectId}/agents/${agentType}`)
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  if (isLoading) return <div className="p-8">Loading recipe...</div>
  if (!recipe) return <div className="p-8">Recipe not found</div>

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Back button */}
      <Link
        href={`/projects/${projectId}/agents/${agentType}/recipes`}
        className="inline-flex items-center text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 mb-6"
      >
        <ArrowLeft className="w-4 h-4 mr-1" />
        Back to Recipes
      </Link>

      {/* Recipe info card */}
      <Card className="p-6 mb-6">
        <h1 className="text-3xl font-bold mb-2 dark:text-white">{recipe.name}</h1>
        <p className="text-gray-600 dark:text-gray-400 mb-4">{recipe.description}</p>
        <div className="flex gap-2">
          <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 rounded capitalize">
            {agentType}
          </span>
          <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300 rounded">
            {recipe.category}
          </span>
        </div>
      </Card>

      {/* Configuration form */}
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
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Task Description (optional)
          </label>
          <input
            type="text"
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
            placeholder={`e.g., ${recipe.name} for Q4 review`}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <Button
          type="submit"
          disabled={executeMutation.isPending}
          className="w-full"
        >
          {executeMutation.isPending ? 'Executing...' : 'Execute Recipe'}
        </Button>
      </form>
    </div>
  )
}
