'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { GraphData, KnowledgeNode } from '@/types/knowledge'

// Safe client-side dynamic loading of WebGL library to prevent SSR evaluate crashes
let ForceGraph3D: any = null
if (typeof window !== 'undefined') {
  ForceGraph3D = require('react-force-graph-3d').default || require('react-force-graph-3d')
}

interface Graph3DProps {
  onNodeClick?: (node: KnowledgeNode) => void
}

export function Graph3D({ onNodeClick }: Graph3DProps) {
  const fgRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })

  const fetchGraph = useCallback(async () => {
    try {
      setLoading(true)
      const res = await fetch('/api/graph')
      if (!res.ok) throw new Error('Failed to fetch graph')
      const data: GraphData = await res.json()
      setGraphData(data)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchGraph()
  }, [fetchGraph])

  // Track container size with ResizeObserver
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect
      if (width > 0 && height > 0) setDimensions({ width, height })
    })
    observer.observe(el)
    const { width, height } = el.getBoundingClientRect()
    if (width > 0 && height > 0) setDimensions({ width, height })
    return () => observer.disconnect()
  }, [])

  const handleNodeClick = useCallback((node: any) => {
    onNodeClick?.(node as KnowledgeNode)
    // Fly camera to clicked node
    const distance = 100
    const distRatio = 1 + distance / Math.hypot(node.x ?? 1, node.y ?? 1, node.z ?? 1)
    fgRef.current?.cameraPosition(
      { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
      node,
      1200
    )
  }, [onNodeClick])

  const nodeCount = graphData.nodes.filter(n => n.type === 'Document').length
  const edgeCount = graphData.links.length

  return (
    <div ref={containerRef} className="relative w-full h-full bg-background rounded-lg overflow-hidden">
      {!loading && !error && ForceGraph3D && (
        <ForceGraph3D
          ref={fgRef}
          graphData={graphData}
          nodeLabel={(node: any) => node.title ?? ''}
          nodeColor={(node: any) => node.color ?? '#4f46e5'}
          nodeRelSize={5}
          nodeOpacity={0.85}
          linkColor={(link: any) =>
            link.type === 'BELONGS_TO' ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.15)'
          }
          linkWidth={(link: any) =>
            link.type === 'BELONGS_TO' ? 0.3 : Math.max(0.5, (link.score ?? 0.5) * 3)
          }
          linkDirectionalParticles={1}
          linkDirectionalParticleWidth={1.5}
          backgroundColor="#09090b"
          onNodeClick={handleNodeClick}
          width={dimensions.width}
          height={dimensions.height}
        />
      )}

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-muted-foreground text-sm font-mono">Loading graph...</div>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-red-400 text-sm font-mono">{error}</div>
        </div>
      )}

      {!loading && !error && nodeCount === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center text-muted-foreground">
            <div className="text-5xl mb-3 opacity-30">◎</div>
            <div className="text-sm font-mono">No nodes yet.</div>
            <div className="text-xs mt-1 opacity-60">Ingest some content to begin.</div>
          </div>
        </div>
      )}

      {nodeCount > 0 && (
        <div className="absolute top-3 left-3 text-xs text-muted-foreground font-mono pointer-events-none">
          {nodeCount} nodes · {edgeCount} edges
        </div>
      )}

      <button
        onClick={fetchGraph}
        disabled={loading}
        aria-label="Refresh graph"
        className="absolute top-3 right-3 text-xs text-muted-foreground hover:text-foreground font-mono px-2 py-1 border border-zinc-800 hover:border-zinc-600 rounded transition-colors bg-background/80 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {loading ? '↺ loading...' : '↺ refresh'}
      </button>
    </div>
  )
}
