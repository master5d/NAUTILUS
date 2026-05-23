import neo4j, { Driver, Integer } from 'neo4j-driver'

let driver: Driver | null = null

export function getDriver(): Driver {
  if (!driver) {
    driver = neo4j.driver(
      process.env.NEO4J_URI!,
      neo4j.auth.basic(
        process.env.NEO4J_USERNAME ?? 'neo4j',
        process.env.NEO4J_PASSWORD!
      ),
      { disableLosslessIntegers: true }
    )
  }
  return driver
}

export async function runCypher(
  cypher: string,
  params: Record<string, unknown> = {}
) {
  const session = getDriver().session({
    database: process.env.NEO4J_DATABASE ?? 'neo4j',
  })
  try {
    const result = await session.run(cypher, params)
    return result.records
  } finally {
    await session.close()
  }
}

// Initialize schema: constraints + vector index
// IMPORTANT: Vector dimensions MUST match the embedding model:
// - gemini-embedding-001 returns 768-dim vectors (used in MVP)
// - gemini-embedding-2-preview returns 768-dim vectors (multimodal, Sprint 2)
export async function initSchema() {
  const constraints = [
    'CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS UNIQUE',
    'CREATE CONSTRAINT highlight_id IF NOT EXISTS FOR (n:Highlight) REQUIRE n.id IS UNIQUE',
    'CREATE CONSTRAINT cluster_id IF NOT EXISTS FOR (n:Cluster) REQUIRE n.id IS UNIQUE',
    'CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (n:Tag) REQUIRE n.name IS UNIQUE',
    'CREATE CONSTRAINT dailylog_date IF NOT EXISTS FOR (n:DailyLog) REQUIRE n.date IS UNIQUE',
  ]

  const vectorIndex = `
    CREATE VECTOR INDEX document_embeddings IF NOT EXISTS
    FOR (n:Document) ON (n.embedding)
    OPTIONS {indexConfig: {\`vector.dimensions\`: 768, \`vector.similarity_function\`: 'cosine'}}
  `

  for (const c of constraints) {
    await runCypher(c)
  }

  // Use procedure for vector index as it is more robust in some 5.x versions
  const indexes = await runCypher('SHOW INDEXES')
  const hasVector = indexes.some(r => r.get('name') === 'document_embeddings')
  
  if (!hasVector) {
    await runCypher(`
      CALL db.index.vector.createNodeIndex('document_embeddings', 'Document', 'embedding', 768, 'cosine')
    `)
  }
}

// Vector similarity search — returns top k nodes by cosine similarity
export async function vectorSearch(
  embedding: number[],
  topK: number = 10,
  minScore: number = 0.7
) {
  const records = await runCypher(
    `
    CALL db.index.vector.queryNodes('document_embeddings', $topK, $embedding)
    YIELD node, score
    WHERE score >= $minScore
    RETURN node.id AS id, node.title AS title, node.content AS content,
           node.url AS url, node.source AS source, node.cluster AS cluster,
           score
    ORDER BY score DESC
    `,
    { topK, embedding, minScore }
  )
  return records.map((r) => ({
    id: r.get('id') as string,
    title: r.get('title') as string,
    content: r.get('content') as string | null,
    url: r.get('url') as string | null,
    source: r.get('source') as string,
    cluster: r.get('cluster') as string | null,
    score: r.get('score') as number,
  }))
}

