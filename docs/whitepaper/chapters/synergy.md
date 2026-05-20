# Synergy: The Integrated Mesh

The true power of SOVRN lies in the synergy between its components. It is not just a collection of tools, but an integrated mesh where the sum is greater than the parts.

## 1. Metadata-Aware Ingestion
When you run `facet ingest my_note.md`, the system doesn't just treat the file as raw text.
- **Context Lookup**: It searches for the nearest `.facets/meta.json`.
- **Enrichment**: It attaches "Team", "Project Status", and "Tags" to the ingestion request.
- **Multidimensional Graph**: In Neo4j, your nodes are now searchable by both semantic content *and* systemic metadata. You can ask: *"Show me all high-priority research notes for the AI team."*

## 2. Dynamic 3D Context Navigation
The `facet visualize` command bridges the gap between the terminal and the visual brain.
- **Instant Access**: Open a spatial representation of your project folder.
- **Cluster Emergence**: See how different files relate across projects, potentially discovering overlaps you didn't know existed.

## 3. Agentic Context Injection
Because ENERV and the Knowledge Graph share a common schema, agents in the `hermes` layer can perform "Cross-Project Reasonings."
- **Scenario**: An agent tasked with "Optimizing deployment" can consult ENERV for the current `status` of all relevant projects and the Knowledge Graph for the actual `deploy.md` logs and documentation.

## 4. Unified Life-Cycle
The `scripts/` directory provides a single point of failure-resistance and orchestration.
- **hermes_startup.ps1**: Launches the LLM servers, the Python indexer, the Neo4j connection, and the Next.js frontend in one orchestrated sequence.
- **Unified .env**: One source of truth for API keys and database credentials across all Python, Node.js, and Bash components.
