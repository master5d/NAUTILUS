# NAUTILUS — Personal Knowledge Mesh & Data Graph

**NAUTILUS** is a unified autonomous environment for personal knowledge management, project indexing, and AI orchestration. It is built on the **SOVRN Architecture** (the sovereignty-first, local-first agentic stack & principles).

Unified autonomous environment for personal knowledge management, project indexing, and AI orchestration.

## 🏗 Architecture (Monorepo)

- **`/apps/knowledge-graph`**: 3D WebGL visualization and GraphRAG (Next.js 16, Neo4j, Gemini).
- **`/core/enerv`**: Faceted indexing system and metadata management (Python CLI).
- **`/config`**: Centralized configurations (LiteLLM, agents, services).
- **`/scripts`**: Lifecycle and startup automation.
- **`/hermes`**: Agent gateway and orchestration logic.

## 🚀 Quick Start

### 1. Environment Setup
Copy root `.env` and fill in your keys (Google AI, Neo4j):
```bash
cp .env.example .env # or edit existing .env
```

### 2. Launch Services
Use the canonical startup script:
```powershell
./scripts/hermes_startup.ps1
```

### 3. Integrated Workflow (CLI)
The `facet` CLI (from ENERV) is now the unified interface:

- **Visualize**: Open 3D graph for current context:
  ```bash
  facet visualize .
  ```
- **Ingest**: Add content to the Knowledge Graph with automatic metadata sync:
  ```bash
  facet ingest path/to/note.md
  ```
- **Audit**: Check system-wide metadata consistency:
  ```bash
  facet audit
  ```

## 🧠 Synergy Features

- **Unified Ingest**: Files ingested via `facet` automatically pull tags and team assignments from `.facets/meta.json`.
- **Metadata Sync**: ENERV attributes (status, priority, team) are stored as node properties in Neo4j, enabling multi-dimensional graph queries.
- **Hermes Integration**: Sub-agents use the shared index to discover tools and knowledge without manual path mapping.

## 🛠 Tech Stack

- **LLM Proxy**: LiteLLM (OpenRouter, Groq, local fallback).
- **Graph DB**: Neo4j AuraDB.
- **Embeddings**: `gemini-embedding-exp-03-07` via Google AI Studio.
- **UI**: Next.js + Three.js (react-force-graph-3d).
- **Indexer**: Python 3.12 + JSON Schema.

---
*Vibe coded with Sovereignty in mind. (v3.4 — Integrated Mesh)*
