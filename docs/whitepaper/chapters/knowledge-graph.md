# Knowledge Graph: 3D Visualization & GraphRAG

**The Knowledge Graph** represents the visual and semantic brain of the Nautilus environment. It maps the meaning of your documents, codebases, and ideas in a dynamic 3D coordinate space, linking vector similarity to systemic metadata relationships.

<div align="center">
  <svg width="100%" height="auto" viewBox="0 0 800 680" style="max-width: 800px; background: #0b0f19; border: 1px solid #1e293b; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); font-family: 'JetBrains Mono', Consolas, monospace;">
    <defs>
      <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
        <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#111827" stroke-width="0.8"/>
      </pattern>
      <marker id="arrow-cyan" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#22d3ee" />
      </marker>
      <marker id="arrow-green" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#34d399" />
      </marker>
      <marker id="arrow-purple" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#a78bfa" />
      </marker>
      <marker id="arrow-amber" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#fbbf24" />
      </marker>
      <marker id="arrow-rose" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#fb7185" />
      </marker>
    </defs>
    
    <!-- Grid Background -->
    <rect width="100%" height="100%" fill="url(#grid)" />
    
    <!-- Title -->
    <text x="30" y="35" fill="#f8fafc" font-size="14" font-weight="bold" letter-spacing="1">SEMANTIC GRAPH PIPELINE</text>
    <text x="30" y="55" fill="#64748b" font-size="10">Active Database Ingestion vs Resilient Offline Fallback</text>
    
    <!-- Source Node -->
    <rect x="290" y="20" width="220" height="40" rx="6" fill="rgba(8, 51, 68, 0.3)" stroke="#22d3ee" stroke-width="1.5" />
    <text x="400" y="44" fill="#22d3ee" font-size="11" font-weight="bold" text-anchor="middle">Markdown Note / Code File</text>
    
    <!-- Normalize Node -->
    <rect x="290" y="85" width="220" height="40" rx="6" fill="rgba(8, 51, 68, 0.3)" stroke="#22d3ee" stroke-width="1.5" />
    <text x="400" y="109" fill="#22d3ee" font-size="10" text-anchor="middle">Text Normalizer &amp; SHA-256</text>
    
    <!-- Check DB Decision Node -->
    <rect x="270" y="150" width="260" height="45" rx="6" fill="rgba(120, 53, 15, 0.2)" stroke="#fbbf24" stroke-width="1.5" />
    <text x="400" y="176" fill="#fbbf24" font-size="11" font-weight="bold" text-anchor="middle">Is Neo4j / FalkorDB Online?</text>
    
    <!-- ACTIVE PATH (Right Side) -->
    <!-- Chunk Node -->
    <rect x="480" y="235" width="260" height="50" rx="6" fill="rgba(6, 78, 59, 0.3)" stroke="#34d399" stroke-width="1.5" />
    <text x="610" y="260" fill="#34d399" font-size="11" text-anchor="middle">Chunk Text &amp; Embeddings</text>
    <text x="610" y="274" fill="#64748b" font-size="8" text-anchor="middle">LiteLLM dynamic routing pool</text>
    
    <!-- Merge Nodes -->
    <rect x="480" y="320" width="260" height="50" rx="6" fill="rgba(6, 78, 59, 0.3)" stroke="#34d399" stroke-width="1.5" />
    <text x="610" y="345" fill="#34d399" font-size="11" text-anchor="middle">Merge Document &amp; Facets</text>
    <text x="610" y="359" fill="#64748b" font-size="8" text-anchor="middle">Create properties &amp; metadata bonds</text>
    
    <!-- Edge Gen -->
    <rect x="480" y="405" width="260" height="50" rx="6" fill="rgba(6, 78, 59, 0.3)" stroke="#34d399" stroke-width="1.5" />
    <text x="610" y="430" fill="#34d399" font-size="11" text-anchor="middle">Generate Cosine SIMILAR_TO</text>
    <text x="610" y="444" fill="#64748b" font-size="8" text-anchor="middle">Forge semantic similarity edges</text>
    
    <!-- Neo4j DB -->
    <rect x="480" y="490" width="260" height="50" rx="6" fill="rgba(136, 19, 55, 0.2)" stroke="#fb7185" stroke-width="1.5" />
    <text x="610" y="520" fill="#fb7185" font-size="12" font-weight="bold" text-anchor="middle">NEO4J / FALKORDB</text>
    
    <!-- OFFLINE FALLBACK PATH (Left Side) -->
    <!-- Obsidian Sweep -->
    <rect x="60" y="235" width="260" height="50" rx="6" fill="rgba(76, 29, 149, 0.3)" stroke="#a78bfa" stroke-width="1.5" />
    <text x="190" y="260" fill="#a78bfa" font-size="11" font-weight="bold" text-anchor="middle">Local Vault export-graph Sweep</text>
    <text x="190" y="274" fill="#64748b" font-size="8" text-anchor="middle">Offline Python parser CLI</text>
    
    <!-- Local Extract -->
    <rect x="60" y="325" width="260" height="50" rx="6" fill="rgba(76, 29, 149, 0.3)" stroke="#a78bfa" stroke-width="1.5" />
    <text x="190" y="350" fill="#a78bfa" font-size="11" text-anchor="middle">Extract Frontmatter &amp; Links</text>
    <text x="190" y="364" fill="#64748b" font-size="8" text-anchor="middle">Parse wiki links [[backlinks]]</text>
    
    <!-- Local Graph -->
    <rect x="60" y="415" width="260" height="50" rx="6" fill="rgba(76, 29, 149, 0.3)" stroke="#a78bfa" stroke-width="1.5" />
    <text x="190" y="440" fill="#a78bfa" font-size="11" text-anchor="middle">Construct Backlink Topology</text>
    <text x="190" y="454" fill="#64748b" font-size="8" text-anchor="middle">Coordinate matrix generation</text>
    
    <!-- WebGL / Nooscope Node -->
    <rect x="270" y="590" width="260" height="55" rx="8" fill="rgba(8, 51, 68, 0.3)" stroke="#22d3ee" stroke-width="1.5" />
    <text x="400" y="618" fill="#22d3ee" font-size="12" font-weight="bold" text-anchor="middle">NOOSCOPE 3D WEBGL VIEW</text>
    <text x="400" y="632" fill="#94a3b8" font-size="8" text-anchor="middle">Interactive force-directed stellar constellation</text>
    
    <!-- CONNECTIONS -->
    <!-- Source --> Normalize -->
    <path d="M 400 60 V 85" fill="none" stroke="#22d3ee" stroke-width="1.5" marker-end="url(#arrow-cyan)" />
    
    <!-- Normalize --> CheckDB -->
    <path d="M 400 125 V 150" fill="none" stroke="#22d3ee" stroke-width="1.5" marker-end="url(#arrow-cyan)" />
    
    <!-- CheckDB --> Chunk (Yes) -->
    <path d="M 400 195 V 215 H 610 V 235" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    <text x="510" y="210" fill="#34d399" font-size="9" text-anchor="middle">Yes</text>
    
    <!-- CheckDB --> ObsidianSweep (No) -->
    <path d="M 400 195 V 215 H 190 V 235" fill="none" stroke="#a78bfa" stroke-width="1.5" marker-end="url(#arrow-purple)" />
    <text x="290" y="210" fill="#a78bfa" font-size="9" text-anchor="middle">No (Offline)</text>
    
    <!-- Chunk --> MergeNodes -->
    <path d="M 610 285 V 320" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    
    <!-- MergeNodes --> EdgeGen -->
    <path d="M 610 370 V 405" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    
    <!-- EdgeGen --> Neo4jDB -->
    <path d="M 610 455 V 490" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    
    <!-- Neo4jDB --> WebGL -->
    <path d="M 610 540 V 565 H 400 V 590" fill="none" stroke="#fb7185" stroke-width="1.5" marker-end="url(#arrow-rose)" />
    
    <!-- ObsidianSweep --> LocalExtract -->
    <path d="M 190 285 V 325" fill="none" stroke="#a78bfa" stroke-width="1.5" marker-end="url(#arrow-purple)" />
    
    <!-- LocalExtract --> LocalGraph -->
    <path d="M 190 375 V 415" fill="none" stroke="#a78bfa" stroke-width="1.5" marker-end="url(#arrow-purple)" />
    
    <!-- LocalGraph --> WebGL -->
    <path d="M 190 465 V 565 H 400 V 590" fill="none" stroke="#a78bfa" stroke-width="1.5" marker-end="url(#arrow-purple)" />
    
  </svg>
