# Hermes Context — Phase 1 Handover
# SOVRN v3.3 | Date: 2026-04-29

---

## What Was Built (Phase 1 — In Progress)

### Infrastructure (current state)

| Service | Status | Endpoint | Notes |
|---------|--------|----------|-------|
| Docker Desktop | ✅ 29.4.1 | — | WSL2 backend |
| Langfuse | ✅ v2.95.11 | http://localhost:3000 | Pinned to :2 tag |
| LiteLLM Proxy | ✅ | http://localhost:4000 | Gemini + fast-pool + local |
| llama-server | ✅ | http://localhost:8080 | Qwen3-Coder-30B-A3B, CUDA |
| Hermes Gateway | ✅ | Telegram | Gemini 2.5 Flash brain |
| GitHub MCP | ✅ | stdio (on-demand) | 45 tools via wrapper script |

### How to Start Services

**ВАЖНО:** LiteLLM должен быть запущен ДО Hermes — иначе Hermes упадёт на OpenRouter fallback.

```powershell
# 1. Langfuse (Docker)
cd "C:\telo\Efforts\Ongoing\SOVERN\docker"
docker compose up -d

# 2. LiteLLM proxy (СНАЧАЛА — Hermes зависит от него)
pwsh -ExecutionPolicy Bypass -File "C:\telo\Efforts\Ongoing\SOVERN\Atlas\Scripts\launch-litellm.ps1"

# 3. llama-server (Qwen3-Coder, CUDA) — опционально, нужен как fallback
pwsh -ExecutionPolicy Bypass -File "C:\telo\Efforts\Ongoing\SOVERN\Atlas\Scripts\launch-llama-server.ps1"

# 4. Hermes Telegram gateway
wsl -e bash -c "hermes gateway run"
```

---

## Hermes Model (Phase 1 upgrade)

- **Primary:** `google/gemini-3-flash-preview` → маршрутизируется через LiteLLM → `gemini/gemini-2.5-flash` (Google AI Studio)
- **Provider:** openrouter (Hermes видит OpenRouter, фактически идёт в LiteLLM на localhost:4000)
- **Key:** `GEMINI_API_KEY` в Windows User env, загружается в LiteLLM при старте
- **Free tier:** 15 RPM, 1500 RPD, 1M context
- **Fallback 1:** `fast-pool` (Cerebras qwen-3-235b ~1000 TPS)
- **Fallback 2:** `local-fallback` (Qwen3-Coder на порту 8080)
- **Fallback Hermes-level:** `openai/gpt-oss-120b:free` via OpenRouter (если LiteLLM недоступен)

### Почему такая схема

Hermes валидирует модели по своему каталогу (Nous Research). `google/gemini-3-flash-preview` — валидное имя в каталоге. LiteLLM перехватывает запрос и направляет на Google AI Studio free tier вместо OpenRouter, не тратя OR-кредиты.

---

## LiteLLM Pool (port 4000)

| Alias | Модель | Провайдер | Лимит |
|-------|--------|-----------|-------|
| `google/gemini-3-flash-preview` | gemini/gemini-2.5-flash | Google AI Studio | 15 RPM, 1500 RPD |
| `fast-pool` | cerebras/qwen-3-235b-a22b | Cerebras | ~1000 TPS, 1M tok/day |
| `fast-pool` | groq/llama-3.3-70b-versatile | Groq | 30 RPM |
| `fast-pool` | groq/llama-4-scout-17b | Groq | 10M context |
| `fast-pool` | openai/meta/llama-3.3-70b via NIM | NVIDIA | 40 RPM |
| `fast-pool` | openrouter/llama-3.3-70b:free | OpenRouter | 1K RPD |
| `reasoning` | groq/qwen/qwen3-32b | Groq | hybrid thinking |
| `local-fallback` | openai/qwen3-coder | localhost:8080 | unlimited |

Fallback chain: `google/gemini-3-flash-preview` → `fast-pool` → `local-fallback`

---

## WSL2 Configuration (Phase 1 changes)

### `/etc/wsl.conf` (внутри WSL)
```ini
[boot]
systemd=true

[user]
default=root   # Hermes установлен как root, нужен root по умолчанию
```

### `C:\Users\sasha\.wslconfig` (Windows)
```ini
[wsl2]
networkingMode=mirrored   # localhost в WSL резолвит Windows-хост (нужно для LiteLLM)
```

**Следствие mirrored networking:** `localhost:4000` из WSL достигает LiteLLM на Windows. Без этого Hermes не может использовать LiteLLM proxy.

---

## GitHub MCP (Phase 1 Track B — Complete)

- **Image:** `ghcr.io/github/github-mcp-server` (45 tools)
- **Wrapper:** `/root/.hermes/bin/github-mcp.sh` — читает GITHUB_TOKEN из `.env`
- **Auth:** Fine-grained PAT, 90 дней, scope: Contents/Issues/PRs/Workflows R+W
- **Registered:** `hermes mcp list` → github (45 tools)
- **Docker profile:** `agentic_ai` в Docker Desktop с GitHub Official сервером

```bash
# Тест GitHub MCP
hermes chat -q "Use GitHub MCP get_me tool to show my GitHub login"
```

---

## Web Search (Phase 1 — добавлено)

- **Provider:** Tavily (`TAVILY_API_KEY` в `~/.hermes/.env`)
- **Free tier:** 1000 запросов/месяц
- **Добавлен через:** `hermes setup` внутри Hermes

---

## API Keys (полный список)

