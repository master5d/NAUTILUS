import { NextRequest } from 'next/server'
import { walkVault } from '@/lib/sources/obsidian'
import { mergeDocument, buildSimilarityEdges, initSchema } from '@/lib/neo4j'
import { embed, chunkText, hashContent } from '@/lib/embeddings'
let schemaInitialized = false
async function ensureSchema() {
  if (!schemaInitialized) {
    await initSchema()
    schemaInitialized = true
  }
}

// Stable ID derived from vault-relative file path — ensures MERGE finds the same node on re-sync
function normalizeId(filePath: string, vaultPath: string): string {
  // Convert backslashes FIRST so the vaultPath replacement works on Windows
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

// Newline-delimited JSON progress stream
type ProgressEvent =
  | { type: 'start'; total: number }
  | { type: 'progress'; file: string; title: string; status: 'ok' | 'skip' | 'unchanged' | 'error'; nodeId?: string; edges?: number; error?: string }
  | { type: 'done'; processed: number; skipped: number; unchanged: number; errors: number; totalEdges: number }

function encode(event: ProgressEvent): Uint8Array {
  return new TextEncoder().encode(JSON.stringify(event) + '\n')
}

export async function POST(req: NextRequest) {
  const { vaultPath } = await req.json()

  if (!vaultPath?.trim()) {
    return new Response('vaultPath is required', { status: 400 })
  }

  // Collect notes first so we can report total count
  let notes: ReturnType<typeof walkVault> extends Generator<infer T> ? T[] : never[]
  try {
    notes = [...walkVault(vaultPath)] as any
  } catch (err) {
    return new Response(
      err instanceof Error ? err.message : 'Failed to read vault',
      { status: 400 }
    )
  }

  const stream = new ReadableStream({
    async start(controller) {
      controller.enqueue(encode({ type: 'start', total: notes.length }))

      await ensureSchema().catch(() => {})

      let processed = 0
      let skipped = 0
      let unchanged = 0
      let errors = 0
      let totalEdges = 0

      for (const note of notes) {
        const shortPath = note.filePath.split(/[\\/]/).slice(-2).join('/')
        try {
          const chunks = chunkText(note.content)
          const docId = normalizeId(note.filePath, vaultPath)
          const contentHash = hashContent(note.content)

          // Check if content changed (deduplication for re-sync)
          const firstEmbedding = await embed(chunks[0])
          const { created, contentChanged } = await mergeDocument({
            id: docId,
            title: note.title,
            content: note.content.slice(0, 5000),
            source: 'obsidian',
            cluster: note.cluster,
            tags: note.tags,
            embedding: firstEmbedding,
            contentHash,
          })

          // Only process chunks and edges if this is a new document or content changed
          if (created || contentChanged) {
            // Extra chunks
            for (let i = 1; i < chunks.length; i++) {
              const chunkId = `${docId}--chunk-${i}`
              const chunkEmbedding = await embed(chunks[i])
              await mergeDocument({
                id: chunkId,
                title: `${note.title} (part ${i + 1})`,
                content: chunks[i],
                source: 'obsidian',
                cluster: note.cluster,
                tags: note.tags,
                embedding: chunkEmbedding,
                contentHash,
              })
            }

            const edges = await buildSimilarityEdges(docId, firstEmbedding)
            totalEdges += edges
            processed++

            controller.enqueue(
              encode({ type: 'progress', file: shortPath, title: note.title, status: 'ok', nodeId: docId, edges })
            )
          } else {
            // Content unchanged — skip re-embedding and edge rebuilding
            unchanged++
            controller.enqueue(
              encode({ type: 'progress', file: shortPath, title: note.title, status: 'unchanged', nodeId: docId })
            )
          }
        } catch (err) {
          errors++
          controller.enqueue(
            encode({
              type: 'progress',
              file: shortPath,
              title: note.title,
              status: 'error',
              error: err instanceof Error ? err.message : 'Unknown error',
            })
          )
        }

        // Small delay to respect Gemini free-tier rate limits
        await new Promise((r) => setTimeout(r, 150))
      }

      controller.enqueue(encode({ type: 'done', processed, skipped: 0, unchanged, errors, totalEdges }))
      controller.close()
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'application/x-ndjson',
      'Transfer-Encoding': 'chunked',
      'Cache-Control': 'no-cache',
    },
  })
}
