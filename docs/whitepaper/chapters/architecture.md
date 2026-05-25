# Architecture Overview

Nautilus follows a **Modular Monorepo Architecture**, separating operational concerns while maintaining a unified bitemporal state across directories.

<div align="center">
  <svg width="100%" height="auto" viewBox="0 0 900 660" style="max-width: 900px; background: #0b0f19; border: 1px solid #1e293b; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); font-family: 'JetBrains Mono', Consolas, monospace;">
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
      <marker id="arrow-slate" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
      </marker>
    </defs>
    
    <!-- Grid Background -->
    <rect width="100%" height="100%" fill="url(#grid)" />
    
    <!-- Title -->
    <text x="30" y="35" fill="#f8fafc" font-size="14" font-weight="bold" letter-spacing="1">NAUTILUS SYSTEM ARCHITECTURE</text>
    <text x="30" y="55" fill="#64748b" font-size="10">Modular Monorepo Topology</text>
    
    <!-- Coder Node -->
    <rect x="360" y="20" width="180" height="40" rx="8" fill="rgba(30, 41, 59, 0.4)" stroke="#94a3b8" stroke-width="1.5" />
    <text x="450" y="44" fill="#f8fafc" font-size="11" font-weight="bold" text-anchor="middle">SOLO VIBE CODER</text>
    
    <!-- Subgraph 1: Orchestration Layer -->
    <rect x="30" y="85" width="380" height="130" rx="10" fill="none" stroke="#1e293b" stroke-width="1.5" stroke-dasharray="4,4" />
    <text x="45" y="105" fill="#64748b" font-size="9" font-weight="bold">ORCHESTRATION LAYER</text>
    
    <!-- Hermes Agent -->
    <rect x="50" y="130" width="150" height="50" rx="6" fill="rgba(8, 51, 68, 0.3)" stroke="#22d3ee" stroke-width="1.5" />
    <text x="125" y="160" fill="#22d3ee" font-size="11" font-weight="bold" text-anchor="middle">HERMES BOSS</text>
    
    <!-- SubAgents -->
    <rect x="230" y="130" width="160" height="50" rx="6" fill="rgba(8, 51, 68, 0.3)" stroke="#22d3ee" stroke-width="1.5" />
    <text x="310" y="160" fill="#22d3ee" font-size="11" font-weight="bold" text-anchor="middle">CODING SUBAGENTS</text>
    
    <!-- Subgraph 2: Model Gateway Layer -->
    <rect x="440" y="85" width="430" height="130" rx="10" fill="none" stroke="#1e293b" stroke-width="1.5" stroke-dasharray="4,4" />
    <text x="455" y="105" fill="#64748b" font-size="9" font-weight="bold">MODEL GATEWAY LAYER</text>
    
    <!-- LiteLLM Proxy -->
    <rect x="470" y="130" width="370" height="50" rx="6" fill="rgba(8, 51, 68, 0.3)" stroke="#22d3ee" stroke-width="1.5" />
    <text x="655" y="160" fill="#22d3ee" font-size="11" font-weight="bold" text-anchor="middle">LITELLM PROXY ROUTER (localhost:4000)</text>
    
    <!-- Subgraph 3: Observability & Tools -->
    <rect x="30" y="240" width="380" height="120" rx="10" fill="none" stroke="#1e293b" stroke-width="1.5" stroke-dasharray="4,4" />
    <text x="45" y="260" fill="#64748b" font-size="9" font-weight="bold">OBSERVABILITY &amp; TOOLS</text>
    
    <!-- OpenLLM & Langfuse -->
    <rect x="50" y="290" width="160" height="50" rx="6" fill="rgba(76, 29, 149, 0.3)" stroke="#a78bfa" stroke-width="1.5" />
    <text x="130" y="320" fill="#a78bfa" font-size="10" font-weight="bold" text-anchor="middle">OPENLLM &amp; LANGFUSE</text>
    
    <!-- facet CLI & Port Broker -->
    <rect x="230" y="290" width="160" height="50" rx="6" fill="rgba(6, 78, 59, 0.3)" stroke="#34d399" stroke-width="1.5" />
    <text x="310" y="320" fill="#34d399" font-size="10" font-weight="bold" text-anchor="middle">FACET CLI &amp; BROKER</text>
    
    <!-- Subgraph 4: Inference Layer -->
    <rect x="440" y="240" width="430" height="205" rx="10" fill="none" stroke="#1e293b" stroke-width="1.5" stroke-dasharray="4,4" />
    <text x="455" y="260" fill="#64748b" font-size="9" font-weight="bold">INFERENCE LAYER</text>
    
    <!-- Local Inference -->
    <rect x="460" y="280" width="390" height="40" rx="6" fill="rgba(6, 78, 59, 0.3)" stroke="#34d399" stroke-width="1.5" />
    <text x="655" y="305" fill="#34d399" font-size="11" font-weight="bold" text-anchor="middle">LOCAL: llama.cpp CUDA GGUF (Qwen3)</text>
    
    <!-- Free Clouds -->
    <rect x="460" y="330" width="390" height="40" rx="6" fill="rgba(120, 53, 15, 0.2)" stroke="#fbbf24" stroke-width="1.5" />
    <text x="655" y="355" fill="#fbbf24" font-size="11" font-weight="bold" text-anchor="middle">FREE: Cerebras / Groq / NIM pools</text>
    
    <!-- Paid Clouds -->
    <rect x="460" y="380" width="390" height="40" rx="6" fill="rgba(136, 19, 55, 0.2)" stroke="#fb7185" stroke-width="1.5" />
    <text x="655" y="405" fill="#fb7185" font-size="11" font-weight="bold" text-anchor="middle">PAID: Anthropic API (Pay-as-you-go)</text>
    
    <!-- Subgraph 5: Bitemporal Memory Layer -->
    <rect x="30" y="385" width="380" height="150" rx="10" fill="none" stroke="#1e293b" stroke-width="1.5" stroke-dasharray="4,4" />
    <text x="45" y="405" fill="#64748b" font-size="9" font-weight="bold">BITEMPORAL MEMORY LAYER</text>
    
    <!-- Fast Path -->
    <rect x="50" y="420" width="340" height="40" rx="6" fill="rgba(120, 53, 15, 0.2)" stroke="#fbbf24" stroke-width="1.5" />
    <text x="220" y="445" fill="#fbbf24" font-size="11" font-weight="bold" text-anchor="middle">FAST PATH: Obsidian ACE Markdown Vault</text>
    
    <!-- Slow Path -->
    <rect x="50" y="480" width="340" height="40" rx="6" fill="rgba(136, 19, 55, 0.2)" stroke="#fb7185" stroke-width="1.5" />
    <text x="220" y="505" fill="#fb7185" font-size="11" font-weight="bold" text-anchor="middle">SLOW PATH: Neo4j / FalkorDB Graph DB</text>
    
    <!-- Subgraph 6: Hosting Fabric -->
    <rect x="30" y="555" width="840" height="85" rx="10" fill="none" stroke="#1e293b" stroke-width="1.5" stroke-dasharray="4,4" />
    <text x="45" y="575" fill="#64748b" font-size="9" font-weight="bold">SOVEREIGN HOSTING FABRIC</text>
    
    <rect x="50" y="590" width="370" height="35" rx="6" fill="rgba(30, 41, 59, 0.3)" stroke="#94a3b8" stroke-width="1.5" />
    <text x="235" y="612" fill="#f8fafc" font-size="10" text-anchor="middle">Surface dev system (Local CUDA)</text>
    
    <rect x="470" y="590" width="370" height="35" rx="6" fill="rgba(30, 41, 59, 0.3)" stroke="#94a3b8" stroke-width="1.5" />
    <text x="655" y="612" fill="#f8fafc" font-size="10" text-anchor="middle">Cloudflare Pages Edge &amp; Hetzner Cloud</text>
    
    <!-- CONNECTIONS -->
    <!-- Coder <--> Hermes -->
    <path d="M 360 40 H 125 V 130" fill="none" stroke="#22d3ee" stroke-width="1.5" stroke-dasharray="2,2" marker-start="url(#arrow-cyan)" marker-end="url(#arrow-cyan)" />
    <text x="242" y="32" fill="#22d3ee" font-size="8" text-anchor="middle">IDE / CLI</text>
    
    <!-- Hermes <--> SubAgents -->
    <path d="M 200 155 H 230" fill="none" stroke="#22d3ee" stroke-width="1.5" marker-start="url(#arrow-cyan)" marker-end="url(#arrow-cyan)" />
    
    <!-- Subagents <--> LiteLLM -->
    <path d="M 390 155 H 470" fill="none" stroke="#22d3ee" stroke-width="1.5" marker-start="url(#arrow-cyan)" marker-end="url(#arrow-cyan)" />
    
    <!-- LiteLLM --> Inference split -->
    <path d="M 655 180 V 230" fill="none" stroke="#64748b" stroke-width="1.5" />
    <path d="M 655 230 H 490 V 280" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    <path d="M 655 230 V 330" fill="none" stroke="#fbbf24" stroke-width="1.5" marker-end="url(#arrow-amber)" />
    <path d="M 655 230 H 820 V 380" fill="none" stroke="#fb7185" stroke-width="1.5" marker-end="url(#arrow-rose)" />
    
    <!-- Subagents <--> Observability -->
    <path d="M 310 180 V 240" fill="none" stroke="#64748b" stroke-width="1.5" />
    <path d="M 310 240 H 130 V 290" fill="none" stroke="#a78bfa" stroke-width="1.5" marker-end="url(#arrow-purple)" />
    <path d="M 310 240 H 310 V 290" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    
    <!-- FacetCLI --> Memory split -->
    <path d="M 310 340 V 375" fill="none" stroke="#64748b" stroke-width="1.5" />
    <path d="M 310 375 H 220 V 420" fill="none" stroke="#fbbf24" stroke-width="1.5" marker-end="url(#arrow-amber)" />
    <path d="M 310 375 H 360 V 480" fill="none" stroke="#fb7185" stroke-width="1.5" marker-end="url(#arrow-rose)" />
    
    <!-- Fast Path --> Slow Path -->
    <path d="M 100 460 V 480" fill="none" stroke="#fbbf24" stroke-width="1.5" marker-end="url(#arrow-amber)" />
    <text x="85" y="474" fill="#fbbf24" font-size="8">SYNC</text>
    
  </svg>
