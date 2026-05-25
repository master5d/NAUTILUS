# ENERV: The Metadata Mesh

**ENERV** is the structural compass of the Nautilus environment. It provides a schema-first, lightweight metadata framework that catalogs and validates your directories without incurring the cost of deep semantic ingestion.

<div align="center">
  <svg width="100%" height="auto" viewBox="0 0 800 660" style="max-width: 800px; background: #0b0f19; border: 1px solid #1e293b; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); font-family: 'JetBrains Mono', Consolas, monospace;">
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
    <text x="30" y="35" fill="#f8fafc" font-size="14" font-weight="bold" letter-spacing="1">NAUTILUS METADATA HARVESTING FLOW</text>
    <text x="30" y="55" fill="#64748b" font-size="10">ENERV Faceted Audit Engine Execution Loop</text>
    
    <!-- Start Node -->
    <rect x="290" y="20" width="220" height="40" rx="20" fill="rgba(8, 51, 68, 0.3)" stroke="#22d3ee" stroke-width="1.5" />
    <text x="400" y="44" fill="#22d3ee" font-size="11" font-weight="bold" text-anchor="middle">facet audit / walk</text>
    
    <!-- Read Directory Node -->
    <rect x="290" y="90" width="220" height="40" rx="6" fill="rgba(8, 51, 68, 0.3)" stroke="#22d3ee" stroke-width="1.5" />
    <text x="400" y="114" fill="#22d3ee" font-size="11" text-anchor="middle">Read Directory Node</text>
    
    <!-- Check Meta Decision Node -->
    <rect x="270" y="160" width="260" height="45" rx="6" fill="rgba(120, 53, 15, 0.2)" stroke="#fbbf24" stroke-width="1.5" />
    <text x="400" y="186" fill="#fbbf24" font-size="11" font-weight="bold" text-anchor="middle">Has .facets/meta.json?</text>
    
    <!-- Inherit Meta Node -->
    <rect x="60" y="245" width="260" height="50" rx="6" fill="rgba(76, 29, 149, 0.3)" stroke="#a78bfa" stroke-width="1.5" />
    <text x="190" y="270" fill="#a78bfa" font-size="11" text-anchor="middle">Inherit context from parent</text>
    <text x="190" y="284" fill="#64748b" font-size="8" text-anchor="middle">Implicit facet cascading</text>
    
    <!-- Parse Meta Node -->
    <rect x="480" y="245" width="260" height="50" rx="6" fill="rgba(6, 78, 59, 0.3)" stroke="#34d399" stroke-width="1.5" />
    <text x="610" y="270" fill="#34d399" font-size="11" text-anchor="middle">Parse meta.json</text>
    <text x="610" y="284" fill="#64748b" font-size="8" text-anchor="middle">Validate JSON Schema</text>
    
    <!-- Check Schema Decision Node -->
    <rect x="480" y="335" width="260" height="45" rx="6" fill="rgba(120, 53, 15, 0.2)" stroke="#fbbf24" stroke-width="1.5" />
    <text x="610" y="361" fill="#fbbf24" font-size="11" font-weight="bold" text-anchor="middle">Valid Schema?</text>
    
    <!-- Schema Error Node -->
    <rect x="200" y="335" width="240" height="45" rx="6" fill="rgba(136, 19, 55, 0.2)" stroke="#fb7185" stroke-width="1.5" />
    <text x="320" y="361" fill="#fb7185" font-size="11" font-weight="bold" text-anchor="middle">Audit failure &amp; Warnings</text>
    
    <!-- Audit Files Node -->
    <rect x="270" y="425" width="260" height="50" rx="6" fill="rgba(6, 78, 59, 0.3)" stroke="#34d399" stroke-width="1.5" />
    <text x="400" y="450" fill="#34d399" font-size="11" text-anchor="middle">Audit Child Files</text>
    <text x="400" y="464" fill="#64748b" font-size="8" text-anchor="middle">Scan Frontmatter Metadata</text>
    
    <!-- Compile Mesh Node -->
    <rect x="270" y="510" width="260" height="50" rx="6" fill="rgba(76, 29, 149, 0.3)" stroke="#a78bfa" stroke-width="1.5" />
    <text x="400" y="535" fill="#a78bfa" font-size="11" text-anchor="middle">Compile In-Memory Mesh</text>
    <text x="400" y="549" fill="#64748b" font-size="8" text-anchor="middle">Assemble faceted topology</text>
    
    <!-- Update Registry Node -->
    <rect x="270" y="590" width="260" height="40" rx="6" fill="rgba(8, 51, 68, 0.3)" stroke="#22d3ee" stroke-width="1.5" />
    <text x="400" y="614" fill="#22d3ee" font-size="11" font-weight="bold" text-anchor="middle">Write status summary to CLI</text>
    
    <!-- CONNECTIONS -->
    <!-- Start --> ReadDir -->
    <path d="M 400 60 V 90" fill="none" stroke="#22d3ee" stroke-width="1.5" marker-end="url(#arrow-cyan)" />
    
    <!-- ReadDir --> CheckMeta -->
    <path d="M 400 130 V 160" fill="none" stroke="#22d3ee" stroke-width="1.5" marker-end="url(#arrow-cyan)" />
    
    <!-- CheckMeta --> InheritMeta (No) -->
    <path d="M 400 205 V 225 H 190 V 245" fill="none" stroke="#fbbf24" stroke-width="1.5" marker-end="url(#arrow-amber)" />
    <text x="290" y="220" fill="#fbbf24" font-size="9" text-anchor="middle">No</text>
    
    <!-- CheckMeta --> ParseMeta (Yes) -->
    <path d="M 400 205 V 225 H 610 V 245" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    <text x="510" y="220" fill="#34d399" font-size="9" text-anchor="middle">Yes</text>
    
    <!-- ParseMeta --> CheckSchema -->
    <path d="M 610 295 V 335" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    
    <!-- CheckSchema --> SchemaError (No) -->
    <path d="M 480 357.5 H 440" fill="none" stroke="#fb7185" stroke-width="1.5" marker-end="url(#arrow-rose)" />
    <text x="460" y="352" fill="#fb7185" font-size="9" text-anchor="middle">No</text>
    
    <!-- CheckSchema --> AuditFiles (Yes) -->
    <path d="M 610 380 V 405 H 400 V 425" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    <text x="505" y="400" fill="#34d399" font-size="9" text-anchor="middle">Yes</text>
    
    <!-- InheritMeta --> AuditFiles -->
    <path d="M 190 295 V 405 H 400 V 425" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    
    <!-- AuditFiles --> CompileMesh -->
    <path d="M 400 475 V 510" fill="none" stroke="#a78bfa" stroke-width="1.5" marker-end="url(#arrow-purple)" />
    
    <!-- CompileMesh --> UpdateRegistry -->
    <path d="M 400 560 V 590" fill="none" stroke="#22d3ee" stroke-width="1.5" marker-end="url(#arrow-cyan)" />
    
  </svg>
