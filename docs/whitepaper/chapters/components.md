# Core Components

The Nautilus monorepo is divided into highly specialized, loosely coupled modules that share state through environment variables, dynamic port allocation, and standardized JSON schemas.

<div align="center">
  <svg width="100%" height="auto" viewBox="0 0 850 480" style="max-width: 850px; background: #0b0f19; border: 1px solid #1e293b; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); font-family: 'JetBrains Mono', Consolas, monospace;">
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
    <text x="30" y="35" fill="#f8fafc" font-size="14" font-weight="bold" letter-spacing="1">NAUTILUS COMPONENT INTERACTION</text>
    <text x="30" y="55" fill="#64748b" font-size="10">Monorepo Modules &amp; Ports Orchestration</text>
    
    <!-- Subgraph: apps/ -->
    <rect x="25" y="245" width="270" height="200" rx="10" fill="none" stroke="#1e293b" stroke-width="1.5" stroke-dasharray="4,4" />
    <text x="40" y="265" fill="#64748b" font-size="9" font-weight="bold">apps/ (Next.js Web UI)</text>
    
    <!-- Nooscope -->
    <rect x="45" y="300" width="230" height="70" rx="6" fill="rgba(8, 51, 68, 0.3)" stroke="#22d3ee" stroke-width="1.5" />
    <text x="160" y="332" fill="#22d3ee" font-size="11" font-weight="bold" text-anchor="middle">NOOSCOPE UI</text>
    <text x="160" y="348" fill="#94a3b8" font-size="8" text-anchor="middle">react-force-graph-3d | WebGL</text>
    
    <!-- Subgraph: hermes/ -->
    <rect x="315" y="20" width="270" height="200" rx="10" fill="none" stroke="#1e293b" stroke-width="1.5" stroke-dasharray="4,4" />
    <text x="330" y="40" fill="#64748b" font-size="9" font-weight="bold">hermes/ (Orchestration)</text>
    
    <!-- Hermes Agent -->
    <rect x="335" y="75" width="230" height="70" rx="6" fill="rgba(8, 51, 68, 0.3)" stroke="#22d3ee" stroke-width="1.5" />
    <text x="450" y="107" fill="#22d3ee" font-size="11" font-weight="bold" text-anchor="middle">HERMES AGENT</text>
    <text x="450" y="123" fill="#94a3b8" font-size="8" text-anchor="middle">Orchestration &amp; WSL Shell</text>
    
    <!-- Subgraph: core/ -->
    <rect x="315" y="245" width="270" height="200" rx="10" fill="none" stroke="#1e293b" stroke-width="1.5" stroke-dasharray="4,4" />
    <text x="330" y="265" fill="#64748b" font-size="9" font-weight="bold">core/ (Python CLI)</text>
    
    <!-- Enerv / facet -->
    <rect x="335" y="300" width="230" height="70" rx="6" fill="rgba(6, 78, 59, 0.3)" stroke="#34d399" stroke-width="1.5" />
    <text x="450" y="332" fill="#34d399" font-size="11" font-weight="bold" text-anchor="middle">ENERV INDEXER (facet CLI)</text>
    <text x="450" y="348" fill="#94a3b8" font-size="8" text-anchor="middle">Faceted Audits &amp; Ingestion</text>
    
    <!-- Subgraph: scripts/ -->
    <rect x="605" y="20" width="220" height="200" rx="10" fill="none" stroke="#1e293b" stroke-width="1.5" stroke-dasharray="4,4" />
    <text x="620" y="40" fill="#64748b" font-size="9" font-weight="bold">scripts/ (Automation)</text>
    
    <!-- Broker -->
    <rect x="620" y="60" width="190" height="40" rx="6" fill="rgba(120, 53, 15, 0.2)" stroke="#fbbf24" stroke-width="1.5" />
    <text x="715" y="84" fill="#fbbf24" font-size="10" font-weight="bold" text-anchor="middle">Port Broker Script</text>
    
    <!-- Launcher -->
    <rect x="620" y="130" width="190" height="40" rx="6" fill="rgba(120, 53, 15, 0.2)" stroke="#fbbf24" stroke-width="1.5" />
    <text x="715" y="154" fill="#fbbf24" font-size="10" font-weight="bold" text-anchor="middle">Service Launchers</text>
    
    <!-- Subgraph: config/ -->
    <rect x="605" y="245" width="220" height="200" rx="10" fill="none" stroke="#1e293b" stroke-width="1.5" stroke-dasharray="4,4" />
    <text x="620" y="265" fill="#64748b" font-size="9" font-weight="bold">config/ (Shared Registry)</text>
    
    <!-- Services.json -->
    <rect x="620" y="285" width="190" height="40" rx="6" fill="rgba(136, 19, 55, 0.2)" stroke="#fb7185" stroke-width="1.5" />
    <text x="715" y="309" fill="#fb7185" font-size="10" font-weight="bold" text-anchor="middle">services.json Registry</text>
    
    <!-- litellm_config -->
    <rect x="620" y="355" width="190" height="40" rx="6" fill="rgba(136, 19, 55, 0.2)" stroke="#fb7185" stroke-width="1.5" />
    <text x="715" y="379" fill="#fb7185" font-size="10" font-weight="bold" text-anchor="middle">litellm_config.yaml</text>
    
    <!-- CONNECTIONS -->
    <!-- Broker --> Services -->
    <path d="M 715 100 V 285" fill="none" stroke="#fbbf24" stroke-width="1.5" marker-end="url(#arrow-amber)" />
    <text x="720" y="210" fill="#fbbf24" font-size="7">Allocates Ports</text>
    
    <!-- Services --> Launcher -->
    <path d="M 680 285 V 170" fill="none" stroke="#fb7185" stroke-width="1.5" marker-end="url(#arrow-rose)" />
    <text x="635" y="210" fill="#fb7185" font-size="7">Resolves Ports</text>
    
    <!-- Launcher --> Nooscope -->
    <path d="M 620 150 H 160 V 300" fill="none" stroke="#fbbf24" stroke-width="1.5" marker-end="url(#arrow-amber)" />
    <text x="165" y="235" fill="#fbbf24" font-size="8">Launches</text>
    
    <!-- Launcher --> LiteLLMConfig -->
    <path d="M 810 150 H 830 V 375 H 810" fill="none" stroke="#fbbf24" stroke-width="1.5" marker-end="url(#arrow-amber)" />
    
    <!-- Enerv --> Services -->
    <path d="M 565 335 H 620" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    <text x="590" y="328" fill="#34d399" font-size="8" text-anchor="middle">Validates</text>
    
    <!-- HermesAgent --> Enerv -->
    <path d="M 450 145 V 300" fill="none" stroke="#a78bfa" stroke-width="1.5" marker-end="url(#arrow-purple)" />
    <text x="455" y="210" fill="#a78bfa" font-size="8">Dispatches</text>
    
    <!-- Nooscope <--> Enerv -->
    <path d="M 275 335 H 335" fill="none" stroke="#22d3ee" stroke-width="1.5" marker-start="url(#arrow-cyan)" marker-end="url(#arrow-cyan)" />
    <text x="305" y="328" fill="#22d3ee" font-size="8" text-anchor="middle">Queries</text>
    
  </svg>
