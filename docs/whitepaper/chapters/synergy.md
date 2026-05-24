# Synergy: The Integrated Mesh

The ultimate capacity of Nautilus is found in the deep **synergy** between its components. Rather than operating as isolated tools, they build an integrated, self-healing mesh where the operations of each component enrich the other.

```mermaid
sequenceDiagram
    autonumber
    actor Coder as Solo Vibe Coder
    participant CLI as facet CLI (enerv)
    participant Meta as .facets/meta.json
    participant Proxy as LiteLLM Proxy
    participant DB as Neo4j Graph DB
    participant UI as Nooscope 3D UI

    Coder->>CLI: facet ingest "Atlas/Notes/Refactoring.md"
    activate CLI
    CLI->>Meta: Resolve parent meta.json schema
    activate Meta
    Meta-->>CLI: Return context (Team=Core, Priority=High, Status=Active)
    deactivate Meta
    
    CLI->>CLI: Segment text into normalized chunks & hash
    
    CLI->>Proxy: Request embedding for text chunks
    activate Proxy
    Proxy-->>CLI: Return 768-dim vector embeddings
    deactivate Proxy

    CLI->>DB: Execute MERGE transactions (Docs, Metadata, Vectors)
    activate DB
    DB->>DB: Identify similarities & link SIMILAR_TO edges
    DB-->>CLI: Confirm transaction success
    deactivate DB
    
    CLI-->>Coder: Ingestion complete (Console summary)
    deactivate CLI

    UI->>DB: Fetch active nodes & semantic links
    activate DB
    DB-->>UI: Return graph coordinates & properties
    deactivate DB
    UI->>Coder: Render live 3D visual cluster update
```

## Core Synergistic Workflows

### 1. Metadata-Aware Ingestion
When the coder executes `facet ingest my_note.md`, the ingestion pipeline does not treat the document as a simple, unstructured text dump.
- **Context Boundary Check**: The indexer ascends the directory path to resolve the closest `.facets/meta.json` file.
- **Context Enrichment**: It automatically merges parameters (e.g., project team, priority level, execution status) into the node properties.
- **Multi-Dimensional Graph**: The database creates a node queryable both by raw semantic meaning (vector similarity) and system-wide structural tags (metadata). This allows for complex searches like: *"Find all high-priority notes linked to the game engine database optimization."*

### 2. Dynamic 3D Context Navigation
The `facet visualize` command links the command-line workspace to the visual brain.
- **Instant Mapping**: By analyzing the active working directory, the Next.js visualizer loads the exact node neighborhood on your screen.
- **Emergent Overlaps**: Seeing physical cluster separations allows the developer to identify hidden conceptual redundancies, circular task loops, and structural gaps.

### 3. Agentic Context Injection
Because ENERV and the Knowledge Graph share unified Pydantic schemas, autonomous agents (Aider, Cline) operating in the orchestration layer can execute context-rich operations.
- **Example Scenario**: An agent tasked with "Resolving port collisions" checks the indexer for services listed under `/config/services.json` and simultaneously queries the Graph for all previous incident reports and documentation files containing "port broker design". The agent receives a hyper-focused, bitemporal context package, preventing "context sprawl" and protecting model reasoning performance.

### 4. Unified Lifecycles
A single startup script orchestrates the monorepo's resilient stack:
- **`master-restart.ps1`**: Queries the port broker, allocates free local sockets (LiteLLM, Neo4j, llama-server, Next.js), writes dynamic variables to `.env` and `.env.local`, and bootstraps all services concurrently.
- **Shared `.env`**: A single source of truth for local paths, database logins, and model aliases, preventing environment drift.
