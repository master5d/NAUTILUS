# Canonical Principles of SOVRN v3.3 (Source of Truth)

## 1. Sovereignty First
- **Sovereignty as Autonomy Under Failure**: The architecture MUST run entirely offline on local hardware (Surface Laptop/WSL2) if every cloud goes dark. Local is the guaranteed fallback floor — never a hard dependency on cloud. Default routing may prefer free clouds for speed (see §5), but the system must always have a viable local-only path.
- **Zero-Telemetry Constraint**: Tools with opaque synchronization or telemetry (Trae, Cursor) are strictly prohibited. Open-source or local-first tools (Zed, Aider, Cline) are preferred.
- **Walk-away Economics**: Infrastructure must support 'pay-as-you-go' or flat-fee licensing. No hidden lock-ins or hard dependencies on transient VC-backed SaaS. Free-tier cloud usage is acceptable provided every dependency has a local or alternative-cloud fallback.

## 2. Boss-Worker Orchestration
- **Hermes as Boss**: Hermes Agent (WSL2 Shell) manages plans, cron jobs, and skill lifecycle. It does not perform mundane coding tasks directly.
- **Delegation to Specialist Agents**: All code generation, refactoring, and complex technical tasks are delegated to sub-agents (Aider, Claude Code, Cline).
- **Explicit Checkpoints**: All `stateful` actions require a cumulative dry-run or a summary + confirmation step before execution.

## 3. DeepVista Skill Schema (Type x Execution)
- **Modularity**: Capabilities are encapsulated in `SKILL.md` files with YAML frontmatter.
- **Stateless vs Stateful**: 
  - `stateless`: Auto-invoked, safe to retry.
  - `stateful`: Requires the `dry_run_gate` and human/boss approval.
- **Persona vs Tool vs Workflow**: Clear semantic separation between background context, atomic tools, and ordered sequences.

## 4. Bitemporal Memory (PARA -> Graphiti)
- **Fast Path (PARA Phase 0)**: Obsidian-based Markdown (Projects, Areas, Resources, Archives) for daily capture and tacit knowledge.
- **Slow Path (Graphiti Phase 1)**: Vector + Graph hybrid (FalkorDB + Qdrant) for multi-hop reasoning, contradiction tracking, and temporal context. Activated only when PARA hits scale limits.
- **Consolidation**: Daily automated migration of 'durable facts' from capture (Daily docs) to long-term memory.

## 5. Model Agnosticism & Resilience
- **LiteLLM Gateway**: Centralized routing on `http://localhost:4000` with explicit fallback arrays. Single OpenAI-compatible entry point for every consumer (Hermes, hooks, CLI tools, Python scripts, Next.js dev).
- **Routing Hierarchy** (default order, override per call when justified):
  1. **Free clouds first** — high-speed tiers (Cerebras qwen-3-235b ~1000 TPS, Groq llama-3.3-70b, Gemini 2.5 Flash 15 RPM / 1500 RPD). Chosen first for latency, not cost — local GGUF cannot match Cerebras throughput on a Surface-class laptop.
  2. **Local GGUF** — `llama-server` (llama.cpp CUDA 13.1, Qwen3-Coder-30B-A3B on `localhost:8080`). Guaranteed fallback when every cloud rate-limits, errors, or goes offline. Must always be reachable as the floor (§1 Sovereignty).
  3. **Paid cloud** — only when free + local exhausted and task quality demands it. Requires explicit caller intent (no implicit upgrade).
- **Reasoning Budgets**: Dynamic allocation of 'effort' based on task complexity (Planning: High, Extraction: Low).
- **No Direct Provider Keys in Code**: Auth lives in LiteLLM config. Consumers see only LiteLLM aliases (`fast-pool`, `local-fallback`, `google/gemini-3-flash-preview`, `reasoning`, etc.).

## 6. High-Standard Visual Aesthetics
- **Output Quality**: Every artifact (Diagrams, Docs, ASCII) must meet the 'Solo Vibe Coder' standard—dark-themed, high-contrast, and structurally precise.
- **ANSI & FIGlet**: Use visual separators and banners for context switching in terminal/shell outputs.
