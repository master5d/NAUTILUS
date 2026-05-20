import { getDriver } from './src/lib/neo4j'

async function runTests() {
  const driver = getDriver()
  const session = driver.session({ database: process.env.NEO4J_DATABASE ?? 'ca57cf0f' })

  try {
    console.log('🧪 MVP QA Tests\n')

    // Test 1: Document count
    console.log('✅ TEST 1: Document Count')
    const docs = await session.run('MATCH (d:Document) RETURN count(d) as count')
    const docCount = docs.records[0].get('count')
    console.log(`  Total documents: ${docCount}`)
    console.log(`  ${docCount > 30 ? '✅ PASS' : '❌ FAIL'}: Expected ~38 documents\n`)

    // Test 2: Vector dimensions
    console.log('✅ TEST 2: Vector Dimensions')
    const dims = await session.run(`
      MATCH (d:Document) WHERE d.embedding IS NOT NULL
      RETURN d.id, size(d.embedding) as dimension LIMIT 1
    `)
    const dimension = dims.records[0].get('dimension')
    console.log(`  Vector dimensions: ${dimension}`)
    console.log(`  ${dimension === 768 ? '✅ PASS' : '❌ FAIL'}: Expected 768 (not 3072)\n`)

    // Test 3: SIMILAR_TO edges
    console.log('✅ TEST 3: SIMILAR_TO Edges')
    const edges = await session.run('MATCH ()-[r:SIMILAR_TO]-() RETURN count(r) as count')
    const edgeCount = edges.records[0].get('count')
    console.log(`  Total edges: ${edgeCount}`)
    console.log(`  ${edgeCount > 30 ? '✅ PASS' : '❌ FAIL'}: Expected 40+ edges\n`)

    // Test 4: Content hash deduplication
    console.log('✅ TEST 4: Content Hash Deduplication')
    const hashes = await session.run(`
      MATCH (d:Document) WHERE d.contentHash IS NOT NULL
      RETURN count(d) as count
    `)
    const hashCount = hashes.records[0].get('count')
    console.log(`  Documents with contentHash: ${hashCount}`)
    console.log(`  ${hashCount > 30 ? '✅ PASS' : '❌ FAIL'}: Expected ~38 documents with hash\n`)

    // Test 5: Similarity scores distribution
    console.log('✅ TEST 5: Similarity Score Distribution')
    const scores = await session.run(`
      MATCH (a:Document)-[r:SIMILAR_TO]-(b:Document)
      RETURN min(r.score) as min_score, avg(r.score) as avg_score, max(r.score) as max_score
    `)
    const rec = scores.records[0]
    const minScore = rec.get('min_score')
    const avgScore = rec.get('avg_score')
    const maxScore = rec.get('max_score')
    console.log(`  Score range: ${minScore.toFixed(3)} - ${maxScore.toFixed(3)} (avg: ${avgScore.toFixed(3)})`)
    console.log(`  ${minScore >= 0.75 ? '✅ PASS' : '⚠️  WARNING'}: Min score should be >= 0.75 (threshold)\n`)

    // Summary
    console.log('🎯 QA SUMMARY')
    const allPass = docCount > 30 && dimension === 768 && edgeCount > 30 && hashCount > 30 && minScore >= 0.75
    console.log(allPass ? '✅ ALL TESTS PASSED - MVP READY FOR TESTING' : '❌ SOME TESTS FAILED')

  } finally {
    await session.close()
    await driver.close()
  }
}

runTests().catch(console.error)
