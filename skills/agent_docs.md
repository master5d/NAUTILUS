---
name: agent-docs
description: Fetch fresh official documentation for agents installed at C:\agents (Claude Code, Hermes/NousResearch, Gemini CLI, Codex, Antigravity/agy) and solve setup/integration tasks within the SOVERN NAUTILUS architecture. Invoke when any agent config, model routing, MCP wiring, shared toolset, or inter-agent integration question arises.
metadata:
  version: "1.1"
  author: sovern
---

# Agent Docs Skill

Fetches the latest official documentation for any agent in the SOVERN mesh and applies it to setup/integration tasks inside the NAUTILUS architecture at `C:\telo\Efforts\Ongoing\NAUTILUS`.

---

## 1. Agent Registry

| Agent | Local path | Version | Official docs source |
|---|---|---|---|
| **Claude Code** | `C:\agents\Claude` | current subscription | `https://docs.anthropic.com/en/docs/claude-code` |
| **Hermes** (NousResearch) | `C:\agents\Hermes` | 0.13.0 | `https://github.com/NousResearch/hermes-agent` → README + wiki |
| **Gemini CLI** | `C:\agents\Gemini` | 0.42.0 | `https://github.com/google-gemini/gemini-cli` |
| **Codex** | `C:\agents\codex` | npm-latest | `https://github.com/openai/codex` |
| **Antigravity (agy)** | `C:\agents\Antigravity` | 1.0.6 | binary-only; use `agy --help` or check release notes |

Config files that govern runtime behavior:

| Agent | Key config path |
|---|---|
| Claude Code | `C:\agents\Claude\.claude_global\CLAUDE.md` · `settings.json` · `.mcp.json` |
| Hermes | `C:\agents\Hermes\.hermes_global\config.yaml` · `models.yaml` · `channel_directory.json` |
| Gemini CLI | `C:\agents\Gemini\data\GEMINI.md` · `settings.json` · `projects.json` |
| Codex | `C:\agents\codex\` (npm package; config via env vars) |

---

## 2. Fetch Protocol

When the user asks a question about agent setup or a feature that may have changed since training:

**Step 1 — Identify the agent and topic:**
- Which agent? → pick the row from the registry above.
- What topic? → e.g. "MCP configuration", "model routing", "skill system", "gateway setup", "auth".

**Step 2 — Search for current docs:**
Use WebSearch:
```
"<AgentName> <topic>" site:<docs-domain> OR site:github.com/<org>/<repo>
```
Examples:
- `"hermes-agent MCP configuration" site:github.com/NousResearch/hermes-agent`
- `"gemini-cli GEMINI.md tools" site:github.com/google-gemini/gemini-cli`
- `"claude code hooks" site:docs.anthropic.com`

**Step 3 — Fetch the authoritative page:**
Use WebFetch on the URL returned by Step 2. For GitHub repos, fetch the raw README or a specific docs file:
```
https://raw.githubusercontent.com/<org>/<repo>/main/README.md
https://raw.githubusercontent.com/<org>/<repo>/main/docs/<topic>.md
```

**Step 4 — Apply to the task:**
Cross-reference the fetched content with:
- The agent's local config at the path in the registry
- The NAUTILUS integration layer (Section 3)
- SOVERN mandates (Section 4)

---

## 3. NAUTILUS Integration Layer

**Architecture:** `C:\telo\Efforts\Ongoing\NAUTILUS`

### LiteLLM Gateway (primary routing layer)
- **URL:** `http://localhost:4001` (note: port 4001, not 4000)
- **Config:** `C:\telo\Efforts\Ongoing\NAUTILUS\config\litellm-config.yaml`
- **Model names in use:**
  - `fast-pool` — rotating free cloud (Cerebras Qwen3-235B, Groq Llama 3.3 70B, NIM, OpenRouter)
  - `google/gemini-3-flash-preview` — Hermes primary brain (Google AI Studio free tier)
  - `local-fallback` — llama-server Qwen3-Coder-30B-A3B at `http://localhost:8080/v1`
  - `reasoning` — Groq Qwen3-32B
- **Fallback chain:** `gemini-3-flash-preview` → `fast-pool` → `hf-llama-70b` → `local-fallback`

