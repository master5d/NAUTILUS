import { NextRequest } from 'next/server'
import { vectorSearch } from '@/lib/neo4j'
import { embed } from '@/lib/embeddings'

export async function POST(req: NextRequest) {
  try {
    const { query, topK = 10 } = await req.json()

    if (!query?.trim()) {
      return Response.json({ error: 'Query is required' }, { status: 400 })
    }

    const embedding = await embed(query)
    const results = await vectorSearch(embedding, topK, 0.6)

    return Response.json({ results, query })
  } catch (err) {
    console.error('[search]', err)
    return Response.json(
      { error: err instanceof Error ? err.message : 'Search failed' },
      { status: 500 }
    )
  }
}
