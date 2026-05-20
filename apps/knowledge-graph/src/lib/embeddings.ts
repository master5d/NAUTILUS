import { GoogleGenerativeAI } from '@google/generative-ai'
import crypto from 'crypto'

let genai: GoogleGenerativeAI | null = null

// Generate SHA-256 hash of content for deduplication on re-sync
export function hashContent(text: string): string {
  return crypto.createHash('sha256').update(text).digest('hex')
}

function getGenAI() {
  if (!genai) {
    genai = new GoogleGenerativeAI(process.env.GOOGLE_GENERATIVE_AI_API_KEY!)
  }
  return genai
}

// Chunk text into overlapping segments
export function chunkText(
  text: string,
  maxWords: number = 400,
  overlapWords: number = 50
): string[] {
  const words = text.split(/\s+/).filter(Boolean)
  if (words.length <= maxWords) return [text]

  const chunks: string[] = []
  let i = 0
  while (i < words.length) {
    const chunk = words.slice(i, i + maxWords).join(' ')
    chunks.push(chunk)
    i += maxWords - overlapWords
  }
  return chunks
}

// Normalize text before embedding
export function normalizeText(text: string): string {
  return text
    .replace(/\s+/g, ' ')
    // Keep all unicode letters/numbers — removes only control chars and zero-width junk
    .replace(/[\p{Cc}\p{Cf}]/gu, '')
    .trim()
    .slice(0, 8000) // gemini-embedding-001 supports 8192 tokens ~= 6000 words
}

// Embed a single text string — returns 768-dim vector
export async function embed(text: string): Promise<number[]> {
  const model = getGenAI().getGenerativeModel({
    model: 'gemini-embedding-001',
  })

  const result = await model.embedContent(normalizeText(text))
  return result.embedding.values
}

// Embed multiple texts in batch (avoids rate limit by sequential processing)
export async function embedBatch(texts: string[]): Promise<number[][]> {
  const results: number[][] = []
  for (const text of texts) {
    const embedding = await embed(text)
    results.push(embedding)
    // Small delay to respect rate limits
    await new Promise((r) => setTimeout(r, 100))
  }
  return results
}

// Cosine similarity for local comparison
export function cosineSimilarity(a: number[], b: number[]): number {
  const dot = a.reduce((sum, ai, i) => sum + ai * b[i], 0)
  const magA = Math.sqrt(a.reduce((sum, ai) => sum + ai * ai, 0))
  const magB = Math.sqrt(b.reduce((sum, bi) => sum + bi * bi, 0))
  return dot / (magA * magB)
}
