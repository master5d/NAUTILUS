# Technical Stack & Resilient Gateway

Nautilus is engineered as a **sovereignty-first platform**. Every layer of the technical stack is modular, allowing you to swap out cloud providers, databases, or local models in days rather than weeks.

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
      <marker id="arrow-slate" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
      </marker>
    </defs>
    
    <!-- Grid Background -->
    <rect width="100%" height="100%" fill="url(#grid)" />
    
    <!-- Title -->
    <text x="30" y="35" fill="#f8fafc" font-size="14" font-weight="bold" letter-spacing="1">RESILIENT GATEWAY ROUTING</text>
    <text x="30" y="55" fill="#64748b" font-size="10">LiteLLM Dynamic High-Throughput &amp; Failsafe Topology</text>
    
    <!-- Caller Node -->
    <rect x="290" y="20" width="220" height="40" rx="6" fill="rgba(8, 51, 68, 0.3)" stroke="#22d3ee" stroke-width="1.5" />
    <text x="400" y="44" fill="#22d3ee" font-size="11" font-weight="bold" text-anchor="middle">Orchestrator / Agent / CLI</text>
    
    <!-- LiteLLM Node -->
    <rect x="290" y="85" width="220" height="40" rx="6" fill="rgba(8, 51, 68, 0.3)" stroke="#22d3ee" stroke-width="1.5" />
    <text x="400" y="109" fill="#22d3ee" font-size="10" text-anchor="middle">LiteLLM Proxy (localhost:4000)</text>
    
    <!-- Check Pool Decision -->
    <rect x="270" y="150" width="260" height="40" rx="6" fill="rgba(120, 53, 15, 0.2)" stroke="#fbbf24" stroke-width="1.5" />
    <text x="400" y="174" fill="#fbbf24" font-size="11" font-weight="bold" text-anchor="middle">1. Query Free Pools?</text>
    
    <!-- Free Pool Node -->
    <rect x="270" y="215" width="260" height="40" rx="6" fill="rgba(120, 53, 15, 0.2)" stroke="#fbbf24" stroke-width="1.5" />
    <text x="400" y="239" fill="#fbbf24" font-size="10" text-anchor="middle">Cerebras / Groq / NIM APIs</text>
    
    <!-- Check Error Decision -->
    <rect x="270" y="280" width="260" height="40" rx="6" fill="rgba(120, 53, 15, 0.2)" stroke="#fbbf24" stroke-width="1.5" />
    <text x="400" y="304" fill="#fbbf24" font-size="11" font-weight="bold" text-anchor="middle">Error or Rate Limit?</text>
    
    <!-- LOCAL PATH (Left Side) -->
    <!-- Check GGUF Decision -->
    <rect x="60" y="345" width="260" height="40" rx="6" fill="rgba(6, 78, 59, 0.3)" stroke="#34d399" stroke-width="1.5" />
    <text x="190" y="369" fill="#34d399" font-size="11" font-weight="bold" text-anchor="middle">2. Query Local GGUF?</text>
    
    <!-- Local GGUF Node -->
    <rect x="60" y="410" width="260" height="40" rx="6" fill="rgba(6, 78, 59, 0.3)" stroke="#34d399" stroke-width="1.5" />
    <text x="190" y="434" fill="#34d399" font-size="10" text-anchor="middle">llama.cpp CUDA Qwen3-Coder</text>
    
    <!-- Check Local Decision -->
    <rect x="60" y="475" width="260" height="40" rx="6" fill="rgba(6, 78, 59, 0.3)" stroke="#34d399" stroke-width="1.5" />
    <text x="190" y="499" fill="#34d399" font-size="11" font-weight="bold" text-anchor="middle">Local Server Offline?</text>
    
    <!-- FALLBACK PATH (Right Side) -->
    <!-- Paid Cloud Node -->
    <rect x="480" y="410" width="260" height="40" rx="6" fill="rgba(136, 19, 55, 0.2)" stroke="#fb7185" stroke-width="1.5" />
    <text x="610" y="434" fill="#fb7185" font-size="11" font-weight="bold" text-anchor="middle">3. Paid Cloud: Anthropic API</text>
    
    <!-- Failsafe Node -->
    <rect x="480" y="520" width="260" height="40" rx="6" fill="rgba(136, 19, 55, 0.2)" stroke="#fb7185" stroke-width="1.5" />
    <text x="610" y="544" fill="#fb7185" font-size="11" font-weight="bold" text-anchor="middle">Failsafe Alert &amp; Terminate</text>
    
    <!-- CONNECTIONS -->
    <!-- Caller --> LiteLLM -->
    <path d="M 400 60 V 85" fill="none" stroke="#22d3ee" stroke-width="1.5" marker-end="url(#arrow-cyan)" />
    
    <!-- LiteLLM --> CheckPool -->
    <path d="M 400 125 V 150" fill="none" stroke="#22d3ee" stroke-width="1.5" marker-end="url(#arrow-cyan)" />
    
    <!-- CheckPool --> FreePool -->
    <path d="M 400 190 V 215" fill="none" stroke="#fbbf24" stroke-width="1.5" marker-end="url(#arrow-amber)" />
    
    <!-- FreePool --> CheckError -->
    <path d="M 400 255 V 280" fill="none" stroke="#fbbf24" stroke-width="1.5" marker-end="url(#arrow-amber)" />
    
    <!-- CheckError --> CheckGGUF (Yes) -->
    <path d="M 400 320 V 332.5 H 190 V 345" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    <text x="290" y="327.5" fill="#34d399" font-size="8" text-anchor="middle">Yes (Error)</text>
    
    <!-- CheckError --> Caller (No - success) -->
    <path d="M 530 300 H 770 V 40 H 510" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    <text x="650" y="292.5" fill="#34d399" font-size="8" text-anchor="middle">No (Success)</text>
    
    <!-- CheckGGUF --> LocalGGUF -->
    <path d="M 190 385 V 410" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    
    <!-- LocalGGUF --> CheckLocal -->
    <path d="M 190 450 V 475" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    
    <!-- CheckLocal --> Caller (No - success) -->
    <path d="M 60 495 H 20 V 40 H 290" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    <text x="40" y="487.5" fill="#34d399" font-size="8" text-anchor="middle">No (Success)</text>
    
    <!-- CheckLocal --> PaidCloud (Yes - offline) -->
    <path d="M 190 515 V 535 H 430 V 430 H 480" fill="none" stroke="#fb7185" stroke-width="1.5" marker-end="url(#arrow-rose)" />
    <text x="310" y="527.5" fill="#fb7185" font-size="8" text-anchor="middle">Yes (Offline)</text>
    
    <!-- PaidCloud --> Caller (Success) -->
    <path d="M 740 430 H 770 V 40 H 510" fill="none" stroke="#34d399" stroke-width="1.5" marker-end="url(#arrow-green)" />
    
    <!-- PaidCloud --> Failsafe (All Fails) -->
    <path d="M 610 450 V 520" fill="none" stroke="#fb7185" stroke-width="1.5" stroke-dasharray="2,2" marker-end="url(#arrow-rose)" />
    <text x="615" y="485" fill="#fb7185" font-size="8">All Fails</text>
    
  </svg>