### Windows User Environment
| Key | Для |
|-----|-----|
| `CEREBRAS_API_KEY` | LiteLLM fast-pool |
| `GROQ_API_KEY` | LiteLLM fast-pool + reasoning |
| `NIM_API_KEY` | LiteLLM fast-pool (NVIDIA) |
| `OPENROUTER_API_KEY` | LiteLLM fast-pool + Hermes fallback |
| `GEMINI_API_KEY` | LiteLLM → Gemini 2.5 Flash (primary Hermes brain) |
| `LANGFUSE_PUBLIC_KEY` | LiteLLM observability |
| `LANGFUSE_SECRET_KEY` | LiteLLM observability |

### WSL `~/.hermes/.env`
| Key | Для |
|-----|-----|
| `OPENROUTER_API_KEY` | Hermes provider auth |
| `GITHUB_TOKEN` | GitHub MCP (fine-grained PAT, ротирован 2026-04-29) |
| `TELEGRAM_BOT_TOKEN` | Hermes Telegram gateway |
| `TELEGRAM_ALLOWED_USERS` | Whitelist для gateway |
| `TAVILY_API_KEY` | Web search toolset |

---

## Skills Installed (`~/.hermes/skills/`)

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

## Architecture Decisions (Locked для Phase 1–2)

**Langfuse v2 (not v3):**
v3 требует ClickHouse обязательно. ~2GB RAM + 3 контейнера без выгоды для solo setup. Апгрейд в Phase 2–3.

**CUDA 13.2+ FORBIDDEN для llama.cpp:**
llama.cpp CUDA builds ломаются на 13.2+. Использовать b8943/b8946 (CUDA 13.1). Жёсткое ограничение.

**Agent Vault (Infisical) — деferred до Phase 2:**
HTTP credential proxy — агенты не видят секреты. Инструмент в preview (создан март 2026), месяц от роду. Добавить когда появятся несколько агентов, разделяющих credentials. Repo: `github.com/Infisical/agent-vault`.

**Hermes model через LiteLLM proxy:**
Hermes валидирует модели по каталогу Nous Research. Используем `google/gemini-3-flash-preview` как alias в LiteLLM — имя проходит валидацию каталога, маршрутизируется на Google AI Studio free tier.

**WSL default user = root:**
Hermes, uv Python, все конфиги установлены в `/root/`. Mirrored networking требует рестарта WSL, после которого default user сбрасывался бы на sasha. Зафиксировано в `/etc/wsl.conf`.

---

## Pending (Phase 1)

### Track A: Gmail Phase I (не начат)
- Дамп 211 писем из Gmail (лейбл "AI Ingest") → `~/life/Atlas/References/AI-Ingest/`
- Формат: PARA Markdown с YAML frontmatter
- Нужно: Google OAuth / Gmail API setup
- Оценка: ~4 часа

### Track C: LangGraph Postgres Checkpointer (опционально)
- Можно пропустить до Phase II Gmail ingest

---

## Key File Locations

```
C:\telo\Efforts\Ongoing\SOVERN\
├── config\litellm-config.yaml      # LiteLLM pool (gemini + fast-pool + local)
├── docker\docker-compose.yml       # Langfuse self-hosted
├── scripts\
│   ├── launch-litellm.ps1          # Start LiteLLM (загружает GEMINI_API_KEY + все ключи)
│   ├── launch-llama-server.ps1     # Start llama-server CUDA
│   ├── launch-hermes.ps1           # Start Hermes + health check
│   └── setup-para.ps1              # Create ~/life/ PARA vault
├── hermes\
│   ├── system-prompt.md            # Hermes identity + DeepVista rules
│   ├── context-phase0.md           # Phase 0 handover (исторический)
│   ├── context-phase1.md           # Этот файл
│   └── reports\
│       └── phase1-track-b.md       # Docker MCP / GitHub MCP report

C:\Users\sasha\.wslconfig           # WSL2 mirrored networking

WSL2 (/root/):
~/.hermes/config.yaml               # model: google/gemini-3-flash-preview, base_url: localhost:4000
~/.hermes/.env                      # OPENROUTER + GITHUB_TOKEN + TELEGRAM + TAVILY
~/.hermes/skills/                   # 8 DeepVista skills
~/.hermes/bin/github-mcp.sh         # GitHub MCP wrapper (читает GITHUB_TOKEN из .env)
/etc/wsl.conf                       # default=root, systemd=true
```

---

## Verification Commands

```bash
# LiteLLM health + модели
curl http://localhost:4000/v1/models -H "Authorization: Bearer dummy"

# Hermes chat test (требует запущенный LiteLLM)
wsl -e bash -c "hermes chat -q 'What model are you?'"

# GitHub MCP test
wsl -e bash -c "hermes chat -q 'Use GitHub MCP get_me tool'"

# Web search test
wsl -e bash -c "hermes chat -q 'Search the web: latest Gemini model release'"

# llama-server health
curl http://localhost:8080/health

# Langfuse UI
# http://localhost:3000
```

---

## Phase Roadmap (верхний уровень)

| Phase | Weeks | Ключевые задачи | Budget |
|-------|-------|-----------------|--------|
| **0** | 1 | ✅ Hermes, PARA, skills, llama.cpp, LiteLLM, Langfuse | ~$0 |
| **1** | 2–3 | ✅ GitHub MCP, Gemini brain, Tavily search · ⏳ Gmail ingest Phase I | ~$0 |
| 2 | 4–6 | Hetzner+Dokploy, Notion→Obsidian, Evernote→archive, Astro site, Agent Vault | ~$5–10/mo |
| 3 | 7–10 | Revenue: affiliate sites, TG bots, Apify, Grafana+Streamlit | ~$9–10/mo |
| 4 | 11–14+ | KMP Android, Godot, YouTube/podcast | +$0–30/mo |
