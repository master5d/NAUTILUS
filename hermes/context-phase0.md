# Hermes Context — Phase 0 Handover
# SOVRN v3.4 | Date: 2026-05-23

## What Was Built (Phase 0 — Complete)

### Infrastructure (all running)

| Service | Status | Endpoint | Notes |
|---------|--------|----------|-------|
| Docker Desktop | ✅ 29.4.1 | — | WSL2 backend |
| Langfuse | ✅ v2.95.11 | http://localhost:3000 | Pinned to :2 tag (v3 requires ClickHouse) |
| LiteLLM Proxy | ✅ | http://localhost:4000 | 6/8 models healthy |
| llama-server | ✅ | http://localhost:8080 | Qwen3-Coder-30B-A3B, CUDA |
| Hermes Gateway | ✅ | Telegram | 114 commands, gpt-oss-120b:free |

### How to Start Services

```powershell
# Langfuse (Docker)
cd "C:\telo\Efforts\Ongoing\NAUTILUS\docker"
docker compose up -d

# LiteLLM proxy
pwsh -ExecutionPolicy Bypass -File "C:\telo\Efforts\Ongoing\NAUTILUS\scripts\launch-litellm.ps1"

# llama-server (Qwen3-Coder, CUDA)
pwsh -ExecutionPolicy Bypass -File "C:\telo\Efforts\Ongoing\NAUTILUS\scripts\launch-llama-server.ps1"

# Hermes Telegram gateway
wsl -e bash -c "hermes gateway run"
```

### LiteLLM Pool (port 4000)

Model alias `fast-pool` rotates across:
- `cerebras/qwen-3-235b-a22b-instruct-2507` — ~1000 TPS, 1M tok/day
- `groq/llama-3.3-70b-versatile` — 30 RPM
- `groq/meta-llama/llama-4-scout-17b-16e-instruct` — 10M context
- `openai/meta/llama-3.3-70b-instruct` via NIM — 40 RPM
- `openrouter/meta-llama/llama-3.3-70b-instruct:free` — 1K RPD

Fallback: `local-fallback` → `openai/qwen3-coder` on port 8080

Reasoning: `groq/qwen/qwen3-32b` (hybrid thinking, replaces deepseek-r1)

### Hermes Model

- **Model:** `openai/gpt-oss-120b:free` via OpenRouter
- **Provider:** openrouter
- **Why:** NousResearch Hermes 3/4 models do NOT support tool calling. gpt-oss-120b:free is the best free OpenRouter model with tool use.
- **Config:** `/root/.hermes/config.yaml` (WSL2)

### Skills Installed (`~/.hermes/skills/`)

| Skill | Type | Execution |
|-------|------|-----------|
| `architect.md` | workflow | stateless |
| `ingest_email.md` | workflow | stateful |
| `publish_podcast.md` | workflow | stateful |
| `compound_engineering.md` | workflow | stateless |
| `evo_promote.md` | workflow | stateful |
| `pii_redact.md` | tool | stateless |
| `dry_run_gate.md` | tool | stateless |
| `consolidate_daily.md` | workflow | stateful |

---

## Pending (Phase 0 — Not Yet Done)

### 1. ACE Vault (`~/life/`)
- **Script:** `C:\telo\Efforts\Ongoing\NAUTILUS\scripts\setup-ace.ps1` — generated but NOT run
- **Action:** Run `pwsh -ExecutionPolicy Bypass -File "C:\telo\Efforts\Ongoing\NAUTILUS\scripts\setup-ace.ps1"`
- **Creates:** Full `~/life/` ACE structure + tacit knowledge files + first daily note

### 2. Hermes Telegram Gateway Restart
- After config change (model update), gateway needs restart
- **Action:** `wsl -e bash -c "hermes gateway run"`

---

## Architecture Decisions (Locked for Phase 0–1)

**Langfuse v2 (not v3):**
Langfuse v3 made ClickHouse mandatory (not optional). ClickHouse adds ~2GB RAM + 3 extra containers for zero solo-user benefit. Stay on v2 until Phase 2–3 when multi-user or high-volume tracing is needed.

**Docker MCP Toolkit (Phase 1):**
Announced DockerCon 2025. Runs MCP servers as isolated Docker containers — Langfuse MCP, GitHub MCP, etc. via Docker Desktop GUI. No daemon setup needed. Add in Phase 1.

**CUDA 13.2+ FORBIDDEN for llama.cpp:**
llama.cpp CUDA builds break on 13.2+. Use b8943/b8946 (CUDA 13.1). This is a hard constraint in the sovereignty rules.

---

## Phase 1 — What Comes Next

1. **Cloud pool fine-tuning** — monitor Cerebras/Groq rate limits, adjust rpm caps
2. **Docker MCP Toolkit** — Langfuse MCP server as container
3. **Gmail ingest Phase I** — 211-email dump, tagging, ACE routing
4. **graphiti/FalkorDB** — only if ACE flat-file search fails 3+ times/week
5. **Handy (voice):** `winget install cjpais.Handy`

---

## Key File Locations

```
C:\telo\Efforts\Ongoing\NAUTILUS\
├── config\litellm-config.yaml      # LiteLLM rotating pool
├── docker\docker-compose.yml       # Langfuse self-hosted
├── scripts\
│   ├── launch-litellm.ps1          # Start LiteLLM (loads keys from User env)
│   ├── launch-llama-server.ps1     # Start llama-server CUDA
│   ├── launch-hermes.ps1           # Start Hermes + health check
│   ├── setup-litellm-keys.ps1      # One-time key setup (SecureString)
│   └── setup-ace.ps1               # Create ~/life/ ACE vault
├── hermes\
│   ├── system-prompt.md            # Hermes identity + DeepVista rules
│   └── context-phase0.md           # This file
└── docs\
    ├── llama-cpp-setup.md          # llama.cpp CUDA 13.1 install guide
    └── compound-engineering-setup.md

WSL2:
~/.hermes/config.yaml               # model: openai/gpt-oss-120b:free
~/.hermes/.env                      # OPENROUTER_API_KEY + Telegram tokens
~/.hermes/skills/                   # 8 DeepVista skills
```

---

## Verification Commands

```bash
# LiteLLM health
curl http://localhost:4000/health

# llama-server health
curl http://localhost:8080/health

# Hermes chat test
wsl -e bash -c "hermes chat -q 'What skills do you have?'"

# Langfuse
# Open http://localhost:3000 in browser
```