</div>

## The Ingestion Pipeline

When you run `facet ingest`, Nautilus executes a multi-stage semantic extraction pipeline:

1. **Normalization & Deduplication**: Text content is stripped of trailing whitespaces and malformed characters. A unique SHA-256 hash is computed for the file. If the hash exists in the database, the ingestion is skipped, preventing node duplication.
2. **Text Chunking**: Files exceeding token boundaries are split into contiguous chunks using a sliding window to preserve context borders.
3. **Embedding Generation**: Chunks are sent to the dynamic LiteLLM gateway (routing by default to high-speed cloud embedders like Google Gemini or falling back to local `BGE-M3` vector engines).
4. **Neo4j Transaction Mapping**:
   - Creates or updates a central `Document` node with metadata attributes (team, status, priority, filepath).
   - Links the document to its respective `Chunk` nodes.
   - Calculates cosine similarity against existing vectors, dynamically forging `SIMILAR_TO` edges to connect related ideas across different projects.

## Visual Intuition: Nooscope 3D UI

The `/apps/knowledge-graph` visualizer runs a WebGL-powered 3D force-directed layout:
- **Interactive Clusters**: Nodes pull together based on semantic similarity and shared project tags, exposing thematic clusters (e.g., all files regarding "SecOps deployment" converge, regardless of whether they exist in `/core/enerv` or `/docs/whitepaper`).
- **GraphRAG Search**: The visualizer features a dedicated sidebar for semantic search. When you query the mesh, the AI fetches the vector neighbors, traverses the graph structure, and feeds a rich GraphRAG context window to the user or agent.

