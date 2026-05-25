import { runCypher } from '@/lib/neo4j'
import { GraphData, KnowledgeNode, KnowledgeEdge } from '@/types/knowledge'
import { execSync } from 'child_process'

const CLUSTER_COLORS: Record<string, string> = {
  file: '#4f46e5',
  url: '#059669',
  readwise: '#d97706',
  highlight: '#dc2626',
  calendar: '#0ea5e9',
  default: '#6b7280',
}

function clusterColor(cluster: string | null): string {
  if (!cluster) return CLUSTER_COLORS.default
  for (const [key, color] of Object.entries(CLUSTER_COLORS)) {
    if (cluster.toLowerCase().includes(key)) return color
  }
  // Generate deterministic color from cluster name
  let hash = 0
  for (const c of cluster) hash = c.charCodeAt(0) + ((hash << 5) - hash)
  const hue = Math.abs(hash) % 360
  return `hsl(${hue}, 65%, 55%)`
}

function normalizeId(filePath: string, vaultPath: string): string {
  const normalizedFile = filePath.replace(/\\/g, '/')
  const normalizedVault = vaultPath.replace(/\\/g, '/')
  const relative = normalizedFile
    .replace(normalizedVault, '')
    .replace(/^\//, '')
    .replace(/\.md$/, '')
  return ('obsidian/' + relative)
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^\p{L}\p{N}\-/]/gu, '')
    .slice(0, 100)
}

export async function GET() {
  try {
    // Fetch documents and their clusters
    const nodeRecords = await runCypher(`
      MATCH (d:Document)
      OPTIONAL MATCH (d)-[:BELONGS_TO]->(c:Cluster)
      RETURN d.id AS id, d.title AS title, d.source AS source,
             d.url AS url, d.cluster AS cluster, d.content AS content,
             c.name AS clusterName
      LIMIT 500
    `)

    // Fetch similarity edges
    const edgeRecords = await runCypher(`
      MATCH (a:Document)-[r:SIMILAR_TO]-(b:Document)
      WHERE a.id < b.id
      RETURN a.id AS source, b.id AS target, 'SIMILAR_TO' AS type, r.score AS score
      LIMIT 1000
    `)

    // Fetch BELONGS_TO edges (document → cluster)
    const belongsRecords = await runCypher(`
      MATCH (d:Document)-[:BELONGS_TO]->(c:Cluster)
      RETURN d.id AS source, 'cluster:' + c.id AS target
    `)

    // Fetch cluster hierarchy
    const clusterRecords = await runCypher(`
      MATCH (c:Cluster)
      RETURN c.id AS id, c.name AS name
    `)

    const nodes: KnowledgeNode[] = nodeRecords.map((r) => ({
      id: r.get('id') as string,
      title: r.get('title') as string,
      source: r.get('source') as any,
      type: 'Document' as const,
      url: r.get('url') as string | undefined,
      content: r.get('content') as string | undefined,
      cluster: r.get('clusterName') ?? r.get('cluster') ?? 'default',
      color: clusterColor(r.get('clusterName') ?? r.get('cluster')),
    }))

    // Add cluster nodes
    const clusterNodes: KnowledgeNode[] = clusterRecords.map((r) => ({
      id: `cluster:${r.get('id')}`,
      title: r.get('name') as string,
      source: 'file' as const,
      type: 'Cluster' as const,
      cluster: r.get('name') as string,
      color: clusterColor(r.get('name') as string),
    }))

    const similarLinks: KnowledgeEdge[] = edgeRecords.map((r) => ({
      source: r.get('source') as string,
      target: r.get('target') as string,
      type: 'SIMILAR_TO' as const,
      score: r.get('score') as number,
    }))

    const belongsLinks: KnowledgeEdge[] = belongsRecords.map((r) => ({
      source: r.get('source') as string,
      target: r.get('target') as string,
      type: 'BELONGS_TO' as const,
      score: 0.5,
    }))

    const links = [...similarLinks, ...belongsLinks]

    const data: GraphData = {
      nodes: [...nodes, ...clusterNodes],
      links,
    }

    return Response.json(data)
  } catch (err) {
    console.warn('⚠️ Neo4j offline. Falling back to local Python Obsidian extraction:', err)
    
    try {
      const cwd = 'C:\\telo\\Efforts\Ongoing\\NAUTILUS'
      const pythonPath = 'C:\\telo\\Efforts\\Ongoing\\NAUTILUS\\core\\enerv'
      const vaultPath = process.env.OBSIDIAN_VAULT_PATH || 'C:\\Users\\sasha\\Downloads\\Notes_ACE'
      
      const cmd = `python -m tools.tools export-graph --vault "${vaultPath}"`
      
      const stdout = execSync(cmd, {
        cwd,
        env: {
          ...process.env,
          PYTHONPATH: pythonPath
        },
        maxBuffer: 15 * 1024 * 1024 // 15MB buffer
      })
      
      const data = JSON.parse(stdout.toString('utf-8'))
      return Response.json(data)
    } catch (fallbackErr: any) {
      console.error('❌ Python fallback extraction failed:', fallbackErr)
      return Response.json(
        { error: 'Failed to connect to Neo4j and Python fallback failed', details: fallbackErr?.message },
        { status: 500 }
      )
    }
  }
}