// Merge a document node (create or update)
// Returns { created: boolean, edgesRefreshed: boolean } for tracking re-syncs
export async function mergeDocument(params: {
  id: string
  title: string
  content: string
  url?: string
  source: string
  cluster?: string
  tags?: string[]
  embedding: number[]
  contentHash?: string // SHA-256 hash for deduplication on re-sync
  metadata?: Record<string, any>
}): Promise<{ created: boolean; contentChanged: boolean }> {
  // Check if document exists and content hash matches (prevents re-embedding on re-sync)
  const existing = await runCypher(
    `MATCH (d:Document {id: $id}) RETURN d.contentHash as existingHash, d.id as exists`,
    { id: params.id }
  )

  const contentChanged = !existing.length || existing[0].get('existingHash') !== params.contentHash
  const created = !existing.length

  await runCypher(
    `
    MERGE (d:Document {id: $id})
    ON CREATE SET d.createdAt = datetime()
    SET d.title = $title,
        d.content = $content,
        d.url = $url,
        d.source = $source,
        d.cluster = $cluster,
        d.embedding = $embedding,
        d.contentHash = $contentHash,
        d.metadata = $metadata,
        d.updatedAt = datetime()
    `,
    {
      id: params.id,
      title: params.title,
      content: params.content,
      url: params.url ?? null,
      source: params.source,
      cluster: params.cluster ?? 'default',
      embedding: params.embedding,
      contentHash: params.contentHash ?? null,
      metadata: JSON.stringify(params.metadata ?? {}),
    }
  )

  // Ensure cluster node exists
  if (params.cluster) {
    await runCypher(
      `
      MERGE (c:Cluster {id: $clusterId})
      ON CREATE SET c.name = $clusterName, c.createdAt = datetime()
      WITH c
      MATCH (d:Document {id: $docId})
      MERGE (d)-[:BELONGS_TO]->(c)
      `,
      {
        clusterId: params.cluster.toLowerCase().replace(/\s+/g, '-'),
        clusterName: params.cluster,
        docId: params.id,
      }
    )
  }

  // Attach tags
  if (params.tags?.length) {
    for (const tag of params.tags) {
      await runCypher(
        `
        MERGE (t:Tag {name: $tag})
        WITH t
        MATCH (d:Document {id: $docId})
        MERGE (d)-[:TAGGED]->(t)
        `,
        { tag, docId: params.id }
      )
    }
  }

  return { created, contentChanged }
}

// Find similar documents and create SIMILAR_TO edges
// THRESHOLD = 0.75 (cosine similarity): lowered from 0.82 to account for multilingual content
// (Cyrillic + English notes). This allows the graph to find cross-language connections while
// still avoiding false positives. Trade-off: may create some false-positive SIMILAR_TO edges,
// acceptable for MVP validation. Adjust to 0.80+ in Sprint 2 if tuning becomes needed.
// NOTE: Call this only when contentChanged=true to avoid redundant edge recreation on re-sync.
export async function buildSimilarityEdges(docId: string, embedding: number[]) {
  const similar = await vectorSearch(embedding, 5, 0.75)
  for (const s of similar) {
    if (s.id === docId) continue
    await runCypher(
      `
      MATCH (a:Document {id: $a}), (b:Document {id: $b})
      MERGE (a)-[r:SIMILAR_TO]-(b)
      SET r.score = $score
      `,
      { a: docId, b: s.id, score: s.score }
    )
  }
  return similar.length
}

/**
 * Extract cross-root links like [[tech:project]] or [[knowledge:topic]]
 * and create explicit REFERENCES edges in Neo4j.
 */
export async function buildCrossRootLinks(docId: string, content: string): Promise<number> {
  const linkPattern = /\[\[(tech|knowledge):([^\]]+)\]\]/g
  const matches = [...content.matchAll(linkPattern)]
  let linksCreated = 0

  for (const match of matches) {
    const rootType = match[1] // tech or knowledge
    const targetName = match[2].trim()
    
    // Attempt to find a Document with a title or cluster matching the target
    // and a source matching the rootType.
    await runCypher(
      `
      MATCH (a:Document {id: $a})
      MATCH (b:Document)
      WHERE (b.title CONTAINS $target OR b.cluster CONTAINS $target)
        AND b.source CONTAINS $rootType
      MERGE (a)-[r:REFERENCES {type: 'cross-root'}]->(b)
      RETURN count(r)
      `,
      { a: docId, target: targetName, rootType: rootType }
    )
    linksCreated++
  }
  return linksCreated
}

