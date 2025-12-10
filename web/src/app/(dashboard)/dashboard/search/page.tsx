"use client"

import { useState } from "react"
import { createClient } from "@/lib/supabase/client"
import { search, type SearchResult } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Sparkles, Search as SearchIcon } from "lucide-react"

export default function SearchPage() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searched, setSearched] = useState(false)
  const supabase = createClient()

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsLoading(true)
    setError(null)
    setSearched(true)

    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return

      const data = await search.semantic(query, session.access_token, { limit: 20 })
      setResults(data.results)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <Badge variant="outline">Search</Badge>
          <p className="text-sm text-muted-foreground">Vector + permissions aware</p>
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Semantic Search</h1>
          <p className="text-muted-foreground">
            Find IP assets using natural language across catalogs, rights types, and permissions.
          </p>
        </div>
      </div>

      {/* Search Form */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Sparkles className="h-5 w-5 text-primary" />
            Natural language search
          </CardTitle>
          <CardDescription>Search embeddings, metadata, and AI permissions in one query.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex flex-col gap-4 md:flex-row">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for music, voices, characters, visual works..."
            />
            <Button type="submit" disabled={isLoading || !query.trim()} className="md:w-36">
              {isLoading ? "Searching..." : "Search"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <Card className="border-destructive/40 bg-destructive/10">
          <CardHeader>
            <CardTitle className="text-destructive text-lg">Search failed</CardTitle>
            <CardDescription className="text-destructive">{error}</CardDescription>
          </CardHeader>
        </Card>
      )}

      {/* Results */}
      {searched && !isLoading && (
        <Card>
          <CardHeader className="border-b border-border">
            <CardTitle>
              {results.length} {results.length === 1 ? "result" : "results"} found
            </CardTitle>
          </CardHeader>

          {results.length === 0 ? (
            <CardContent className="flex flex-col items-center justify-center gap-3 py-12 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
                <SearchIcon className="h-6 w-6 text-muted-foreground" />
              </div>
              <div>
                <h3 className="text-lg font-semibold">No results yet</h3>
                <p className="text-sm text-muted-foreground">
                  Try a different search term or add more entities.
                </p>
              </div>
            </CardContent>
          ) : (
            <div className="divide-y divide-border">
              {results.map((result) => (
                <CardContent key={result.entity_id} className="flex flex-col gap-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="capitalize">
                          {result.rights_type.replace("_", " ")}
                        </Badge>
                        {result.catalog_name && (
                          <span className="text-xs text-muted-foreground">{result.catalog_name}</span>
                        )}
                      </div>
                      <h3 className="text-lg font-semibold leading-tight">{result.title}</h3>
                      {result.snippet && (
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {result.snippet}
                        </p>
                      )}
                    </div>
                    <div className="min-w-[140px] text-right">
                      <p className="text-sm font-semibold">
                        {(result.similarity_score * 100).toFixed(1)}% match
                      </p>
                      <div className="flex flex-wrap justify-end gap-1 pt-2">
                        {result.permissions_summary.training_allowed && (
                          <Badge variant="success" className="text-xs">Training OK</Badge>
                        )}
                        {result.permissions_summary.commercial_allowed && (
                          <Badge variant="outline" className="text-xs">Commercial OK</Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Initial State */}
      {!searched && !isLoading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center gap-3 py-14 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
              <SearchIcon className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold">Search your IP catalog</h3>
            <p className="max-w-md text-sm text-muted-foreground">
              Use natural language to find music, voice recordings, characters, and other intellectual property across your catalogs.
            </p>
          </CardContent>
        </Card>
      )}

      {isLoading && (
        <Card>
          <CardContent className="flex items-center gap-3 py-6">
            <Skeleton className="h-10 w-10 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-3 w-1/3" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