</div>

## Monorepo Directory Breakdown

### 1. `/apps/knowledge-graph` (Nooscope UI)
- **Tech Stack**: Next.js 16, React, WebGL (Three.js via `react-force-graph-3d`), Neo4j-driver.
- **Responsibility**: Serves as the developer's 3D semantic control dashboard. Renders interactive structural nodes and allows for multi-dimensional GraphRAG search queries directly from the sidebar. It is designed with robust **offline fallbacks**, sweeping the local Obsidian markdown notes vault when the Neo4j database is offline.

### 2. `/core/enerv` (ENERV Systemic Indexer)
- **Tech Stack**: Python 3.12, Pydantic, JSON Schema, system Python libraries.
- **Responsibility**: Houses the `facet` CLI. Runs fast folder-level metadata scans, schema validations, and structural audits. Incorporates the native `facet ingest` pipeline, performing file normalization, multi-chunk parsing, embedding generation, and atomic transactional writes to Neo4j.

### 3. `/config` (Shared Registry)
- **Tech Stack**: JSON, YAML.
- **Responsibility**: Holds the configuration profiles for the monorepo services:
  - `services.json`: Automatically updated by the Port Broker to register the active host ports.
  - LiteLLM configuration profiles mapping standard model aliases and routing protocols.

### 4. `/scripts` (Lifecycle & Port Broker Automation)
- **Tech Stack**: PowerShell Core (`pwsh`), Python.
- **Responsibility**: Prevents port collisions on local Windows hosts. The dynamic `port_broker.py` sweeps available sockets, binds free ports, updates service configs, and feeds variables into `.env` and `.env.local` before bootstrapping llama-server and LiteLLM gateways via `master-restart.ps1`.

### 5. `/hermes` (Agentic Orchestration Layer)
- **Tech Stack**: Bash, Pydantic-AI, Aider/Cline CLI harnesses.
- **Responsibility**: Serves as the central autonomous gateway. Hermes listens to Telegram controls, executes scheduled memory sweeps, and coordinates specialist sub-agents (Aider, Cline) using strict contextual boundaries.