## Resilient Offline Fallback: `walkVault`

A core tenet of the Nautilus architecture is **Sovereignty Under Failure**. If Docker is stopped and the Neo4j database goes offline, the 3D Nooscope UI does not fail:

- **Ambient Traversal**: The system automatically executes a fallback Obsidian note traversal sweep (`walkVault`).
- **Backlink Extraction**: It reads local markdown frontmatter, parses backlinks (e.g., `[[MyOtherNote]]`), and constructs an interactive backlink coordinate network.
- **Result**: You retain a fully functional, highly interactive local-first knowledge graph, even in a total database blackout.

### Visual Transition: From PARA (Tiago Forte) to ACE/LYT (Nick Milo)

The visual design of the Nooscope 3D force layout represents the conceptual shift from **PARA** to **ACE/LYT**:
- **Why PARA Fails in 3D Space**: Under Tiago Forte's PARA model, notes are separated into hard vertical subfolders by "Project" or "Area". In a force-directed WebGL canvas, this forces nodes into separate, disconnected clusters that cannot easily build cross-project connections, causing a fragmented, disjointed "scatter-plot" layout.
- **Why ACE/LYT Thrives in 3D Space**: By structuring notes under Nick Milo's **ACE (Atlas, Calendar, Efforts)** framework, files reside fluidly under unified domains, bridged by **Maps of Content (MOCs)**. On the WebGL canvas, MOCs act as **high-gravity central hub nodes**, beautifully pulling related sub-notes into elegant semantic clusters. This results in an organic, highly interconnected 3D stellar constellation layout, allowing the developer to see holistic conceptual structures emerging naturally.

