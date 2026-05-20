import { NextRequest } from 'next/server'
import { mergeDocument, buildSimilarityEdges, buildCrossRootLinks, initSchema } from '@/lib/neo4j'
import { embed, chunkText, hashContent } from '@/lib/embeddings'
import { IngestRequest } from '@/types/knowledge'
import { randomUUID } from 'crypto'

let schemaInitialized = false

async function ensureSchema() {
  if (!schemaInitialized) {
    await initSchema()
    schemaInitialized = true
  }
}

function normalizeId(title: string, url?: string): string {
  // Use URL as stable ID if available, otherwise hash title
  if (url) {
    return url
      .replace(/^https?:\/\//, '')
      .replace(/[^a-z0-9]/gi, '-')
      .toLowerCase()
      .slice(0, 80)
  }
  return title.toLowerCase().replace(/\s+/g, '-').replace(/[^\p{L}\p{N}-]/gu, '').slice(0, 60) + '-' + randomUUID().slice(0, 8)
}

export async function POST(req: NextRequest) {
  try {
    await ensureSchema()

    const body: IngestRequest = await req.json()
    const { source, content, title, url, cluster, tags, metadata } = body

    if (!content?.trim()) {
      return Response.json({ error: 'Content is required' }, { status: 400 })
    }

    const docTitle = title ?? url ?? 'Untitled'
    const docId = normalizeId(docTitle, url)
    const contentHash = hashContent(content)

    // Chunk long content
    const chunks = chunkText(content)
    let totalEdges = 0

    if (chunks.length === 1) {
      // Single chunk — embed and store directly
      const embedding = await embed(content)
      const { created, contentChanged } = await mergeDocument({
        id: docId,
        title: docTitle,
        content: content.slice(0, 2000), // store preview in node
        url,
        source,
        cluster: cluster ?? source,
        tags,
        embedding,
        contentHash,
        metadata,
      })
      if (created || contentChanged) {
        totalEdges = await buildSimilarityEdges(docId, embedding)
        await buildCrossRootLinks(docId, content)
      }
    } else {
      // Multiple chunks — store first chunk as main node, rest as linked chunks
      const firstEmbedding = await embed(chunks[0])
      const { created, contentChanged } = await mergeDocument({
        id: docId,
        title: docTitle,
        content: content.slice(0, 2000), // preserve original newlines for markdown rendering
        url,
        source,
        cluster: cluster ?? source,
        tags,
        embedding: firstEmbedding,
        contentHash,
        metadata,
      })

      if (created || contentChanged) {
        await buildCrossRootLinks(docId, content)
        
        for (let i = 1; i < chunks.length; i++) {
          const chunkId = `${docId}--chunk-${i}`
          const chunkEmbedding = await embed(chunks[i])
          await mergeDocument({
            id: chunkId,
            title: `${docTitle} (part ${i + 1})`,
            content: chunks[i],
            url,
            source,
            cluster: cluster ?? source,
            tags,
            embedding: chunkEmbedding,
            contentHash,
            metadata,
          })
        }

        totalEdges = await buildSimilarityEdges(docId, firstEmbedding)
      }
    }

    return Response.json({
      nodeId: docId,
      chunksCreated: chunks.length,
      edgesCreated: totalEdges,
      embedded: true,
    })
  } catch (err) {
    console.error('[ingest]', err)
    return Response.json(
      { error: err instanceof Error ? err.message : 'Ingestion failed' },
      { status: 500 }
    )
  }
}
