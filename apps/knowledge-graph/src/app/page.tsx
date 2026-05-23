'use client'

import dynamic from 'next/dynamic'
import { useState } from 'react'
import { KnowledgeNode } from '@/types/knowledge'
import { IngestPanel } from '@/components/ingest-panel'
import { SearchPanel } from '@/components/search-panel'
import { NodeViewer } from '@/components/node-viewer'

// SSR must be disabled — react-force-graph-3d uses WebGL + window
const Graph3D = dynamic(
  () => import('@/components/graph-3d').then((m) => m.Graph3D),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full bg-background rounded-lg flex items-center justify-center">
        <span className="text-muted-foreground text-sm font-mono">Loading 3D engine...</span>
      </div>
    ),
  }
)

export default function Home() {
  const [selectedNode, setSelectedNode] = useState<KnowledgeNode | null>(null)
  const [sidePanel, setSidePanel] = useState<'ingest' | 'search'>('ingest')

  return (
    <div className="h-screen bg-background text-foreground flex flex-col overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-5 py-3 border-b border-zinc-900 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
          <span className="text-sm font-mono text-zinc-300 tracking-wide">NOOSCOPE</span>
          <span className="text-xs text-zinc-700 font-mono">/ knowledge graph</span>
        </div>
        <nav className="flex gap-1" aria-label="Panel navigation">
          <button
            onClick={() => setSidePanel('ingest')}
            aria-pressed={sidePanel === 'ingest'}
            className={`px-3 py-1 text-xs font-mono rounded border transition-colors ${
              sidePanel === 'ingest'
                ? 'bg-zinc-800 border-zinc-700 text-zinc-200'
                : 'border-zinc-900 text-muted-foreground hover:border-zinc-800 hover:text-zinc-400'
            }`}
          >
            + ingest
          </button>
          <button
            onClick={() => setSidePanel('search')}
            aria-pressed={sidePanel === 'search'}
            className={`px-3 py-1 text-xs font-mono rounded border transition-colors ${
              sidePanel === 'search'
                ? 'bg-zinc-800 border-zinc-700 text-zinc-200'
                : 'border-zinc-900 text-muted-foreground hover:border-zinc-800 hover:text-zinc-400'
            }`}
          >
            ⌕ query
          </button>
        </nav>
      </header>

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* 3D Graph — main canvas */}
        <main className="flex-1 p-3 min-h-0">
          <Graph3D onNodeClick={setSelectedNode} />
        </main>

        {/* Side panel */}
        <aside aria-label="Knowledge graph controls" className="w-[380px] border-l border-zinc-900 bg-background overflow-y-auto p-4 shrink-0">
          {sidePanel === 'ingest' ? (
            <>
              <h2 className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-4">
                Add to Knowledge Graph
              </h2>
              <IngestPanel />
            </>
          ) : (
            <>
              <h2 className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-4">
                Query Knowledge Graph
              </h2>
              <SearchPanel onNodeClick={setSelectedNode} />
            </>
          )}
        </aside>
      </div>

      {/* Node viewer (sheet) */}
      <NodeViewer node={selectedNode} onClose={() => setSelectedNode(null)} />
    </div>
  )
}