</div>

## The Principle of Faceted Indexing

Traditional personal search systems rely on complete full-text indexes. While powerful, full-text indexes lack structural awareness—they cannot tell you if a file belongs to an active project, which engineering team owns it, or its priority level in a sprint. 

ENERV solves this via **Faceted Indexing**. By scanning for metadata boundaries, it constructs an environment map based on hierarchical facets:

1. **Environmental Scope**: Mapped absolute pathways (e.g., `TECH_ROOT`, `KNOWLEDGE_ROOT`).
2. **Context Contracts**: `.facets/meta.json` files that define project attributes.
3. **Implicit Inheritance**: Subfolders inherit metadata attributes from their nearest parent contract unless explicitly overridden, preventing manual duplication.

## The `.facets/meta.json` Schema

Every project directory contains a local configuration file that defines its operational context. An example schema contains:

```json
{
  "$schema": "../../core/enerv/schemas/meta-schema.json",
  "project": "nautilus-core",
  "team": "AI Orchestration",
  "status": "active",
  "priority": "P0",
  "tags": ["knowledge-mesh", "graph-rag", "local-first"]
}
```

ENERV validates these configurations using standard JSON Schemas. If a project declares an invalid status or an unmapped team, the auditing engine flags it immediately.

## Key CLI Operations

- `facet audit`: Recursively scans directories to detect schema violations, broken paths, or orphaned files.
- `facet walk`: Traverses active directories to generate a unified, lightweight system registry, providing the baseline context for AI orchestration layers.
- `facet visualize`: Seamlessly transfers the current directory's metadata context to the 3D Nooscope interface.

---
> [!TIP]
> Use `facet audit` regularly to detect "context drift" across project directories. It acts as a linting tool for your file organization.