// Merge a daily log node and link to previous/next chronological nodes
export async function mergeDailyLog(params: {
  date: string      // YYYY-MM-DD
  title: string
  content: string
  source: string
  tags?: string[]
  embedding?: number[]
  contentHash?: string
  metadata?: Record<string, any>
}): Promise<{ created: boolean; contentChanged: boolean }> {
  // Check if DailyLog already exists
  const existing = await runCypher(
    `MATCH (d:DailyLog {date: $date}) RETURN d.contentHash as existingHash, d.id as exists`,
    { date: params.date }
  )

  const contentChanged = !existing.length || existing[0].get('existingHash') !== params.contentHash
  const created = !existing.length

  const id = `daily-log-${params.date}`

  // MERGE standard Document node representing the log file so it shows in 3D graph and vector search
  await mergeDocument({
    id,
    title: params.title,
    content: params.content,
    source: params.source,
    cluster: 'Calendar',
    tags: params.tags,
    embedding: params.embedding ?? Array(768).fill(0), // default empty embedding if none
    contentHash: params.contentHash,
    metadata: params.metadata,
  })

  // MERGE DailyLog node itself
  await runCypher(
    `
    MERGE (dl:DailyLog {date: $date})
    ON CREATE SET dl.createdAt = datetime()
    SET dl.id = $id,
        dl.title = $title,
        dl.content = $content,
        dl.source = $source,
        dl.contentHash = $contentHash,
        dl.updatedAt = datetime()
    `,
    {
      date: params.date,
      id,
      title: params.title,
      content: params.content.slice(0, 2000),
      source: params.source,
      contentHash: params.contentHash ?? null,
    }
  )

  // Link standard Document to DailyLog
  await runCypher(
    `
    MATCH (d:Document {id: $id}), (dl:DailyLog {date: $date})
    MERGE (d)-[:REPRESENTS_LOG]->(dl)
    `,
    { id, date: params.date }
  )

  // Chronological linking: find previous daily log and link (prev)-[:NEXT_DAY]->(curr)
  // And find next daily log and link (curr)-[:NEXT_DAY]->(next)
  await runCypher(
    `
    MATCH (dl:DailyLog {date: $date})
    WITH dl
    // Link to previous day
    OPTIONAL MATCH (prev:DailyLog)
    WHERE prev.date < $date
    WITH dl, prev
    ORDER BY prev.date DESC
    LIMIT 1
    FOREACH (p IN CASE WHEN prev IS NOT NULL THEN [prev] ELSE [] END |
      MERGE (p)-[:NEXT_DAY]->(dl)
    )
    `,
    { date: params.date }
  )

  await runCypher(
    `
    MATCH (dl:DailyLog {date: $date})
    WITH dl
    // Link to next day
    OPTIONAL MATCH (next:DailyLog)
    WHERE next.date > $date
    WITH dl, next
    ORDER BY next.date ASC
    LIMIT 1
    FOREACH (n IN CASE WHEN next IS NOT NULL THEN [next] ELSE [] END |
      MERGE (dl)-[:NEXT_DAY]->(n)
    )
    `,
    { date: params.date }
  )

  return { created, contentChanged }
}

// Link a document to a daily log (representing active cognitive focus on that day)
export async function linkDocumentToDailyLog(docId: string, logDate: string) {
  await runCypher(
    `
    MATCH (d:Document {id: $docId}), (dl:DailyLog {date: $logDate})
    MERGE (d)-[r:LOGGED_ON]->(dl)
    SET r.date = $logDate
    `,
    { docId, logDate }
  )
}

// Link an internal wiki-link mention to a daily log by title or ID contains match
export async function linkMentionToDailyLog(targetTitle: string, logDate: string) {
  // Normalize targetTitle
  const cleanTitle = targetTitle.replace(/\\/g, '/').split('/').pop()?.replace(/\.md$/, '') || targetTitle
  await runCypher(
    `
    MATCH (dl:DailyLog {date: $logDate})
    MATCH (d:Document)
    WHERE d.title = $targetTitle 
       OR d.id CONTAINS $cleanTitle
       OR toLower(d.title) = toLower($cleanTitle)
    MERGE (d)-[r:LOGGED_ON]->(dl)
    SET r.date = $logDate
    `,
    { targetTitle, cleanTitle: cleanTitle.toLowerCase(), logDate }
  )
}