### Connecting an agent to the gateway
Any agent that supports OpenAI-compatible API:
```yaml
base_url: http://localhost:4001/v1
api_key: dummy   # LiteLLM does not enforce a proxy key unless configured
model: fast-pool # or google/gemini-3-flash-preview
```
For Hermes: edit `C:\agents\Hermes\.hermes_global\config.yaml` → `model.base_url`.
For Gemini CLI: add `GEMINI_API_BASE=http://localhost:4001/v1` or edit `settings.json`.
For Codex: set `OPENAI_BASE_URL=http://localhost:4001/v1`.

### Shared MCP config
Claude Code MCP registry: `C:\agents\Claude\.claude_global\.mcp.json`  
When a new MCP server is added, check if Hermes also needs it in its toolset (Hermes has its own MCP tool loader at `C:\agents\Hermes\tools\mcp_tool.py`).

### NAUTILUS skills directory
Skills shared across agents: `C:\telo\Efforts\Ongoing\NAUTILUS\skills\`  
Claude Code skills: `C:\Users\sasha\.claude\skills\`  
Hermes skills: `C:\agents\Hermes\skills\`  
Gemini CLI skills: loaded via `GEMINI.md` references or `skills/` in project root.

---

## 4. SOVERN Mandates (integration constraints)

Before proposing any config change, verify compliance:

1. **ACE Root Standard** — no files in `C:\telo` root outside Atlas/Calendar/Efforts/logs.
2. **Agent Residency** — all agent state/cache/config lives under `C:\agents\<AgentName>\`. If a tool forces a dot-folder in root, create a symlink junction → `C:\agents\<AgentName>\.dot-folder`.
3. **Sovereignty** — local-first: prefer `localhost:4001` (LiteLLM) before cloud APIs. Local floor: `localhost:8080` (llama-server Qwen3-Coder).
4. **No ANTHROPIC_API_KEY** — Claude Code uses subscription auth only.
5. **Dry-Run Gate** — for any stateful change (config mutation, file creation, service restart), state the change + affected files and wait for explicit approval.

---

## 5. Common Integration Tasks

### Task: Add new agent to the mesh
1. Fetch latest install docs for the agent (Step 2–3 above).
2. Install binary/package into `C:\agents\<AgentName>\`.
3. Set `base_url` → `http://localhost:4001/v1`.
4. Copy or symlink relevant MCP servers from `.mcp.json`.
5. If the agent supports a global config file (AGENTS.md / GEMINI.md / CLAUDE.md), symlink it from `C:\agents\<AgentName>\` into the project root if required.
6. Add an entry to `C:\telo\Efforts\Ongoing\NAUTILUS\config\services.json`.
7. Document in `C:\telo\Efforts\Ongoing\NAUTILUS\docs\claude-code-capabilities.md` (or equivalent for the new agent).

### Task: Update model routing for an agent
1. Check current config at the path in the registry.
2. Verify available models in `litellm-config.yaml`.
3. Edit the agent config to point to the correct `model_name`.
4. Restart LiteLLM if config changed: `litellm --config litellm-config.yaml --port 4001`.

### Task: Debug agent not reaching gateway
Checklist:
- Is LiteLLM running? `Invoke-WebRequest http://localhost:4001/health`
- Is the model name correct? Check `litellm-config.yaml` model_list entries.
- Is the API key set? Check env vars: `GEMINI_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`, etc.
- Is llama-server running for local fallback? `Invoke-WebRequest http://localhost:8080/health`

### Task: Sync a skill across agents
- Claude Code: `C:\Users\sasha\.claude\skills\<skill-name>\SKILL.md`
- NAUTILUS shared: `C:\telo\Efforts\Ongoing\NAUTILUS\skills\<skill>.md`
- Hermes: `C:\agents\Hermes\skills\<skill>.md`
- Gemini CLI: reference in `C:\agents\Gemini\data\GEMINI.md` under `skills:` section.

---

## 6. Quick CLI Reference

```powershell
# Check agent versions
& "C:\agents\Antigravity\core\agy.exe" --version
& "C:\agents\Gemini\core\node_modules\.bin\gemini" --version
python -c "import importlib.metadata; print(importlib.metadata.version('hermes-agent'))"

# Launch agents (headless mode — always close stdin for non-interactive)
# Codex headless (close stdin to prevent hang):
cmd /c "echo task | C:\agents\codex\codex.cmd ..."

# Hermes one-shot:
python "C:\agents\Hermes\cli.py" -p "task description"

# LiteLLM gateway start:
litellm --config "C:\telo\Efforts\Ongoing\NAUTILUS\config\litellm-config.yaml" --port 4001
```
