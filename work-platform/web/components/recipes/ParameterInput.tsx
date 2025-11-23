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
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
            />
            <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
              <span>{schema.min}</span>
              <strong className="text-gray-900 dark:text-gray-100">{value ?? schema.default ?? schema.min}</strong>
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            />
            {schema.max_length && (
              <div className="text-xs text-gray-500 text-right dark:text-gray-400">
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
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">{option}</span>
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
