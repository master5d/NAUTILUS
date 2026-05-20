import { NextRequest } from 'next/server'

export async function POST(req: NextRequest) {
  const { url } = await req.json()

  if (!url?.trim()) {
    return Response.json({ error: 'URL is required' }, { status: 400 })
  }

  try {
    const res = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; EmbeddingAgent/1.0)' },
      signal: AbortSignal.timeout(10000),
    })

    if (!res.ok) {
      return Response.json({ error: `HTTP ${res.status} fetching ${url}` }, { status: 400 })
    }

    const html = await res.text()
    const text = html
      // Remove scripts and styles entirely
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, ' ')
      .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, ' ')
      // Strip remaining tags
      .replace(/<[^>]+>/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 10000)

    if (!text) {
      return Response.json({ error: 'No readable content found at this URL' }, { status: 400 })
    }

    return Response.json({ text })
  } catch (err) {
    return Response.json(
      { error: err instanceof Error ? err.message : 'Failed to fetch URL' },
      { status: 400 }
    )
  }
}
