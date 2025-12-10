'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { entities, assets, jobs, type RightsEntity, type Asset, type ProcessingJob } from '@/lib/api'
import Link from 'next/link'
import { ProcessingStatus, EmbeddingStatusBadge } from '@/components/ProcessingStatus'

const ASSET_TYPES = [
  { value: 'audio_master', label: 'Audio Master' },
  { value: 'audio_preview', label: 'Audio Preview' },
  { value: 'audio_stem', label: 'Audio Stem' },
  { value: 'lyrics', label: 'Lyrics' },
  { value: 'sheet_music', label: 'Sheet Music' },
  { value: 'artwork', label: 'Artwork' },
  { value: 'photo', label: 'Photo' },
  { value: 'contract', label: 'Contract' },
  { value: 'certificate', label: 'Certificate' },
  { value: 'other', label: 'Other' },
]

export default function EntityDetailPage() {
  const params = useParams()
  const router = useRouter()
  const entityId = params.id as string
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [entity, setEntity] = useState<RightsEntity | null>(null)
  const [entityAssets, setAssets] = useState<Asset[]>([])
  const [entityJobs, setJobs] = useState<ProcessingJob[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [uploadType, setUploadType] = useState('audio_master')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<string | null>(null)
  const supabase = createClient()

  const loadData = useCallback(async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        setError('Not authenticated')
        setIsLoading(false)
        return
      }

      const [entityResult, assetsResult, jobsResult] = await Promise.all([
        entities.get(entityId, session.access_token),
        assets.list(entityId, session.access_token),
        jobs.listForEntity(entityId, session.access_token, { limit: 10 })
      ])

      setEntity(entityResult.entity)
      setAssets(assetsResult.assets)
      setJobs(jobsResult.jobs)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load entity')
    } finally {
      setIsLoading(false)
    }
  }, [entityId, supabase.auth])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setUploadProgress(`Uploading ${file.name}...`)
    setError(null)

    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        setError('Not authenticated')
        return
      }

      const result = await assets.upload(entityId, file, uploadType, session.access_token)
      setAssets([result.asset, ...entityAssets])
      setUploadProgress(null)

      // Trigger processing
      try {
        await assets.triggerProcessing(result.asset.id, session.access_token)
        // Refresh assets to get updated status
        const assetsResult = await assets.list(entityId, session.access_token)
        setAssets(assetsResult.assets)
      } catch {
        // Processing trigger failed, but upload succeeded
        console.warn('Asset uploaded but processing trigger failed')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
      setUploadProgress(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleTriggerEmbedding = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return

      await entities.triggerProcessing(entityId, session.access_token)

      // Refresh data
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trigger processing')
    }
  }

  const handleDownload = async (assetId: string) => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return

      const result = await assets.getDownloadUrl(assetId, session.access_token)
      window.open(result.url, '_blank')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get download URL')
    }
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin" />
      </div>
    )
  }

  if (!entity) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-slate-900">Entity not found</h2>
        <button onClick={() => router.back()} className="text-blue-600 hover:underline mt-2 inline-block">
          Go Back
        </button>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <button onClick={() => router.back()} className="text-sm text-slate-500 hover:text-slate-700 mb-2 inline-flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
          </svg>
          Back
        </button>
        <div className="flex items-start justify-between mt-2">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className={`px-2 py-1 text-xs font-medium rounded ${
                entity.status === 'active' ? 'bg-green-100 text-green-800' :
                entity.status === 'pending' ? 'bg-amber-100 text-amber-800' :
                'bg-slate-100 text-slate-800'
              }`}>
                {entity.status}
              </span>
              <EmbeddingStatusBadge status={entity.embedding_status} />
              <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">
                {entity.rights_type}
              </span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900">{entity.title}</h1>
            <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
              <span>Version {entity.version}</span>
              <span>Created {new Date(entity.created_at).toLocaleDateString()}</span>
              {entity.entity_key && <span className="font-mono">{entity.entity_key}</span>}
            </div>
          </div>
          <div className="flex gap-2">
            {entity.embedding_status !== 'processing' && entity.embedding_status !== 'ready' && (
              <button
                onClick={handleTriggerEmbedding}
                className="px-4 py-2 border border-slate-300 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-50 transition-colors"
              >
                Generate Embeddings
              </button>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
          <button onClick={() => setError(null)} className="ml-2 text-red-500 hover:text-red-700">Dismiss</button>
        </div>
      )}

      {uploadProgress && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg text-blue-700">
          {uploadProgress}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Assets Section */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200">
            <div className="p-6 border-b border-slate-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Assets</h2>
              <span className="text-sm text-slate-500">{entityAssets.length} files</span>
            </div>

            {/* Upload Area */}
            <div className="p-6 border-b border-slate-200 bg-slate-50">
              <div className="flex items-center gap-4">
                <select
                  value={uploadType}
                  onChange={(e) => setUploadType(e.target.value)}
                  className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-slate-900 focus:border-slate-900 outline-none"
                >
                  {ASSET_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileSelect}
                  disabled={isUploading}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className={`px-4 py-2 bg-slate-900 text-white text-sm font-medium rounded-lg cursor-pointer transition-colors ${
                    isUploading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-slate-800'
                  }`}
                >
                  {isUploading ? 'Uploading...' : 'Upload File'}
                </label>
              </div>
            </div>

            {/* Assets List */}
            {entityAssets.length === 0 ? (
              <div className="p-12 text-center">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-slate-900 mb-2">No assets yet</h3>
                <p className="text-slate-500">Upload files to attach to this entity.</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-200">
                {entityAssets.map((asset) => (
                  <div key={asset.id} className="p-4 hover:bg-slate-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                          <svg className="w-5 h-5 text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                          </svg>
                        </div>
                        <div>
                          <p className="font-medium text-slate-900 text-sm">{asset.filename}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-slate-500">{asset.asset_type}</span>
                            <span className="text-xs text-slate-400">{formatFileSize(asset.file_size_bytes)}</span>
                            <ProcessingStatus status={asset.processing_status} size="sm" />
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDownload(asset.id)}
                        className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* AI Permissions */}
          {entity.ai_permissions && Object.keys(entity.ai_permissions).length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">AI Permissions</h2>
              <pre className="text-sm bg-slate-50 p-4 rounded-lg overflow-x-auto">
                {JSON.stringify(entity.ai_permissions, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Processing Jobs */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200">
            <div className="p-4 border-b border-slate-200">
              <h3 className="font-semibold text-slate-900">Processing Jobs</h3>
            </div>
            {entityJobs.length === 0 ? (
              <div className="p-6 text-center text-sm text-slate-500">
                No processing jobs yet
              </div>
            ) : (
              <div className="divide-y divide-slate-200">
                {entityJobs.map((job) => (
                  <div key={job.id} className="p-4">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-slate-900">
                        {job.job_type.replace('_', ' ')}
                      </span>
                      <ProcessingStatus status={job.status} size="sm" />
                    </div>
                    <p className="text-xs text-slate-500">
                      {new Date(job.created_at).toLocaleString()}
                    </p>
                    {job.error_message && (
                      <p className="text-xs text-red-600 mt-1">{job.error_message}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Metadata */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <h3 className="font-semibold text-slate-900 mb-3">Details</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">ID</dt>
                <dd className="font-mono text-slate-900 text-xs">{entity.id.slice(0, 8)}...</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Catalog</dt>
                <dd>
                  <Link href={`/dashboard/catalogs/${entity.catalog_id}`} className="text-blue-600 hover:underline">
                    View
                  </Link>
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Verification</dt>
                <dd className="text-slate-900">{entity.verification_status}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Updated</dt>
                <dd className="text-slate-900">{new Date(entity.updated_at).toLocaleDateString()}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}
