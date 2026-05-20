'use client'

import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { IngestResult } from '@/types/knowledge'

interface IngestResult_ extends IngestResult {
  error?: string
}

interface ObsidianProgressLine {
  type: 'start' | 'progress' | 'done'
  total?: number
  file?: string
  title?: string
  status?: 'ok' | 'skip' | 'error'
  nodeId?: string
  edges?: number
  error?: string
  processed?: number
  errors?: number
  totalEdges?: number
}

export function IngestPanel() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<IngestResult_ | null>(null)

  const [textContent, setTextContent] = useState('')
  const [textTitle, setTextTitle] = useState('')
  const [textCluster, setTextCluster] = useState('')
  const [textTags, setTextTags] = useState('')

  const [urlInput, setUrlInput] = useState('')
  const [urlCluster, setUrlCluster] = useState('')

  const [vaultPath, setVaultPath] = useState('')
  const [obsidianRunning, setObsidianRunning] = useState(false)
  const [obsidianLog, setObsidianLog] = useState<ObsidianProgressLine[]>([])
  const logEndRef = useRef<HTMLDivElement>(null)

  async function ingest(payload: object) {
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch('/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error ?? 'Ingestion failed')
      setResult(data)
    } catch (e) {
      setResult({ nodeId: '', chunksCreated: 0, edgesCreated: 0, embedded: false, error: (e as Error).message })
    } finally {
      setLoading(false)
    }
  }

  async function syncObsidian() {
    if (!vaultPath.trim()) return
    setObsidianRunning(true)
    setObsidianLog([])

    try {
      const res = await fetch('/api/ingest/obsidian', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vaultPath }),
      })

      if (!res.ok) {
        const err = await res.text()
        setObsidianLog([{ type: 'progress', status: 'error', error: err, file: '', title: '' }])
        return
      }

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.trim()) continue
          try {
            const event: ObsidianProgressLine = JSON.parse(line)
            setObsidianLog((prev) => [...prev, event])
            setTimeout(() => logEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
          } catch {}
        }
      }
    } catch (err) {
      setObsidianLog((prev) => [
        ...prev,
        { type: 'progress', status: 'error', file: '', title: '', error: (err as Error).message },
      ])
    } finally {
      setObsidianRunning(false)
    }
  }

  async function ingestUrl() {
    if (!urlInput.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const fetchRes = await fetch('/api/ingest/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: urlInput }),
      })
      const fetchData = await fetchRes.json()
      if (!fetchRes.ok) throw new Error(fetchData.error ?? 'Could not fetch URL')

      await ingest({
        source: 'url',
        content: fetchData.text,
        url: urlInput,
        title: urlInput,
        cluster: urlCluster || 'web',
      })
    } catch (e) {
      setResult({ nodeId: '', chunksCreated: 0, edgesCreated: 0, embedded: false, error: (e as Error).message })
      setLoading(false)
    }
  }

  const inputClass = 'bg-card border-zinc-800 text-foreground text-sm placeholder:text-muted-foreground'

  return (
    <div className="space-y-4">
      <Tabs defaultValue="text">
        <TabsList className="bg-card border border-zinc-800">
          <TabsTrigger value="text" className="data-[state=active]:bg-zinc-800 text-xs">
            Text
          </TabsTrigger>
          <TabsTrigger value="url" className="data-[state=active]:bg-zinc-800 text-xs">
            URL
          </TabsTrigger>
          <TabsTrigger value="obsidian" className="data-[state=active]:bg-zinc-800 text-xs">
            Obsidian
          </TabsTrigger>
        </TabsList>

        <TabsContent value="text" className="space-y-3 mt-3">
          <Input
            id="text-title"
            aria-label="Title"
            placeholder="Title (optional)"
            value={textTitle}
            onChange={(e) => setTextTitle(e.target.value)}
            className={inputClass}
          />
          <Input
            id="text-cluster"
            aria-label="Cluster"
            placeholder="Cluster (e.g. 'psychology', 'tech', 'health')"
            value={textCluster}
            onChange={(e) => setTextCluster(e.target.value)}
            className={inputClass}
          />
          <Input
            id="text-tags"
            aria-label="Tags, comma-separated"
            placeholder="Tags (comma-separated)"
            value={textTags}
            onChange={(e) => setTextTags(e.target.value)}
            className={inputClass}
          />
          <Textarea
            id="text-content"
            aria-label="Content to ingest"
            placeholder="Paste your content here — notes, highlights, articles, transcripts..."
            value={textContent}
            onChange={(e) => setTextContent(e.target.value)}
            className={`${inputClass} min-h-[180px] resize-none`}
          />
          <Button
            onClick={() =>
              ingest({
                source: 'file',
                content: textContent,
                title: textTitle || undefined,
                cluster: textCluster || undefined,
                tags: textTags ? textTags.split(',').map((t) => t.trim()) : undefined,
              })
            }
            disabled={loading || !textContent.trim()}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-sm"
          >
            {loading ? 'Embedding...' : 'Add to Knowledge Graph'}
          </Button>
        </TabsContent>

        <TabsContent value="url" className="space-y-3 mt-3">
          <Input
            id="url-input"
            aria-label="URL to ingest"
            placeholder="https://..."
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            className={inputClass}
          />
          <Input
            id="url-cluster"
            aria-label="Cluster"
            placeholder="Cluster (e.g. 'research', 'bookmarks')"
            value={urlCluster}
            onChange={(e) => setUrlCluster(e.target.value)}
            className={inputClass}
          />
          <Button
            onClick={ingestUrl}
            disabled={loading || !urlInput.trim()}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-sm"
          >
            {loading ? 'Fetching & Embedding...' : 'Ingest URL'}
          </Button>
        </TabsContent>

        <TabsContent value="obsidian" className="space-y-3 mt-3">
          <Input
            id="vault-path"
            aria-label="Obsidian vault path"
            placeholder="Vault path — e.g. C:\Users\you\Documents\MyVault"
            value={vaultPath}
            onChange={(e) => setVaultPath(e.target.value)}
            className={`${inputClass} font-mono`}
          />
          <p className="text-xs text-muted-foreground">
            Reads all .md files. Folder name becomes cluster. Frontmatter tags preserved.
          </p>
          <Button
            onClick={syncObsidian}
            disabled={obsidianRunning || !vaultPath.trim()}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-sm"
          >
            {obsidianRunning ? 'Syncing vault...' : 'Sync Vault → Knowledge Graph'}
          </Button>

          {obsidianLog.length > 0 && (
            <div
              role="log"
              aria-label="Vault sync progress"
              aria-live="polite"
              className="bg-background border border-zinc-800 rounded-md p-3 max-h-64 overflow-y-auto text-xs font-mono space-y-1"
            >
              {obsidianLog.map((line, i) => {
                if (line.type === 'start') {
                  return <div key={i} className="text-muted-foreground">Found {line.total} notes. Starting...</div>
                }
                if (line.type === 'done') {
                  return (
                    <div key={i} className="text-emerald-400 border-t border-zinc-800 pt-1 mt-1">
                      Done — {line.processed} notes · {line.totalEdges} edges · {line.errors} errors
                    </div>
                  )
                }
                if (line.status === 'ok') {
                  return (
                    <div key={i} className="text-muted-foreground">
                      <span className="text-emerald-600" aria-label="Success">✓</span>{' '}
                      <span className="text-zinc-300">{line.title}</span>
                      {line.edges ? <span className="opacity-60"> +{line.edges} edges</span> : null}
                    </div>
                  )
                }
                if (line.status === 'error') {
                  return (
                    <div key={i} className="text-red-400">
                      <span aria-label="Error">✗</span> {line.file || line.title}: {line.error}
                    </div>
                  )
                }
                return null
              })}
              <div ref={logEndRef} />
            </div>
          )}
        </TabsContent>
      </Tabs>

      {result && (
        <div
          role="status"
          aria-live="polite"
          className={`rounded-md p-3 text-xs font-mono border ${
            result.error
              ? 'bg-red-950/50 border-red-900 text-red-400'
              : 'bg-emerald-950/50 border-emerald-900 text-emerald-400'
          }`}
        >
          {result.error ? (
            <span>✗ {result.error}</span>
          ) : (
            <div className="space-y-1">
              <div>✓ Node created: <span className="text-zinc-300">{result.nodeId}</span></div>
              <div>{result.chunksCreated} chunk(s) · {result.edgesCreated} similarity edge(s)</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
