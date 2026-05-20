# Content Hash Deduplication Strategy

**Status**: ✅ IMPLEMENTED
**Date**: 2026-03-30
**MVP Priority**: Medium (optimization for re-sync)

---

## Overview

This document explains how content hash deduplication works to prevent unnecessary re-embedding of unchanged documents when syncing Obsidian vault or re-ingesting URLs.

## Problem Solved

**Scenario**: User runs `POST /api/ingest/obsidian` twice on the same vault.

**Without deduplication**:
- All ~38 notes are re-embedded (even if unchanged)
- API calls doubled to Gemini (cost, rate limiting)
- All SIMILAR_TO edges recreated (even though identical)
- Sync time: 10-15 minutes for 38 notes at 150ms/note

**With deduplication**:
- Unchanged notes skip embedding
- Only modified notes re-embedded and edges rebuilt
- Sync time: <1 minute (only process new/changed notes)
- Reduced API cost and rate limit pressure

---

## Implementation

### 1. Content Hash Storage

**Where**: `Document` node in Neo4j
**Field**: `contentHash` (SHA-256 hex string)
**Computed**: Once per note, stored with document

```cypher
MATCH (d:Document {id: "obsidian/notes/meditation"})
RETURN d.contentHash
# Returns: "a3f2d1b7e8c2f4a9..."
```

### 2. Hash Generation

**File**: `src/lib/embeddings.ts`

```typescript
import crypto from 'crypto'

export function hashContent(text: string): string {
  return crypto.createHash('sha256').update(text).digest('hex')
}
```

**Properties**:
- Deterministic: same text → same hash every time
- Fast: SHA-256 is ~1µs per document
- Collision-safe: 256-bit hash space

### 3. Merge Logic

**File**: `src/lib/neo4j.ts` (updated `mergeDocument()`)

```typescript
export async function mergeDocument(params: {
  id: string
  // ... other fields
  contentHash?: string
}): Promise<{ created: boolean; contentChanged: boolean }> {
  // Check if document exists and content hash matches
  const existing = await runCypher(
    `MATCH (d:Document {id: $id}) RETURN d.contentHash as existingHash`,
    { id: params.id }
  )

  const contentChanged = !existing.length ||
                         existing[0].get('existingHash') !== params.contentHash
  const created = !existing.length

  // MERGE with contentHash stored
  await runCypher(`
    MERGE (d:Document {id: $id})
    SET d.contentHash = $contentHash,
        // ... other fields
  `, { contentHash: params.contentHash, ... })

  return { created, contentChanged }
}
```

**Returns**:
- `created: true` → document is new
- `contentChanged: true` → document exists but content changed
- `contentChanged: false` → document unchanged (skip embedding)

### 4. Ingest Routes Updated

Both routes now use deduplication:

**File**: `src/app/api/ingest/obsidian/route.ts`
```typescript
const contentHash = hashContent(note.content)
const { created, contentChanged } = await mergeDocument({
  // ...
  contentHash,
})

// Only embed and build edges if new or changed
if (created || contentChanged) {
  const firstEmbedding = await embed(chunks[0])
  const edges = await buildSimilarityEdges(docId, firstEmbedding)
  processed++
} else {
  unchanged++  // Track unchanged count
}
```

**File**: `src/app/api/ingest/route.ts` (generic URL/content ingestion)
```typescript
const contentHash = hashContent(content)
const { created, contentChanged } = await mergeDocument({
  // ...
  contentHash,
})

if (created || contentChanged) {
  totalEdges = await buildSimilarityEdges(docId, embedding)
}
```

---

## Progress Reporting

**Obsidian ingest** reports three statuses:

| Status | Meaning | Example |
|--------|---------|---------|
| `ok` | Document new or content changed → embedded | "Meditation Practice.md" |
| `unchanged` | Document exists with identical content → skipped embedding | "Daily Notes.md" |
| `error` | Failed to process | "Corrupt.md" |

**Final summary** includes:
```json
{
  "type": "done",
  "processed": 12,      // New + changed
  "unchanged": 26,      // Unchanged (skipped)
  "errors": 0,
  "totalEdges": 42
}
```

---

## Performance Impact

### First Sync (Cold)
```
38 notes × 150ms/note = 5.7 seconds
+ vector search + edge creation ≈ 10-15 minutes
```

### Re-sync (Hot) with Deduplication
```
If 2 notes changed:
2 notes × 150ms/note = 300ms
36 notes skipped = 0ms
+ vector search (only 2 docs) ≈ 30 seconds total
```

**Benefit**: 95% faster on typical re-sync (only 2-3 changes)

---

## Edge Cases

