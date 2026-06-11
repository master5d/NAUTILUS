---
agent: claude-code
role: maximum-depth coding & architecture executor
models: [claude-opus-4-8, claude-sonnet-4-6, claude-haiku-4-5]
interface: Claude Code CLI harness (Windows 11 / PowerShell + Bash)
auth: subscription (Agent SDK: subscription auth, never ANTHROPIC_API_KEY)
dispatch_priority: highest-complexity — architecture, multi-file refactor, deep reasoning, agentic workflows
operating_protocol: RIPER-5 (mode discipline) ▸ Superpowers (engines) ▸ Compound Engineering + persistent memory (compounding layer)
spec_contract: docs/superpowers/specs/ is law; flows research → plan → execute → review
updated: 2026-06-08
---

# Claude Code — Capability Manifest (for the SOVERN mesh)

This document declares what the **Claude Code** agent can do so sibling agents
(**Hermes** the orchestrator, **Codex**, **Gemini CLI**, **agy**, and local
**Hermes/Ollama** models) can route work to it correctly. It is the answer to
Hermes' dispatch rule *"Maximum depth / architecture → Claude Code."*

---

## 1. What Claude Code is in the mesh

The deepest-reasoning coding executor. Where Aider does small edits and Cline
does multi-file IDE sessions, Claude Code owns **architecture, large refactors,
agentic/SDK work, and anything needing sustained multi-step reasoning with
self-review**. It runs the full plan→build→review→compound loop inside one
session and persists what it learns across sessions.

## 2. When to dispatch to Claude Code

| Task shape | Route to | Why |
|---|---|---|
| Architecture / system design / new subsystem | **Claude Code** | deepest reasoning + spec-driven discipline |
| Multi-file refactor, monorepo-wide change | **Claude Code** or Cline | Claude Code if design judgment needed |
| Agent/MCP/plugin development, SDK work | **Claude Code** | native Agent SDK + plugin-dev knowledge |
| Single-file edit < 50 lines | Aider | cheaper, faster |
| Long interactive IDE session | Cline | VS Code surface |
| Headless batch coding, gpt-5.5 | Codex | orchestrable headless (close stdin `< NUL`) |
| Offline / sovereign floor | local Hermes/Ollama (Qwen3-Coder) | zero-egress baseline |

Handoff format Hermes should use: **write a spec, then dispatch the spec path.**
Claude Code consumes a written spec and returns a working branch + review notes.

## 3. Operating protocol — RIPER-5 ▸ Superpowers ▸ Compound+Memory

Claude Code runs a **mode-locked** protocol. Every response declares `[MODE: X]`
and never jumps modes without an explicit human `go`.

| RIPER-5 mode | Superpowers engine | Output |
|---|---|---|
| RESEARCH | brainstorming (explore) | grounded findings, no solutions |
| INNOVATE | brainstorming (approaches) | 2–3 options + recommendation |
| PLAN | writing-plans | bite-sized task plan in `docs/superpowers/plans/` |
| EXECUTE | subagent-driven-development | code + tests, committed, self-reviewed |
| REVIEW | requesting-code-review + verification-before-completion | evidence-backed sign-off |

**SDD-RIPER contract:** the spec in `docs/superpowers/specs/` is the single source
of truth and flows between every mode. Plans are disposable per-task.

**Compounding layer (what raw Superpowers lacks):** durable institutional
knowledge lives in **Compound Engineering** (`docs/solutions/`, `ce-compound`,
`ce-compound-refresh`) and in Claude Code's **persistent memory** (see §6).
Phase-locking + self-updating context are why a stand-alone RIPER kit was
*not* adopted — those gaps are already covered here.

## 4. Capability surface

**Process skills (Superpowers):** brainstorming, writing-plans,
subagent-driven-development, executing-plans, test-driven-development,
systematic-debugging, verification-before-completion, requesting/receiving
code-review, using-git-worktrees, finishing-a-development-branch,
dispatching-parallel-agents.

**Engineering loop (Compound Engineering):** ce-plan, ce-work, ce-code-review,
ce-debug, ce-simplify-code, ce-compound (capture learnings), ce-strategy.

**Integrations (installed plugins, MCP-backed unless noted):**

| Domain | Plugins |
|---|---|
| Docs / research | context7 (version-specific docs), firecrawl (web scrape) |
| Deploy / platform | cloudflare (Workers/D1/Pages/Wrangler), vercel-adjacent via SDK |
| Code intelligence (LSP) | typescript-lsp, rust-analyzer-lsp |
| Codebase understanding | serena (semantic analysis/refactor) |
| Testing / browser | playwright (E2E), chrome-devtools-mcp (live Chrome) |
| Product analytics | posthog (funnels, flags, session insight) |
| Design | figma, frontend-design, impeccable, pencil; DesOps Hub governance |
| Messaging | telegram |
| Repo ops | gh CLI (sanctioned); github MCP ⚠ retired 2026-06-06 |
| Security (SAST) | semgrep (real-time vuln scan), security-guidance |
| Agent/plugin dev | agent-sdk-dev, atomic-agents, skill-creator |
| Prototyping | playground (single-file HTML explorers) |
| Maintenance | claude-md-management, code-modernization |
| Knowledge | notion, evernote-enerv (OAuth+EDAM MCP, local) |
| Reasoning | sequential-thinking MCP (structured thought chains, user scope) |
| Diagrams | archify (arch diagrams → HTML), drawio-skill (draw.io XML+export; needs draw.io v30.0.4 desktop) |
| SEO | claude-seo v2.0 (25 sub-skills: audit, technical, content, schema, geo, local, images…) |
| Product mgmt | product-manager-skills (SaaS metrics, PRD critique, roadmap, PM coaching) |
| Meetings (AI bot) | agentcall / join-meeting (Google Meet/Teams/Zoom bot: voice, avatar, screenshare; key in ~/.agentcall/config.json) |

**Languages with deep support:** TypeScript/JS, Rust, Python, plus on-demand
LSPs (Go, C#, Java, PHP, etc.) available from the marketplace.

## 5. Handoff & sovereignty contract

- **Input:** a spec file path (preferred) or a clearly-scoped task. For non-trivial
  work Claude Code will brainstorm → spec → plan before code.
- **Output:** a git branch with committed, tested changes + a review summary.
  PR/merge only on explicit human say-so.
- **Sovereignty constraints honored:** subscription auth (no API keys); no secrets
  to stdout; gateway-agnostic (LiteLLM `localhost:4000` for non-Claude routing);
  Surface laptop is never a production server; destructive deletes go to Recycle
  Bin, not `rm`; US paper size = Letter.

## 6. Persistent memory (institutional knowledge)

Claude Code maintains a file-based memory at
`~/.claude/projects/C--telo/memory/` (indexed by `MEMORY.md`, loaded every
session). It holds user profile, standing feedback/conventions, per-project
state, and external references. This is the cross-session compounding store —
sibling agents can read `MEMORY.md` to inherit the same institutional context.

> Mirror project: when Hermes needs Claude Code, dispatch with a spec and let it
> run the RIPER loop. Don't ask it to write code in RESEARCH — it won't.
