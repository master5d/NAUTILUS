---
name: Nautilus Mesh
type: tool
execution: stateless
description: Query the Nautilus Knowledge Graph semantically, audit project contracts, and ingest files into the vector database.
---

# Nautilus Mesh Skill

This skill equips AI agents (Aider, Cline, Claude Code) and orchestrators (Hermes) with structural and semantic tools to interact with the **Nautilus monorepo knowledge mesh**.

## Capabilities

AI agents should invoke this skill to find relevant codebase patterns, search reference archives, audit structural meta contracts, or publish new learnings upon completing a task.

### 1. Semantic Search
Search the bitemporal vector database for related documentation, snippets, or code utilities:
* **Tool Name**: `facet_search`
* **CLI Command**: `facet search "<query>"`
* **Usage**: Use this to find relevant conceptual neighbors across multiple projects without reading the directory structure recursively.

### 2. GraphRAG Synthesis
Ask complex reasoning questions that synthesize connections across multiple graph nodes:
* **Tool Name**: `facet_graphrag`
* **CLI Command**: `facet graphrag "<question>"`
* **Usage**: Use this to resolve structural contradictions or explore high-level design relationships between different parts of the workspace.

### 3. File Ingestion
Ingest a newly written or modified file (markdown logs, design sheets, or specifications) directly into the knowledge mesh:
* **Tool Name**: `facet_ingest`
* **CLI Command**: `facet ingest "<file_path>"`
* **Usage**: Execute this after completing a task to ensure your output is indexed and visible to subsequent agent sessions.

### 4. Structural Project Audit
Audit structural `.facets/meta.json` boundaries and schema health inside project directories:
* **Tool Name**: `facet_audit`
* **CLI Command**: `facet audit`
* **Usage**: Run this before concluding a code task to verify that you did not introduce "context drift" or schema violations.

---

## Related Skills
- PR Review
- Code Reviewer
- Architect Framing