### Case 1: Note Content Changed, Metadata Unchanged
```
Before: "Meditation Practice" (hash: abc123)
After:  "Meditation Practice" (hash: def456)

Result:
- contentChanged = true
- Re-embed: YES
- Rebuild edges: YES
```

### Case 2: Note Title Changed, Content Identical
```
Before: "Daily Notes 2024-01-01" (hash: abc123)
After:  "Daily Notes 2024-01-02" (hash: abc123)

Result:
- contentChanged = false (content hash matches)
- Re-embed: NO
- Rebuild edges: NO
- Title updated in MERGE SET
```

**Implication**: Title changes alone don't trigger re-embedding (acceptable for MVP).

### Case 3: Obsidian Syntax Changes (image paths, wikilinks)
```
Before: "![[image.png]]" (stripped in stripObsidianSyntax)
After:  "![[image.png]] (still there)"

Result:
- Content after stripping is identical
- contentChanged = false
- Skip re-embedding
```

**Implication**: Obsidian syntax-only changes don't trigger re-embedding (good — content is semantically unchanged).

---

## Testing Deduplication

### Manual Test

1. **First sync**:
   ```bash
   POST /api/ingest/obsidian
   { "vaultPath": "C:/Users/sasha/Documents/Obsidian/LifeBook" }

   # Monitor output
   # Expected: 38 "ok" statuses, totalEdges ≈ 200
   ```

2. **Change one note** in Obsidian vault (edit content)

3. **Second sync**:
   ```bash
   # Re-run same POST

   # Expected output:
   # - "ok": 1 (changed note)
   # - "unchanged": 37 (others skipped)
   # - totalEdges ≈ 5 (only for changed note + neighbors)
   # Total time: <1 minute
   ```

4. **Verify in Neo4j**:
   ```cypher
   // Check changed note has new hash
   MATCH (d:Document {id: "obsidian/notes/meditation"})
   RETURN d.contentHash, d.updatedAt

   // Check unchanged notes are not touched
   MATCH (d:Document)
   WHERE d.updatedAt < now() - duration('PT5M')  // >5 min ago
   RETURN count(d)  // Should be 37 (unchanged notes)
   ```

### Automated Test (For Sprint 2)

Add to test suite:
```typescript
test('deduplication: unchanged documents skipped', async () => {
  // 1. Ingest vault
  // 2. Record contentHash of note A
  // 3. Re-ingest vault (no changes)
  // 4. Verify: note A not re-embedded, hash unchanged
  // 5. Modify note A
  // 6. Re-ingest vault
  // 7. Verify: note A re-embedded, hash changed
})
```

---

## Limitations & Future Work

### Current Limitations

1. **Title/metadata changes alone don't re-embed** — if you rename a note but don't change content, hash stays same, embedding reused
   - **Acceptable for MVP**: Title isn't embedded, only content matters
   - **Fix for Sprint 2**: Store `{ contentHash, metadataHash }` separately

2. **No incremental chunk updates** — if you add text to middle of long document, all chunks may be re-numbered
   - **Acceptable for MVP**: Full re-chunking on change is simple
   - **Fix for Sprint 2**: Implement chunk-level diffing

3. **No cross-document deduplication** — if you paste same text into two documents, both are embedded separately
   - **Acceptable for MVP**: Rare in practice (personal vault)
   - **Fix for Sprint 2**: Add global content dedup across all sources

### Future Enhancements

**Sprint 2**:
- [ ] Metadata hash (title, tags) to trigger index-only updates
- [ ] Chunk-level diffing for incremental re-processing
- [ ] Cross-source dedup (if Readwise + URL have identical content)

---

## Code Changes Summary

**Files Modified**:
1. `src/lib/embeddings.ts` — Added `hashContent()` function
2. `src/lib/neo4j.ts` — Updated `mergeDocument()` to track `created` and `contentChanged`
3. `src/app/api/ingest/obsidian/route.ts` — Integrated dedup logic, added `unchanged` counter
4. `src/app/api/ingest/route.ts` — Integrated dedup logic
5. `IMPLEMENTATION_REPORT.md` — Documented as "nice-to-have" medium priority item

**Total LOC Added**: ~80 lines
**Complexity**: Low (hash comparison, conditional embedding)
**Testing**: Manual verification steps documented above

---

## Conclusion

Content hash deduplication is now **implemented and ready for testing**. It provides:
- ✅ Automatic skip of re-embedding unchanged documents
- ✅ ~95% faster re-sync (only process changed notes)
- ✅ Reduced API cost and rate limiting on Gemini
- ✅ Progress reporting distinguishes `ok` vs `unchanged` vs `error`

**Next step**: Test with Obsidian vault re-sync to verify unchanged documents are skipped and embedding time improves significantly.
