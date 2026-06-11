@AGENTS.md

# Nooscope — Context for Claude

## What this project is
Personal AI second brain / knowledge graph MVP. See full PRD:
https://www.notion.so/synergify/Embedding-Agent-PRD-32896060a52d80ae882eefbc2c7aba73

Core loop: ingest any content → embed with Google AI → store in Neo4j graph → explore via 3D WebGL visualization → query with GraphRAG.

## Current sprint: Sprint 1 (complete)
- Text + URL ingestion ✓
- Gemini embeddings + Neo4j MERGE ✓
- SIMILAR_TO edge auto-generation ✓
- 3D force graph (react-force-graph-3d) ✓
- Semantic search ✓
- GraphRAG streaming answers ✓

## Next sprint: Sprint 2
- Readwise highlights import (Readwise API)
- Browser extension web clipper
- Multimodal embeddings — **sovereign jina-embeddings-v4** (self-hosted, NOT Gemini Embedding 2). Forces dim 768→1024 + full graph re-embed. See `SPRINT2_EMBEDDINGS_ADR.md` before touching embeddings.
- Auto-Brainwriting per cluster
- Dynamic cluster emergence (Louvain algorithm)

## Tech decisions to preserve
- **Embeddings (Sprint 1, current)**: `gemini-embedding-001` (stable GA, 768-dim via `outputDimensionality`; NOT the `-exp-*` previews — Google pulls exp models without notice, NOT text-embedding-004 — deprecated Aug 2025)
- **Embeddings (Sprint 2, decided)**: migrate to sovereign `jina-embeddings-v4` (local, multimodal, 1024-dim) — see `SPRINT2_EMBEDDINGS_ADR.md`
- **LLM**: `gemini-2.5-flash` (stable, free tier 15 RPM; NOT `-preview-*` snapshots)
- **Graph**: Neo4j AuraDB free, Cypher, `MERGE` not `CREATE`
- **3D graph**: imperative API via `ForceGraph3D as any` — the TS types lie, the factory pattern is correct
- **SSR**: graph-3d.tsx must stay `dynamic(..., { ssr: false })` — WebGL requires browser

## Env vars required
See `.env.local` — needs `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `GOOGLE_GENERATIVE_AI_API_KEY`

## Key files
- `src/lib/neo4j.ts` — all Neo4j interactions
- `src/lib/embeddings.ts` — embed() + chunking
- `src/app/api/ingest/route.ts` — main ingestion pipeline
- `src/app/api/graphrag/route.ts` — GraphRAG streaming
- `src/components/graph-3d.tsx` — 3D visualization
