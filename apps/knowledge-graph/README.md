# Nautilus — 3D Interactive Knowledge Graph UI

Nautilus is a personal AI second brain and 3D visual explorer, running on the **SOVRN Architecture** (sovereignty-first local stack).

**PRD**: https://www.notion.so/synergify/Embedding-Agent-PRD-32896060a52d80ae882eefbc2c7aba73

A personal AI second brain: ingest any content → embed it → explore it as a self-organizing 3D knowledge graph → query it with natural language.

---

## Vision (from PRD)

Multiple classes of knowledge stored in a unified graph:
- Files (txt, md, pdf) and web URLs
- Browser bookmarks, social media saves, playlists
- **Highlights** (most important class — citable, uniquely attributed)
- Notes (Evernote, Notion), AI chat logs

Interface: terminal-like dashboard with a **3D interactive knowledge graph** (Google Earth-style, like Obsidian graph view). Clusters emerge from folder structure, then self-organize as new connections form.

Reference UI inspiration: https://www.miromind.ai

---

## Current State (Sprint 1 — MVP)

### What works
- **Ingest**: paste text or a URL → auto-embeds → stores in Neo4j → auto-links to similar nodes
- **3D Graph**: WebGL force-directed visualization, colored by cluster, click node to view content
- **Semantic Search**: vector cosine similarity across the knowledge base
- **GraphRAG**: finds relevant subgraph → streams answer with graph citations

### Sprint 2 (not yet built)
- Readwise highlights import + sync
- Browser extension (web clipper)
- Image / audio / video multimodal embeddings
- Auto-Brainwriting from cluster dashboard
- Dynamic cluster emergence (Louvain community detection)

---

## Stack (all free)

| Layer | Technology | Free tier |
|-------|-----------|-----------|
| Framework | Next.js 16 (Turbopack) | — |
| Embeddings | `gemini-embedding-001` (stable GA) via Google AI Studio | 10M tokens/min |
| LLM | `gemini-2.5-flash` (stable) | 15 RPM, 1000 req/day |
| Graph DB | Neo4j AuraDB | 200k nodes, 400k rels |
| 3D viz | `react-force-graph-3d` (Three.js) | MIT |
| UI | shadcn/ui + Geist, dark mode | MIT |

---

## Setup

### 1. Neo4j AuraDB (free)
1. Go to [console.neo4j.io](https://console.neo4j.io)
2. Create a free instance
3. Copy URI, username, password

### 2. Google AI Studio (free)
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click "Get API key"

### 3. Fill in `.env.local`
```
NEO4J_URI=neo4j+s://XXXXXXXX.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j

GOOGLE_GENERATIVE_AI_API_KEY=your-key
```

### 4. Run
```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Project Structure

```
src/
├── app/
│   ├── page.tsx                    # Main UI: 3D graph + side panels
│   └── api/
│       ├── ingest/route.ts         # POST: content → embed → Neo4j
│       ├── graph/route.ts          # GET: full graph for 3D visualization
│       ├── search/route.ts         # POST: semantic vector search
│       └── graphrag/route.ts       # POST: question → subgraph → stream answer
├── components/
│   ├── graph-3d.tsx                # react-force-graph-3d (dynamic, ssr: false)
│   ├── node-viewer.tsx             # Sheet panel: click node to read content
│   ├── ingest-panel.tsx            # Add content: text or URL
│   └── search-panel.tsx            # Semantic search + GraphRAG chat
├── lib/
│   ├── neo4j.ts                    # Driver singleton, MERGE, vector search
│   └── embeddings.ts               # embed() via Google Generative AI SDK
└── types/
    └── knowledge.ts                # KnowledgeNode, GraphData, IngestRequest types
```

---

## Key Architecture Decisions

**Why Neo4j AuraDB**: Graph-native queries (multi-hop traversal, shortest path), native vector index in 5.x, free tier is generous enough for personal use, Cypher is the standard language for graph queries.

**Why gemini-embedding-001**: Stable GA Google embedding model (768-dim via `outputDimensionality`), free via AI Studio. Chosen over `-exp-*` previews on purpose — Google retires experimental embedding models without notice, and changing the embedding model forces a full graph re-embed (vector space differs). `text-embedding-004` was deprecated August 2025. Sprint 2 multimodal (images/video/audio) will move to `gemini-embedding-2-preview` when it reaches GA.

**Why react-force-graph-3d**: Three.js-based, matches the Obsidian/Google Earth 3D vision from PRD, imperative API gives full control. Must be `dynamic(() => import(...), { ssr: false })` — uses WebGL + window.

**Entity resolution**: All nodes use `MERGE` not `CREATE` — same URL or normalized title = same node. Prevents duplicates when the same content is ingested twice.

**Similarity edges**: After each ingest, the system runs a vector search against existing nodes and creates `SIMILAR_TO` edges for nodes scoring > 0.82 cosine similarity. This is how the graph self-organizes.

---

## Research Notes

From "Building Applications with AI Agents" (Albada, O'Reilly 2025), Ch. 6:
- KG construction: data → NER → triples (subject-predicate-object) → ontology → Neo4j → validation → maintenance
- GraphRAG: KG nodes/edges → subgraph retrieval → LLM synthesis. Better than flat RAG for multi-hop questions.
- Dynamic KGs are hard: incremental updates, entity resolution drift, resource intensity are the main challenges.

Real-world updates (2026):
- **LightRAG** (EMNLP 2025): 84% GraphRAG quality at 1/100th cost — 6000x cheaper
- **Hybrid approach wins**: retrieve subgraph → 200K context LLM (not full graph dump)
- **200K context** = 83% accuracy; 1M context = 67% accuracy (more ≠ better)
- **KuzuDB archived** by Apple Oct 2025 — do not use
- **FalkorDB** is 6.7x faster than Neo4j but source-available license
