import { NextRequest } from 'next/server'
import { vectorSearch, runCypher } from '@/lib/neo4j'
import { embed } from '@/lib/embeddings'
import { GoogleGenerativeAI } from '@google/generative-ai'

const genai = new GoogleGenerativeAI(process.env.GOOGLE_GENERATIVE_AI_API_KEY!)

async function fetchSubgraph(anchorIds: string[]): Promise<string> {
  if (!anchorIds.length) return 'No relevant nodes found in knowledge base.'

  // Expand 1-2 hops from anchor nodes
  const records = await runCypher(
    `
    MATCH (anchor:Document)
    WHERE anchor.id IN $ids
    OPTIONAL MATCH (anchor)-[r:SIMILAR_TO|BELONGS_TO|TAGGED]-(neighbor)
    RETURN anchor.id AS anchorId, anchor.title AS anchorTitle,
           anchor.content AS anchorContent,
           type(r) AS relType,
           CASE WHEN neighbor IS NOT NULL THEN neighbor.title ELSE null END AS neighborTitle,
           CASE WHEN neighbor IS NOT NULL THEN neighbor.id ELSE null END AS neighborId
    LIMIT 30
    `,
    { ids: anchorIds }
  )

  if (!records.length) return 'No context found for this query.'

  const lines: string[] = []
  const seen = new Set<string>()

  for (const r of records) {
    const anchorTitle = r.get('anchorTitle') as string
    const anchorContent = r.get('anchorContent') as string | null
    const relType = r.get('relType') as string | null
    const neighborTitle = r.get('neighborTitle') as string | null

    if (!seen.has(anchorTitle)) {
      seen.add(anchorTitle)
      lines.push(`📄 ${anchorTitle}`)
      if (anchorContent) lines.push(`   ${anchorContent.slice(0, 300)}...`)
    }

    if (relType && neighborTitle) {
      lines.push(`   → [${relType}] ${neighborTitle}`)
    }
  }

  return lines.join('\n')
}

export async function POST(req: NextRequest) {
  const { question } = await req.json()

  if (!question?.trim()) {
    return new Response('Question is required', { status: 400 })
  }

  try {
    // 1. Embed the question and find anchor nodes
    const queryEmbedding = await embed(question)
    const anchors = await vectorSearch(queryEmbedding, 5, 0.6)
    const anchorIds = anchors.map((a) => a.id)

    // 2. Fetch subgraph around anchors
    const graphContext = await fetchSubgraph(anchorIds)

    // 3. Stream answer with Gemini
    const model = genai.getGenerativeModel({ model: 'gemini-2.5-flash' })

    const prompt = `You are a knowledge assistant helping the user explore their personal knowledge base.

Answer the question thoughtfully using the graph context below. Your answer should:
- Synthesize ideas across multiple nodes when relevant
- Explain the *meaning* of connections, not just name them
- Reference specific documents and relationships to support your reasoning
- Be 2-4 paragraphs — substantive but focused

Format graph citations inline like: (📄 Document Title → [RELATION] → Document Title)

## Knowledge Graph Context:
${graphContext}

## Question:
${question}`

    const result = await model.generateContentStream(prompt)

    const encoder = new TextEncoder()
    const stream = new ReadableStream({
      async start(controller) {
        for await (const chunk of result.stream) {
          const text = chunk.text()
          if (text) controller.enqueue(encoder.encode(text))
        }
        controller.close()
      },
    })

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Transfer-Encoding': 'chunked',
      },
    })
  } catch (err) {
    console.error('[graphrag]', err)
    return new Response(
      err instanceof Error ? err.message : 'GraphRAG failed',
      { status: 500 }
    )
  }
}
