'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { KnowledgeNode } from '@/types/knowledge'

interface SearchResult {
  id: string
  title: string
  content: string | null
  url: string | null
  source: string
  cluster: string | null
  score: number
}

interface SearchPanelProps {
  onNodeClick?: (node: KnowledgeNode) => void
}

function SkeletonCard() {
  return (
    <div className="rounded-md border border-zinc-800 p-3 space-y-2 animate-pulse">
      <div className="flex justify-between gap-2">
        <div className="h-4 bg-zinc-800 rounded w-3/4" />
        <div className="h-4 bg-zinc-800 rounded w-10 shrink-0" />
      </div>
      <div className="h-3 bg-zinc-800 rounded w-full" />
      <div className="h-3 bg-zinc-800 rounded w-2/3" />
    </div>
  )
}

export function SearchPanel({ onNodeClick }: SearchPanelProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)

  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [asking, setAsking] = useState(false)
  const [graphragError, setGraphragError] = useState<string | null>(null)

  async function search() {
    if (!query.trim()) return
    setSearching(true)
    setResults([])
    setSearchError(null)
    setHasSearched(false)
    try {
      const res = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.error ?? `Search failed (${res.status})`)
      }
      const data = await res.json()
      setResults(data.results ?? [])
      setHasSearched(true)
    } catch (e) {
      setSearchError(e instanceof Error ? e.message : 'Search failed')
    } finally {
      setSearching(false)
    }
  }

  async function askGraphRAG() {
    if (!question.trim()) return
    setAsking(true)
    setAnswer('')
    setGraphragError(null)
    try {
      const res = await fetch('/api/graphrag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.error ?? `Request failed (${res.status})`)
      }

      if (!res.body) throw new Error('No response body')

      const reader = res.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        setAnswer((prev) => prev + decoder.decode(value))
      }
    } catch (e) {
      setGraphragError(e instanceof Error ? e.message : 'Failed to get answer')
    } finally {
      setAsking(false)
    }
  }

  return (
    <Tabs defaultValue="search" className="w-full">
      <TabsList className="bg-card border border-zinc-800">
        <TabsTrigger value="search" className="data-[state=active]:bg-zinc-800 text-xs">
          Search
        </TabsTrigger>
        <TabsTrigger value="graphrag" className="data-[state=active]:bg-zinc-800 text-xs">
          GraphRAG
        </TabsTrigger>
      </TabsList>

      <TabsContent value="search" className="mt-3 space-y-3">
        <div className="flex gap-2">
          <Input
            aria-label="Search query"
            placeholder="Search your knowledge base..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && search()}
            className="bg-card border-zinc-800 text-foreground text-sm placeholder:text-muted-foreground"
          />
          <Button
            onClick={search}
            disabled={searching || !query.trim()}
            aria-label={searching ? 'Searching…' : 'Run search'}
            className="bg-zinc-800 hover:bg-zinc-700 text-foreground text-sm shrink-0"
          >
            {searching ? '…' : 'Search'}
          </Button>
        </div>

        {searchError && (
          <p role="alert" className="text-xs text-red-400 font-mono">✗ {searchError}</p>
        )}

        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {searching && (
            <>
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </>
          )}

          {!searching && results.map((r) => (
            <button
              key={r.id}
              onClick={() => onNodeClick?.({
                id: r.id,
                title: r.title,
                content: r.content ?? undefined,
                url: r.url ?? undefined,
                source: r.source as KnowledgeNode['source'],
                type: 'Document',
                cluster: r.cluster ?? undefined,
              })}
              className="w-full text-left rounded-md border border-zinc-800 p-3 space-y-1 hover:border-zinc-600 hover:bg-zinc-900/40 transition-colors cursor-pointer"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="text-sm text-foreground font-medium leading-tight">{r.title}</span>
                <Badge
                  variant="outline"
                  className="border-zinc-700 text-muted-foreground text-xs shrink-0 font-mono"
                >
                  {(r.score * 100).toFixed(0)}%
                </Badge>
              </div>
              {r.content && (
                <p className="text-xs text-muted-foreground line-clamp-2">{r.content}</p>
              )}
              <div className="flex gap-1 items-center">
                {r.cluster && (
                  <Badge variant="secondary" className="text-xs bg-zinc-800 text-muted-foreground">
                    {r.cluster}
                  </Badge>
                )}
                {r.url && (
                  <a
                    href={r.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="text-xs text-indigo-500 hover:text-indigo-400"
                  >
                    ↗ source
                  </a>
                )}
              </div>
            </button>
          ))}

          {hasSearched && results.length === 0 && !searching && (
            <p className="text-xs text-muted-foreground text-center py-4">No results</p>
          )}
        </div>
      </TabsContent>

      <TabsContent value="graphrag" className="mt-3 space-y-3">
        <Textarea
          aria-label="Question for knowledge graph"
          placeholder="Ask a question about your knowledge base...&#10;e.g. 'What do I know about consciousness?' or 'How does X relate to Y?'"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className="bg-card border-zinc-800 text-foreground text-sm min-h-[80px] placeholder:text-muted-foreground resize-none"
        />
        <Button
          onClick={askGraphRAG}
          disabled={asking || !question.trim()}
          className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-sm"
        >
          {asking ? 'Traversing graph...' : 'Ask Knowledge Graph'}
        </Button>

        {graphragError && (
          <p role="alert" className="text-xs text-red-400 font-mono">✗ {graphragError}</p>
        )}

        {answer && (
          <div className="rounded-md border border-zinc-800 bg-card/50 p-4">
            <p className="text-xs text-muted-foreground mb-2 font-mono uppercase tracking-wider">Answer</p>
            <div className="prose prose-sm prose-invert max-w-none text-zinc-200 [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
              <ReactMarkdown>{answer}</ReactMarkdown>
            </div>
          </div>
        )}
      </TabsContent>
    </Tabs>
  )
}
