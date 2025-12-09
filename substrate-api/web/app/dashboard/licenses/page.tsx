'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { workspaces, catalogs, entities, licenses, type Workspace, type Catalog, type RightsEntity, type License } from '@/lib/api'
import Link from 'next/link'

type LicenseWithContext = License & {
  entity_title: string
  catalog_name: string
  workspace_name: string
}

export default function LicensesPage() {
  const [allLicenses, setLicenses] = useState<LicenseWithContext[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const supabase = createClient()

  useEffect(() => {
    async function load() {
      try {
        const { data: { session } } = await supabase.auth.getSession()
        if (!session) return

        const wsResult = await workspaces.list(session.access_token)
        const allLicenseData: LicenseWithContext[] = []

        for (const ws of wsResult.workspaces) {
          try {
            const catResult = await catalogs.list(ws.id, session.access_token)
            for (const cat of catResult.catalogs) {
              try {
                const entResult = await entities.list(cat.id, session.access_token)
                for (const ent of entResult.entities) {
                  try {
                    const licResult = await licenses.listForEntity(ent.id, session.access_token)
                    for (const lic of licResult.licenses) {
                      allLicenseData.push({
                        ...lic,
                        entity_title: ent.title,
                        catalog_name: cat.name,
                        workspace_name: ws.name,
                      })
                    }
                  } catch {
                    // Entity may not have licenses
                  }
                }
              } catch {
                // Catalog may not have entities
              }
            }
          } catch {
            // Workspace may not have catalogs
          }
        }

        setLicenses(allLicenseData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load licenses')
      } finally {
        setIsLoading(false)
      }
    }
    load()
  }, [])

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">Active</span>
      case 'expired':
        return <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">Expired</span>
      case 'revoked':
        return <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded">Revoked</span>
      case 'pending':
        return <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">Pending</span>
      default:
        return <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">{status}</span>
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
            <Link href="/dashboard" className="hover:text-gray-700">Dashboard</Link>
            <span>/</span>
            <span className="text-gray-900">Licenses</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Licenses</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading && (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {!isLoading && !error && allLicenses.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-2">No licenses yet</h3>
            <p className="text-gray-500 mb-4">Licenses will appear here when you grant access to your IP.</p>
            <Link
              href="/dashboard/workspaces"
              className="inline-block px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800"
            >
              Go to Workspaces
            </Link>
          </div>
        )}

        {!isLoading && allLicenses.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 divide-y">
            {allLicenses.map((license) => (
              <div key={license.id} className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      {getStatusBadge(license.status)}
                    </div>
                    <h3 className="font-medium text-gray-900">{license.entity_title}</h3>
                    <p className="text-sm text-gray-500 mt-1">
                      {license.workspace_name} / {license.catalog_name}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                      <span>Effective: {new Date(license.effective_date).toLocaleDateString()}</span>
                      {license.expiration_date && (
                        <span>Expires: {new Date(license.expiration_date).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