</div>

## The Three Core Layers

### 1. The Metadata Layer (The Compass)
Located in `/core/enerv`. This layer provides systemic environmental awareness. It uses **Faceted Indexing** to categorize every folder on your disk. Rather than analyzing file contents, ENERV looks *around* the files (analyzing metadata schemas, tag hierarchies, team assignments, and project execution priority).

### 2. The Semantic Layer (The Brain)
Located in `/apps/knowledge-graph`. This layer interprets the semantic "meaning" of your data. It uses vector embeddings to map hidden connections between disparate text files and stores them as an active Knowledge Graph inside a Graph Database (Neo4j/FalkorDB).

### 3. The Orchestration Layer (The Pilot)
Located in `/hermes`. This layer is the execution engine. It utilizes a central orchestrator and highly specialized coding agents (Aider, Cline) to execute refactoring tasks and workflows based on the structured context injected from the Compass and Brain layers.

## Data Flow: The Ingestion Pipeline

1. **Discovery**: The `facet` CLI walks the directories to map projects.
2. **Classification**: Local `.facets/meta.json` files define metadata contracts.
3. **Ingestion**: The `facet ingest` Python command processes the file (chunking, cleaning).
4. **Embedding**: Google Gemini or local embedding models generate high-fidelity vector representations.
5. **Graph Construction**: Neo4j builds structured `Document` nodes and dynamically maps `SIMILAR_TO` edges.
6. **Visualization**: Next.js renders the live 3D semantic nodes web for the coder.

## Directory Structure

The Nautilus monorepo is cleanly separated into modular functional folders:

```text
NAUTILUS/
├── apps/               # Web interfaces (Next.js 3D Force Graph)
├── core/               # Systemic indexing & CLI tools (Python/ENERV)
├── config/             # Shared service registries & environment configs
├── scripts/            # Port broker & automation bootstrap files
├── hermes/             # Agent skills & orchestration loops
└── docs/               # Architecture documents & white papers
```