</div>

## Model Gateway: LiteLLM Rotating Pool

All models (local and cloud) are consolidated under a single entry point running on `localhost:4000` via **LiteLLM**. Individual consumer scripts see only model aliases, keeping credentials decoupled from application logic. The routing hierarchy is structured to optimize latency, cost, and reliability:

1. **Free Cloud Tiers First**: Utilizes high-speed, zero-cost developer APIs (Cerebras Qwen-3 MoE ~1000 TPS, Groq Llama-3.3-70B, NVIDIA NIM). These are preferred for prompt execution and high-throughput tasks.
2. **Local GGUF Second**: Serves as the absolute, offline-capable sovereignty floor. Powered by `llama.cpp` CUDA binaries running a quantized Qwen3-Coder-30B (MoE) on your GPU (Surface Studio i7/RTX 4060).
3. **Paid Clouds Third**: Leveraged only as a last resort or when a task demands extreme frontier reasoning (e.g., Anthropic Opus/Sonnet API via pay-as-you-go).

## Unified Memory Layers

Memory is split into two asynchronous loops to prevent context bloat:

- **Fast Path (ACE Phase 0)**: Local Obsidian markdown folders (`Efforts/`, `Atlas/`, `Calendar/`). Features automated daily cron consolidation, harvesting durable facts from daily logs and writing summaries to references.
- **Slow Path (Graphiti Phase 1)**: FalkorDB / Neo4j Graph DB combined with a local Qdrant Vector store. Used to resolve complex temporal relationships and track knowledge contradictions.

## SecOps: Sovereign Shield

Deployed on the Hetzner compute host, the **Sovereign Shield** protects your workspace against agent-based prompt injections, vault tampering, and network intrusion:

- **Wazuh Agent**: Monitors File Integrity (FIM) across Obsidian notes directories and monitors system logins.
- **Falco (eBPF)**: Tracks system-level syscalls. Includes rules to detect prompt injections (scanning n8n logs for malicious system prompt commands) and triggers container quarantine protocols on compromise.
- **CrowdSec**: Automatically blocks hostile IP addresses at the Cloudflare DNS and proxy edge.
- **Retaliation Engine**: An autonomous bash script that immediately kills compromised containers, updates iptables, and sends an alert payload to the Coder via Telegram on threat detection.

## Hosting & Compute Boundaries

To protect battery health, avoid residential IP collisions, and prevent system lag, development and production boundaries are strictly isolated:

| Layer | Environment | Technology |
| --- | --- | --- |
| **Local Dev** | Surface Laptop Studio 2 / Win11 Pro | Zed, Aider, Cline, llama.cpp CUDA, Local Obsidian |
| **Edge Compute** | Cloudflare Pages & Workers | Next.js Frontend UI, n8n webhook routing |
| **Sovereign Cloud** | Hetzner CX23 VPS (€3.79/mo) | Dokploy, Docker, Qdrant, Wazuh Server, Postiz |
