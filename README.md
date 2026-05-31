# NAUTILUS — Sovereign Personal Knowledge Mesh & AI Pilot

**Nautilus** is a local-first autonomous environment for personal knowledge management, multi-dimensional semantic indexing, and secure AI agent orchestration. It is built upon the **SOVRN Architecture blueprints**—a set of sovereignty-first, zero-telemetry, and highly resilient technical principles.

<div align="center">
  <img src="docs/whitepaper/images/concept.svg" alt="Nautilus Concept Flowchart" style="width: 100%; max-width: 800px; background: #0b0f19; border: 1px solid #1e293b; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);" />
</div>


---

## 🏗 Monorepo Architecture

Nautilus is divided into modular directory boundaries:

* **`/apps/knowledge-graph` (Nooscope UI)**: A WebGL-powered 3D force-directed node visualization dashboard (Next.js 16 + React + Three.js). Features custom GraphRAG searches and supports a robust offline fallback (`walkVault`) sweeping local Obsidian directories when database servers are offline.
* **`/core/enerv` (ENERV Indexer)**: A fast, schema-first environmental compass (Python CLI). Validates project directories against strict JSON contracts (`.facets/meta.json`) and powers the local `facet ingest` pipeline.
* **`/config` (Shared Service Configs)**: Houses LiteLLM provider configurations and holds the dynamic service registry updated by the Port Broker.
* **`/scripts` (Lifecycle & Port Broker Automation)**: Prevents port collisions on local Windows hosts via socket availability sweeps, automatically synchronizing dynamic ports across envs (`.env`, `.env.local`, `.hermes/config.yaml`).
* **`C:\telo\Efforts\Simmering`**: The back-burner zone for active ideas fermentation.
* **`/hermes/skills` (Orchestration & Skills)**: The central AI pilot gateway. Listens to Telegram bot directives, manages cumulative dry-runs, and dispatches tasks to specialist coding agents (Aider, Cline). Includes the **Resonance Audit** skill for cognitive bandwidth management.
* **`/Atlas/Maps/Interests MOC.md`**: The central index for high-resonance "Drive" projects.

---

## 📂 Sovereign File System Recommendations

Nautilus enforces a **Zero-Clutter Root Policy** to minimize "Folder Tax" and maximize focus. For a canonical **Solo Vibe Coder** setup:

1.  **ACE Core**: The project root (`C:\telo`) must only contain the three ACE pillars (**Atlas**, **Calendar**, **Efforts**), essential logs, and minimal system configs (`.env`, `.mcp.json`).
2.  **Agent Redirection**: All agent-specific working files (keche, configs, persistent state) must be relocated to a centralized `C:\agents\<AgentName>` directory and mapped back via hidden **Symbolic Junctions**.
3.  **STIER Dimension**: Efforts should be tagged with **⚡ Drive** or **🛠️ Duty** prefixes to enable the **Resonance Audit** and maintain energy balance.

---

## 🧠 Sovereignty-First Principles

1. **Autonomy Under Failure**: The stack is designed to operate 100% offline on your local hardware (Surface Studio/WSL2) if every cloud goes dark. Local GGUF (`llama-server`) and local Obsidian directories serve as the guaranteed baseline floor.
2. **Zero Telemetry Constraint**: Opaque development environments with closed telemetry tracking are strictly prohibited. Open, local-first tools (Zed, Aider, Cline) are leveraged exclusively.
3. **Gateway Agnosticism**: All Large Language Models are routed through a central LiteLLM gateway (`localhost:4000`) with dynamic failover arrays (Free cloud pools first → Local GGUF second → Paid cloud third).

---

## 🚀 Quick Start

### 1. Environment Preparation
Initialize the environment configuration by copying the template and setting up your keys:
```bash
cp .env.example .env
```

### 2. Bootstrap the Local Stack
Execute the canonical launch script. The **Port Broker** will scan for available host ports, synchronize configurations, and safely start all database, inference, and visualization services:
```powershell
./scripts/master-restart.ps1
```

### 3. Integrated CLI Commands
The Python-powered `facet` CLI provides a unified control interface:

* **Ingest Documents**: Chunk, hash, embed, and transactionally merge files into your knowledge graph with automatic metadata inheritance:
  ```bash
  facet ingest path/to/note.md
  ```
* **Audit Directory Contexts**: Recursively scan all project directories for schema drift or missing configurations:
  ```bash
  facet audit
  ```
* **Open 3D Visualization**: Instantly map the current directory context in the WebGL Nooscope UI:
  ```bash
  facet visualize .
  ```

---

## 🎙 Echo Voice Capture

[Echo](https://github.com/master5d/Echo) — the local-first dictation app — can drop voice notes straight into the mesh. Echo is the **sensory audio bridge**: you speak, and your words become a note Nautilus ingests.

In Echo's **Settings → Advanced**, set the **Voice capture folder** to a Nautilus/Obsidian inbox directory and add a **trigger phrase** (e.g. `запиши в наутилус`). Saying *"&lt;phrase&gt; …"* writes a timestamped markdown note (with `source: echo` frontmatter) into that folder instead of typing it into the active app. The normal `facet ingest` / n8n pipeline then consumes it — no extra wiring, fully local and sovereign.

---

## 📖 Deeper Reading
The full system architecture, bitemporal memory designs, and multi-phase rollout lifecycles are documented in the **[Nautilus White Paper](docs/whitepaper/README.md)**:

* **[Vision & Principles](docs/whitepaper/chapters/vision.md)**: Failure boundaries and zero-telemetry rules.
* **[Architecture Overview](docs/whitepaper/chapters/architecture.md)**: Metadata, semantic, and orchestration layers.
* **[Core Components](docs/whitepaper/chapters/components.md)**: Monorepo folder layouts and dynamics.
* **[ENERV: Metadata Mesh](docs/whitepaper/chapters/enerv.md)**: Schema-first faceted directory indexer.
* **[Knowledge Graph & RAG](docs/whitepaper/chapters/knowledge-graph.md)**: Ingestion flows, 3D WebGL, and `walkVault` local fallbacks.
* **[Technical Stack](docs/whitepaper/chapters/stack.md)**: LiteLLM rotating pools and SecOps Sovereign Shield monitoring.
* **[Phased Roadmap](docs/whitepaper/chapters/roadmap.md)**: Progression timeline (Phases 0 to 4).
