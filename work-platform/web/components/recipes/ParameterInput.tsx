'use client'

import { useState, useId, type KeyboardEvent } from 'react'
import { Label } from '@/components/ui/Label'
import { X } from 'lucide-react'
import type { ParameterSchema } from '@/lib/types/recipes'

interface ParameterInputProps {
  name: string
  schema: ParameterSchema
  value: any
  onChange: (value: any) => void
  error?: string
}

export function ParameterInput({ name, schema, value, onChange, error }: ParameterInputProps) {
  const [tagInput, setTagInput] = useState('')
  const inputId = useId()

  const handleTagKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      const newTag = tagInput.trim()
      if (newTag && !(value ?? []).includes(newTag)) {
        onChange([...(value ?? []), newTag])
      }
      setTagInput('')
    } else if (e.key === 'Backspace' && !tagInput && value?.length > 0) {
      onChange(value.slice(0, -1))
    }
  }

  const removeTag = (tagToRemove: string) => {
    onChange((value ?? []).filter((t: string) => t !== tagToRemove))
  }

  const renderInput = () => {
    switch (schema.type) {
      case 'range':
        return (
          <div className="space-y-2">
            <input
              id={inputId}
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
              id={inputId}
              type="text"
              value={value ?? schema.default ?? ''}
              onChange={(e) => onChange(e.target.value)}
              maxLength={schema.max_length}
              placeholder={schema.placeholder || (schema.optional ? 'Optional' : 'Required')}
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
      case 'multiselect':
        return (
          <div role="group" aria-labelledby={inputId} className="space-y-2">
            {schema.options?.map((option, idx) => {
              const optionId = `${inputId}-option-${idx}`
              return (
                <label key={option} htmlFor={optionId} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    id={optionId}
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
              )
            })}
          </div>
        )

      case 'tags':
        return (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2 p-2 border border-gray-300 rounded-md min-h-[42px] dark:border-gray-600 dark:bg-gray-800">
              {(value ?? []).map((tag: string) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 px-2 py-1 text-sm bg-blue-100 text-blue-800 rounded dark:bg-blue-900/30 dark:text-blue-400"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeTag(tag)}
                    className="hover:text-blue-600 dark:hover:text-blue-300"
                    aria-label={`Remove ${tag}`}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
              <input
                id={inputId}
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleTagKeyDown}
                placeholder={value?.length > 0 ? '' : (schema.placeholder || 'Type and press Enter')}
                className="flex-1 min-w-[120px] outline-none bg-transparent text-sm dark:text-white"
              />
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Press Enter or comma to add tags
            </p>
          </div>
        )

      default:
        return (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Unsupported parameter type: {schema.type}
          </p>
        )
    }
  }

  // For multiselect, the label is referenced by aria-labelledby so we need an id on it
  const isMultiselect = schema.type === 'multi-select' || schema.type === 'multiselect'

  return (
    <div className="space-y-2">
      <Label htmlFor={isMultiselect ? undefined : inputId} id={isMultiselect ? inputId : undefined}>
        {schema.label}
        {!schema.optional && <span className="text-red-500 ml-1">*</span>}
      </Label>
      {renderInput()}
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  )
}
