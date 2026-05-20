# MVP Testing Guide

## Quick Validation (15 minutes)

### Test 1: Vector Index Creation
```bash
npm run dev
# Navigate to http://localhost:3000/ingest

# Steps:
1. Paste your Obsidian vault path (e.g., C:/Users/sasha/Documents/Obsidian/LifeBook)
2. Click "Ingest"
3. Watch progress stream
4. Expect: "Done" with count of processed notes

# Verify in Neo4j Browser:
MATCH (d:Document) RETURN count(d) as total_documents
# Should return ~38 nodes

# Check vector dimensions:
MATCH (d:Document) WHERE d.embedding IS NOT NULL
RETURN d.id, size(d.embedding) as dimension LIMIT 1
# Should return: dimension = 768
```

**Expected Result**: ✅ No dimension mismatch errors, documents stored with 768-dim embeddings

---

### Test 2: Semantic Search with Multilingual Content
```bash
# In search tab at http://localhost:3000

# Test multilingual search:
- Query: "energy"
- Expected: Returns both English notes about energy AND Russian notes (энергия, энергетика)

# Test 0.75 threshold:
- Query: "meditation"
- Expected: Returns notes about meditation AND related concepts (mindfulness, breathwork, chakras)
  because 0.75 threshold is lenient enough to find semantic neighbors

# Verify threshold isn't too low:
- Query: "random text xyz abc"
- Expected: Returns NO results (no matches above 0.75 threshold)
```

**Expected Result**: ✅ Multilingual matches appear, threshold filtering works

---

### Test 3: Similarity Edges in Graph
```bash
# In Neo4j Browser:
MATCH (d:Document)-[r:SIMILAR_TO]-(s:Document)
RETURN d.title, s.title, r.score
ORDER BY r.score DESC
LIMIT 10

# Expected: See 10+ SIMILAR_TO relationships with scores between 0.75-0.95
# Example results:
# - "Chakra System" → "Energy Anatomy" (score: 0.89)
# - "Meditation Practice" → "Mindfulness Guide" (score: 0.82)
# etc.
```

**Expected Result**: ✅ SIMILAR_TO edges created, scores reasonable (0.75-0.95 range)

---

### Test 4: 3D Graph Rendering
```bash
# In graph tab at http://localhost:3000

# Steps:
1. Wait for force layout to stabilize (~5 seconds)
2. Check node count display (top-left): should show "~150 nodes · ~200 edges"
3. Click a node → camera should fly to it, panel shows content
4. Look for node images rendering (if vault has images)

# Expected in console: no WebGL errors
```

**Expected Result**: ✅ Graph renders smoothly, node interaction works, no crashes

---

### Test 5: Chunk Overlap Validation
```bash
# Create a long note (>400 words) in Obsidian
# Ingest vault again

# In Neo4j Browser:
MATCH (d:Document) WHERE d.id LIKE '%chunk%'
RETURN d.id, d.title, size(d.embedding) as dim
# Should see multiple chunk nodes for long documents

# Test chunk search:
# Create a search query that matches phrase in the middle of a long document
# Expected: Search returns the document (overlap helps span boundaries)
```

**Expected Result**: ✅ Long documents chunked with overlap, semantic search works across chunks

---

## Troubleshooting

### Error: "Index does not support querying with vectors of dimension 768"
**Cause**: Vector index still configured for wrong dimension
**Fix**: Check `src/lib/neo4j.ts` line 49 — should be `vector.dimensions: 768`

### Error: "Index document_embeddings does not exist"
**Cause**: Schema initialization failed
**Fix**:
1. Check Neo4j connection in `.env.local`
2. Manually run `CALL db.indexes()` in Neo4j Browser to verify index creation
3. Drop and recreate: `DROP INDEX document_embeddings; POST /ingest again`

### Search returns no results
**Cause**: Vector similarity below 0.75 threshold
**Fix**: Temporarily lower threshold in `buildSimilarityEdges()` from 0.75 → 0.70, re-ingest
**Or**: Query may be too generic — try more specific terms

### Graph doesn't render
**Cause**: WebGL not supported or disabled
**Fix**: Check browser console (F12) for WebGL errors
**Or**: Try a different browser (Chrome/Edge have better WebGL support)

### Images don't show in node viewer
**Cause**: Image path rewriting failed in `stripObsidianSyntax()`
**Fix**:
1. Check browser Network tab for 404 on `/api/vault-image/*`
2. Verify image file exists at path
3. Check `.env.local` has correct `OBSIDIAN_VAULT_PATH`

---

## Performance Benchmarks (Expected)

| Metric | Expected | Notes |
|--------|----------|-------|
| Ingest time per note | <100ms | With overlap chunks |
| Graph rendering (200 nodes) | <2 sec | Force layout stabilization |
| Search latency | <500ms | Vector query + top-10 results |
| Memory (running app) | <200MB | Node process + Chrome render |

If performance is worse:
- Check Neo4j has vector index (not doing full-table scans)
- Profile with DevTools Performance tab
- Consider pagination for 500+ nodes

---

## Sign-Off Checklist

Before declaring MVP ready for user testing:

- [ ] No console errors on ingest
- [ ] Vector dimensions verified as 768 in Neo4j
- [ ] SIMILAR_TO edges created (10+ edges visible)
- [ ] Semantic search returns relevant results
- [ ] Multilingual matches work (Russian ↔ English)
- [ ] 3D graph renders smoothly
- [ ] Node viewer shows content + images
- [ ] No performance issues (<2 sec for render, <500ms for search)
- [ ] Obsidian frontmatter parsed correctly (title, tags, metadata)
- [ ] All 38 notes from test vault ingested successfully

**Status**: ✅ Ready for testing once validation passed
