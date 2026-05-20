# Architecture Overview

SOVRN follows a **Modular Monorepo Architecture**, separating concerns while maintaining a unified state.

## The Three Layers

### 1. The Metadata Layer (The Compass)
Located in `/core/enerv`. This layer provides systemic awareness. It uses "Faceted Indexing" to categorize every folder on your disk. It doesn't look *at* the content, but *around* it (metadata, tags, team, status).

### 2. The Semantic Layer (The Brain)
Located in `/apps/knowledge-graph`. This layer understands the "meaning" of your data. It uses vector embeddings to find connections between disparate pieces of information and stores them in a Graph Database (Neo4j).

### 3. The Orchestration Layer (The Pilot)
Located in `/hermes`. This layer is where action happens. It uses LiteLLM and specialized agents to execute tasks based on the context provided by the Metadata and Semantic layers.

## Data Flow: The Ingestion Pipeline

1. **Discovery**: ENERV scans the `TECH_ROOT` and `KNOWLEDGE_ROOT`.
2. **Classification**: `meta.json` files define the project context.
3. **Ingestion**: The `facet ingest` command sends content + metadata to the Knowledge Graph API.
4. **Embedding**: Gemini generates 768-dim vectors.
5. **Graph Construction**: Neo4j creates `Document` nodes and `SIMILAR_TO` edges.
6. **Visualization**: The Next.js frontend renders the 3D graph.

## Structural Map

```text
SOVRN/
├── apps/               # User-facing applications (Next.js)
├── core/               # Systemic tools (Python/CLI)
├── config/             # Shared service configs
├── scripts/            # Automation & Lifecycle
└── hermes/             # Agent orchestration
```
