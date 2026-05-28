# Стек SOVRN V3.3 — Суверенная Архитектура Solo Vibe Coder

> **Дата:** 28 апреля 2026 · **Статус:** consolidated source of truth · **Заменяет:** v3.0 (Loop 1), v3.1 (Loop 2), v3.2 (Loop 3) · **Loop:** 4 (Gmail AI Ingest synthesis applied)
---
## TL;DR в одном абзаце
Sovereignty-first персональная AI-организация для Solo Vibe Coder на Surface Laptop Studio 2 (RTX 4060 8GB / 64GB RAM / Win11): локальный harness **Hermes Agent через ****`ollama launch hermes`** управляет sub-агентами **Aider + Cline + Compound Engineering plugin**; модельный gateway **LiteLLM** маршрутизирует между локальным **Qwen3-Coder-30B-A3B (MoE) на llama.cpp + CUDA 13.1** и пятью уровнями облачного фоллбэка **Cerebras → Groq → NIM → OpenRouter → HF Serverless (Llama-3.3-70B + Qwen2.5-72B)**; память — **двухступенчатая (ACE fast path → graphiti+FalkorDB+Qdrant slow path)**; skills — **DeepVista schema (type × execution)** с обязательным `--dry-run` для stateful; ingest — **Gmail AI Ingest → Hermes → graphiti**; хостинг — **Cloudflare + Hetzner CX23**; observability — **OpenLLMetry → Langfuse self-hosted**. Бюджет: $0 PoC / $20 (Claude Pro) / $30–60 (Anthropic API pay-as-you-go). Заменяемость каждого слоя — дни, не недели.
---
## Линейка изменений
| Версия | Loop | Что добавлено | Главные удаления |
| --- | --- | --- | --- |
| v3.0 | 1 | Hermes-as-boss; CrewAI; Qwen3.6-27B; NIM; custom Next.js dash | — |
| v3.1 | 2 | Pydantic AI; Aider+Cline; Qwen3-Coder-30B-A3B (MoE); rotating pool; graphiti+Neo4j+Qdrant; Cloudflare+Hetzner; Grafana+Streamlit; Handy | CrewAI как primary; OpenClaw как продукт |
| v3.2 | 3 | `--n-cpu-moe`; CUDA 13.1; FalkorDB; LiteLLM `fallbacks:`; `effort` parameter | Vulkan default; `thinking_budget_tokens`; Neo4j JVM на ноуте |
   14|| **v3.3** | **4** | **Hermes в Linux-оболочке (WSL2/Native); Compound Engineering plugin; DeepVista skill schema; ACE фаза-0 памяти; Ramp PM skill; NotebookLM as pipeline; Apify; Substack для digital-goods; HF Serverless 5th fallback (router.huggingface.co); models.yaml GGUF registry; hf-models skill** | **Ollama-нативный Hermes; custom evo-loop; 1-фазная graphiti с нуля** |
   15|---
   16|## 1. Слоистая архитектура (one-page mental model)
   17|```javascript
   18|┌─────────────────────────────────────────────────────────────────────┐
   19|│  HUMAN (Architect · PM · Operator · Reviewer)                       │
   20|│  ↕ Telegram + Zed + Claude Code CLI                                 │
   21|├─────────────────────────────────────────────────────────────────────┤
   22|│  BOSS / ORCHESTRATION                                                │
   23|│    Hermes Agent (Linux Shell / WSL2) — skills, cron, gateways        │
   24|├─────────────────────────────────────────────────────────────────────┤

│    architect.md (Ramp PM)  ·  ingest_email  ·  publish.podcast       │
│    compound_engineering    ·  evo (versioned A/B)                    │
├─────────────────────────────────────────────────────────────────────┤
│  CODING SUB-AGENTS                                                   │
│    Aider (CLI/git)  ·  Cline (VS Code)  ·  Claude Code               │
│    Compound Engineering plugin (Klaassen, /workflows /lfg)           │
├─────────────────────────────────────────────────────────────────────┤
│  MODEL GATEWAY — LiteLLM (with explicit fallbacks: array)            │
│    ┌─ local: llama.cpp + CUDA 13.1 → Qwen3-Coder-30B-A3B / 8B / 9B   │
│    └─ cloud: Cerebras → Groq → NIM → OpenRouter → HF Serverless      │
│       HF Serverless: router.huggingface.co (Llama-3.3-70B, Qwen2.5-72B) │
│       HF registry: ~/.hermes/models.yaml (commit-hash pinned GGUFs)  │
│       optional: Anthropic API pay-as-you-go via Aider                │
├─────────────────────────────────────────────────────────────────────┤
│  MEMORY                                                              │
│    Phase 0 (Felix/ACE):  Obsidian ~/life/ + daily.md + tacit.md     │
│    Phase 1 (graphiti):    FalkorDB + Qdrant + BGE-M3 + Qwen3-8B      │
├─────────────────────────────────────────────────────────────────────┤
│  TOOL LAYER — MCP (Linux Foundation, 97M monthly downloads)          │
│    graphiti MCP · Telegram relay · Granola · Playwright QA · Apify   │
├─────────────────────────────────────────────────────────────────────┤
│  OBSERVABILITY — OpenLLMetry SDK → Langfuse self-hosted              │
│  DASHBOARD     — Grafana (advanced) + Streamlit (simplified)         │
├─────────────────────────────────────────────────────────────────────┤
│  HOSTING FABRIC                                                      │
│    Edge: Cloudflare Pages + Workers + R2 + D1 ($0)                   │
│    Compute: Hetzner CX23 + Dokploy + n8n + Postiz (€3.79/mo)         │
│    Mail: Fastmail ($5/mo)                                            │
│    Local-only: Surface Laptop (никогда production server)            │
└─────────────────────────────────────────────────────────────────────┘

```
---
## 2. Hardware tier
**Целевое железо:** Surface Laptop Studio 2 · Intel i7-13800H · 64GB DDR5 · RTX 4060 Laptop 8GB VRAM · 1TB NVMe (430GB used) · Win11 Pro 25H2.
**Доп.:** Pixel 10 Pro XL + Pixel 6 Pro XL · SanDisk 4TB Extreme portable SSD · 2× YubiKey 5C NFC.
**Принципы.** Surface Laptop = primary dev + local inference. **Никогда не production server** (residential ISP, dynamic IP, battery wear, Win update reboots, thermal throttling). Production = Hetzner CX23 + Cloudflare. SanDisk 4TB = mirrored vault для Obsidian + graphiti dumps + model weights.
---
## 3. Local inference — llama.cpp + Qwen3-Coder-30B-A3B (MoE)
**Primary daily driver.** Qwen3-Coder-30B-A3B-Instruct (UD-Q4_K_XL, MoE, 3B active params), запускается через `llama-server`. **Не Ollama as primary** (Ollama — convenience wrapper).
**Build (Windows 11):** llama.cpp с CUDA 13.1 binaries (release `b8943`/`b8946`). **CUDA 13.2 запрещён** — issue #21255, Unsloth #4849: tensor math corruption на IQ3_S/IQ3_XXS/IQ2_M; fix не подтверждён в 13.3+.
**Эталонный launch:**
```javascript
llama-server -m Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf \
  --jinja -ngl 99 --n-cpu-moe 34 -c 32768 \
  -fa on -ctk q8_0 -ctv q8_0 --no-mmap \
  --threads <physical-cores> --threads-batch <physical-cores> \
  -b 2048 -ub 512 \
  --temp 0.7 --top-p 0.8 --top-k 20 --repeat-penalty 1.05

```
Тюнинг: `--n-cpu-moe` уменьшать вниз до OOM, отступать на 1–2. Для Q5/Q6 → 38–40. `-fa on` обязателен для `-ctk/-ctv q8_0`. Ожидаемый throughput: **15–25 tok/s** типично, **8–12 tok/s** на 32K контекста.
**Tier ladder.**
| Модель | Назначение | VRAM | Speed |
| --- | --- | --- | --- |
| Qwen3-Coder-30B-A3B Q4 | daily coding | ~5.5GB резидентно | 15–25 tok/s |
| Qwen3.6-35B-A3B Q4 | heavy reasoning fallback | ~7GB | 12–18 tok/s |
| Qwen3.5-9B Q4 | fast autocomplete, 200K ctx | full GPU | 50+ tok/s |
| Qwen3-8B Instruct Q4 | graphiti extraction LLM | ~5GB | 30–50 tok/s |
| GPT-OSS-20B Q4 | OpenAI-aligned baseline | full GPU | 25–35 tok/s |
**Альтернативы отклонены:** Vulkan backend (5GB VRAM-claim не подтверждён, prompt processing проигрывает CUDA, WSL2 требует Dozen path). Ollama as primary (mutable tags, нет Vulkan без source build, не поддерживает Qwen3.6 GGUF из коробки).
---
   86|## 4. Boss/Orchestration — Hermes Agent (Linux-оболочка)
   87|**Установка (v3.3 correction):**
   88|Hermes запускается напрямую в Linux (WSL2 или Native Shell). Это дает полный контроль над окружением, системными зависимостями и интеграцией с MCP серверами. **Ollama используется только как один из провайдеров моделей**, но не как среда запуска Hermes.
   89|
   90|Команда запуска:
   91|```bash
   92|hermes gateway run
   93|```
   94|**Ответственность Hermes.** Telegram-relay primary, cron triggers, skills lifecycle, sub-agent dispatch.

- Telegram bot token → primary control plane
- Skills folder: `~/.hermes/skills/` (DeepVista schema, см. §6)
- Cron: nightly memory consolidation (PARA → graphiti), weekly digest, monthly skill A/B promotion
- Никакого self-modification meta-agent (Loop 3 «линия, которую не пересекаем»)
---
## 5. Coding sub-agents
**Stack:**
| Tool | Когда | Лицензия | Лок-ин |
| --- | --- | --- | --- |
| **Aider** | CLI/git, refactor, mature; работает с любой моделью через LiteLLM | Apache 2.0 | минимальный |
| **Cline** | VS Code/VSCodium, BYOK, длинные сессии | Apache 2.0 | минимальный |
| **Claude Code** | когда нужна максимальная глубина; через API pay-as-you-go | Anthropic | средний |
| **Compound Engineering plugin** (Klaassen) | `/workflows`, `/lfg`, Playwright MCP QA | MIT | минимальный |
**Compound Engineering loop** (Loop 4, P2):
```javascript
Plan → Work → Assess → Compound
  │      │      │         └─ capture learnings → claude.md
  │      │      └─ review agents (security/architect/quality)
  │      └─ Claude asks clarifying Qs first
  └─ sub-agents research codebase + best practices in parallel

```
Установка: `claude code plugin install compound-engineering` (или эквивалент в маркетплейсе плагинов).
**Cursor — отклонён:** proprietary, весь контекст через Cursor servers, opaque privacy. **Trae — запрещён:** ByteDance telemetry, 5-year retention, no opt-out.
---
## 6. Skills schema — DeepVista (новое в v3.3)
Источник: deepvista.substack.com / Jingconan Wang (письмо 20 апр 2026).
**Каждый SKILL.md имеет YAML-фронтматтер:**
```javascript
---
name: PR Review
type: workflow         # persona | tool | workflow
execution: stateful    # stateless | stateful
description: Review PR for security and code quality issues.
---

## Steps
1. Fetch the pull request
2. Analyze the code
3. Generate feedback
4. Post review comments

## Side Effects
- Writes comments to GitHub
- May update review status

## Related Skills
- Code Reviewer
- Post GitHub Comment

```
**Правила интерпретации (вшиты в Hermes system prompt):**
- `type: persona` → load as background context, don't invoke as command
- `type: tool` → invoke when task requires, return result
- `type: workflow` → run sequence in order, no mixing with other skills
- `execution: stateless` → run freely, retry on failure
- `execution: stateful` → **обязательный ****`--dry-run`**** или summary + confirmation**
**Fallback:** missing fields → treat as `stateful`, apply checkpoint.
**Минимальный starter set skills для v3.3:**
| Skill | type | execution | Источник |
| --- | --- | --- | --- |
| `architect.md` | workflow | stateless | Ramp PM (Geoff Charles, 15 мар 2026) — 7 framing вопросов, 6–10 parallel research agents, 2-min spec |
| `ingest_email` | workflow | stateful | Loop 4, §11 |
| `publish.podcast` | workflow | stateful | NotebookLM wrapper (P7) |
| `compound_engineering` | workflow | stateless | Klaassen plugin (P2) |
| `evo_promote` | workflow | stateful | Wilson lower-bound A/B promotion + Telegram approval |
| `pii_redact` | tool | stateless | для всех outbound writes |
| `dry_run_gate` | tool | stateless | wrap stateful actions |
| **`hf-models`** | **tool** | **stateful** | **HF Model Manager — `hf status/check/download/pin`; пишет в models.yaml** |
---
## 7. Memory — двухступенчатая (ACE fast path → graphiti slow path)
**Главное обновление v3.3 (P4):** не строить graphiti с нуля. Сначала фаза 0 — ACE на Markdown.
### Фаза 0 — Felix/ACE stack (~30 минут setup)
Источник: Nat Eliason, "Use OpenClaw to Build a Business That Runs Itself" (22 фев 2026), 3-layer memory:
```javascript
~/life/                                  # Obsidian vault
├── Efforts/On/                            # ACE Layer 1: knowledge graph
│   ├── 01-knowledge-graph-foundation/
│   ├── 02-affiliate-agency/
│   ├── 03-digital-goods/
│   ├── 04-android-tg-bots/
│   ├── 05-yt-social/
│   ├── 06-game-defi/
│   └── 07-native-windows-apps/
├── Efforts/Ongoing/                               # ongoing responsibilities
├── Atlas/References/                           # reference material
│   └── AI-Ingest/                       # см. §11
├── Atlas/Archives/
├── Calendar/Logs/                               # Layer 2: per-date markdown
│   └── 2026-04-28.md
└── Atlas/Workflows/                               # Layer 3: tacit knowledge
    ├── communication-preferences.md
    ├── workflow-habits.md
    ├── hard-rules.md
    └── lessons-from-past-mistakes.md

```
**Hermes-skill ****`consolidate_daily`**** (cron 02:00 ежедневно):** читает `Calendar/Logs/<today>.md` → извлекает durable facts → пишет в `Efforts/On/Efforts/Ongoing/resources` с YAML-фронтматтером → пишет ссылки обратно в `Calendar/Logs/`.
### Фаза 1 — graphiti slow path (запускать только после 1–2 недель ACE, если упирается)
Только когда ACE перестаёт хватать (multi-hop queries, temporal reasoning, contradictions tracking):
| Компонент | Pick | Лицензия |
| --- | --- | --- |
| Graph DB | **FalkorDB** (P3 из v3.2) | SSPLv1 (личное использование OK) |
| Vector store | **Qdrant local** Docker | Apache 2.0 |
| Embedding model | **BGE-M3 fp16** на 4060 (~1.2GB) | MIT |
| Extraction LLM | **Qwen3-8B Instruct Q4** (`enable_thinking:false`) | Apache 2.0 |
| Framework | **graphiti MCP Server v1.0** | Apache 2.0 |
| Image | `zepai/knowledge-graph-mcp:standalone` | — |
**FalkorDB persistence:** AOF `everysec` + RDB, mount `/var/lib/falkordb/data` to host volume, `aof-use-rdb-preamble yes`.
**Не использовать:** Neo4j Community JVM на ноуте (memory bloat); Kùzu (archived Oct 2025); Memgraph (нет out-of-box graphiti driver). **Можно использовать:** Neo4j AuraDB managed cloud для priority-#6 (game/DeFi-graph) с GCP $300 кредита (Loop 4 уточнение).
---
## 8. Cloud fallback — LiteLLM rotating pool
**Pool composition** (все OpenAI-compatible, все бесплатные):
| Provider | Free tier | Сильная сторона |
| --- | --- | --- |
| **Cerebras** | 1M tok/day, 30 RPM, ~1000 TPS | volume + speed |
| **Groq** | 30 RPM, 6K TPM, 1K RPD | low latency |
| **NVIDIA NIM** | 40 RPM/model, no daily cap | model breadth (DeepSeek V4, Kimi K2.6, GLM-5) |
| **OpenRouter** ($10 deposit) | 1K RPD across 29 free models | optionality |
| **HF Serverless** (новое v3.3) | бесплатно с HF_TOKEN, rate limited | 5th fallback; cold start 5–30s |
**HF Serverless models:** `meta-llama/Llama-3.3-70B-Instruct` (hf-llama-70b) → `Qwen/Qwen2.5-72B-Instruct` (hf-qwen-72b). Endpoint: `https://router.huggingface.co/v1` (OpenAI-compatible; `openai/` prefix в LiteLLM). **Не** `api-inference.huggingface.co/v1` — устаревший.
**HF Model Registry:** `~/.hermes/models.yaml` — единственный источник правды для локальных GGUF-моделей, закреплённых по полному commit hash (40 chars). Никогда `revision: main`.
**Платный когда нужно:** Anthropic API pay-as-you-go через Aider, $30–60/мес. Walk-away anytime.
**LiteLLM config (P4 из v3.2 — критический):**
```javascript
model_list:
  - model_name: fast-pool
    litellm_params: {model: cerebras/llama-4-maverick, api_key: os.environ/CEREBRAS_API_KEY, rpm: 30}
  - model_name: fast-pool
    litellm_params: {model: groq/llama-3.3-70b-versatile, api_key: os.environ/GROQ_API_KEY, rpm: 30}
  - model_name: fast-pool
    litellm_params: {model: openai/meta/llama-3.3-70b-instruct, api_base: https://integrate.api.nvidia.com/v1, api_key: os.environ/NIM_API_KEY, rpm: 60}
  - model_name: local-fallback
    litellm_params: {model: openai/qwen3-coder, api_base: http://localhost:8080/v1, api_key: dummy}

litellm_settings:
  fallbacks:                                         # CRITICAL — issue #26015
    - {"google/gemini-3-flash-preview": ["fast-pool", "hf-llama-70b", "local-fallback"]}
    - {"fast-pool": ["hf-llama-70b", "local-fallback"]}
    - {"hf-llama-70b": ["hf-qwen-72b", "local-fallback"]}
    - {"hf-qwen-72b": ["local-fallback"]}
    - {"reasoning": ["reasoning-local"]}
  default_fallbacks: ["local-fallback"]
  context_window_fallbacks: [{"fast-pool": ["local-fallback"]}]
  request_timeout: 60
  num_retries: 2

router_settings:
  routing_strategy: simple-shuffle
  cooldown_time: 60
  allowed_fails: 1
  retry_policy:
    RateLimitErrorRetries: 2
    TimeoutErrorRetries: 2
    InternalServerErrorRetries: 3
  allowed_fails_policy:
    RateLimitErrorAllowedFails: 2

```
**Pin LiteLLM version**, не `main-latest`. Custom providers регистрировать как `openai/...` namespace (избегает #24366 mis-classification).
---
## 9. Reasoning budgets (P5 из v3.2)
`thinking_budget_tokens` **deprecated на Claude 4.6/4.7** в пользу `effort` + опционального `task_budget` (beta header `task-budgets-2026-03-13`).
| Модель | Контроль | Дефолт |
| --- | --- | --- |
| Claude Opus 4.7 | `output_config.effort` + `task_budget` | medium |
| Claude Sonnet 4.6 | `effort` only | **explicitly set ****`medium`** для агентов |
| Claude Haiku 4.5 / Sonnet 4 / 3.7 | legacy `thinking={"type":"enabled","budget_tokens":N}` | min 1024 |
| DeepSeek V3.2 / R1 | `extra_body={"thinking":{"type":"enabled|disabled"}}` + `reasoning_effort` | R1 always thinks |
| OpenAI o-series, GPT-OSS-120B | `reasoning_effort` (none/min/low/med/high/xhigh) | medium |
| Qwen3.5/3.6 (local) | `--chat-template-kwargs '{"enable_thinking":false}'` + stop tokens + `--reasoning-budget` | combine all three |
**Правила распределения по типу задачи:**
| Task | Anthropic | DeepSeek | OpenAI |
| --- | --- | --- | --- |
| graphiti extraction | low / disabled | disabled | minimal |
| IDE autocomplete | low / none | disabled | minimal |
| coding agent step | medium | high | medium |
| architect / refactor planning | high (Opus xhigh) | enabled high | high |
| deep research | xhigh / max + task_budget | R1 enabled | xhigh |
---
## 10. Observability + Dashboard
**Instrument:** OpenLLMetry SDK (Apache 2.0) — vendor-neutral OTel exporter. Делает backend swappable.
**Backend default:** Langfuse self-hosted via Docker. **Альтернатива при росте:** Laminar (long-running agent debugging).
**Host metrics:** Prometheus + Grafana node-exporter + DCGM Exporter (GPU).
**Dashboard split (Loop 2):**
- **Grafana (advanced view):** GPU/CPU/RAM, agent traces from Langfuse, request rates
- **Streamlit (simplified view):** sprint status, agent activity, top errors, weekly digest
**Не строить custom Next.js.** Productivity trap для соло-оператора.
---
## 11. Ingest pipeline — Gmail "AI Ingest" → graphiti (новое в v3.3)
**Источник:** Loop 4 mining, 211 сообщений в корпусе, 200 уникальных тредов, 2 fwd-в-Evernote (Neo4j fraud-webinar).
**Конвейер:**
```javascript
Gmail watch() → Pub/Sub → Cloudflare Worker webhook
   → n8n workflow on Hetzner CX23
   → filter labelIds CONTAINS "AI Ingest"
   → readability/markdown extract → canonical URL strip → SHA-256 dedup
   → Hermes skill: ingest_email
       │  type: workflow
       │  execution: stateful   ← DeepVista schema
       │  --dry-run: yes
       └→ extract via Qwen3-8B-Instruct local:
           {title, tldr_3, entities, topics, models, tools,
            papers, urls, stance_vs_v3.x, novelty_0_1,
            action_required, time_to_act_days}
   → graphiti episode write
   → bi-temporal edges:
       (Email)-[MENTIONS]->(Tool|Model|Paper|Person)
       (Email)-[CONTRADICTS|SUPPORTS]->(StackChoice)
       (Tool)-[ALTERNATIVE_TO]->(Tool)
       (Sender)-[HIGH_SIGNAL_RATE]->(Topic)        ← новое v3.3
   → daily relevance-decay job:
       score = w1·exp(-age_days/90)
             + w2·sender_signal_rate
             + w3·topic_alignment_v3.x
             - w4·staleness_flag
   → weekly Hermes digest (понедельник 09:00, Telegram):
       "5 неинкорпорированных insights за неделю"
       "3 противоречия с v3.x для разрешения"
       "1 stale action 14+ дней: <link>"

```
**Sender-ranking** (новая идея v3.3): signal_rate = реальные действия / письма от sender'а. Сейчас Neo4j: 2/12 = 0.17, остальные 0/N. Фишка станет рабочей через 90 дней.
**Реализация в 3 фазы:**
1. **Phase I (4 часа):** разовый дамп текущих 211 писем → `~/life/Atlas/References/AI-Ingest/` PARA-структура с YAML-фронтматтером. Без графити.
2. **Phase II (1 weekend):** Cloudflare Worker + n8n + графити episodes для нового incoming потока. Старые 211 — пакетно через тот же conveyer.
3. **Phase III (1 weekend):** Hermes weekly-digest skill в Telegram.
---
## 12. Editor stack
| Editor | Роль | Source of truth |
| --- | --- | --- |
| **Zed** | primary IDE; Apache 2.0 GPUI; Win11 DirectX 11 backend (apr 2026); BYOK Anthropic + Ollama OpenAI-compat; parallel agents (apr 22 2026) | — |
| **VSCodium + Cline + Continue.dev** | fallback для niche extensions | — |
| **Claude Code CLI в PowerShell** | always-available, через API pay-as-you-go | существующая установка |
| **Aider** | CLI/git workflows | LiteLLM |
**Запрещено:** Trae IDE (ByteDance telemetry), Antigravity as primary (sovereignty-failing — Loop 4 P-validation), Cursor (proprietary context routing).
**Antigravity (Google):** активирован 8 мар 2026. **Решение:** валидировать в течение недели, есть ли что ради чего держать параллельно с Zed; если нет — официально deprecate.
---
## 13. SecOps — Sovereign Shield (новое, deployed May 2026)
**Статус:** Active on Hetzner CX23. Zero-tolerance policy. Immediate automated retaliation.

### 13.1 Threat model (AI-native kill chain)
Источник: `C:\telo\secops` deployment + `Snapshot.jpg` (Loop 4 SecOps synthesis).
| Stage | Attacker Goal | ENERV Countermeasure | Tool |
| --- | --- | --- | --- |
| **Reconnaissance** | Map attack surface | Detect + block at edge | CrowdSec + Cloudflare Bouncer |
| **Initial Access** | Phishing, stolen creds | Brute-force + anomaly detection | Wazuh Active Response + Fail2Ban |
| **Execution** | Malware, prompt injection | Kernel-level syscall monitoring | Falco (eBPF) + custom AI rules |
| **Persistence** | Tamper with vault/memory | File Integrity Monitoring (FIM) | Wazuh FIM + AIDE baseline |
| **Privilege Escalation** | Gain root | EDR + endpoint visibility | Wazuh Agent + Velociraptor (ready) |
| **Lateral Movement** | Spread across nodes | Network segmentation + container quarantine | Docker network isolation + retaliation script |
| **Data Exfiltration** | Steal vault/Qdrant index | Egress monitoring + immediate block | Wazuh + CrowdSec deny-list |

### 13.2 AI-specific attack vectors
Из `Snapshot.jpg` — 4 вектора injection в agent-контекст:
1. **Direct Prompt Injection** → Input validation guardrail (DeepVista `dry_run_gate` skill)
2. **Indirect Prompt Injection** → Strict API/webpage allow-lists; sanitize before Context
3. **Memory Injection** → FIM on `~/life/` (Obsidian) + Qdrant; Wazuh alert on unauthorized write
4. **Plan Injection** → `--dry-run` mandatory for all stateful skills; architect review gate

### 13.3 Deployed stack (Hetzner CX23)
**CrowdSec** (`enerv_crowdsec`) — parses `/var/log`, shares threat intel, auto-blocks via Cloudflare API.
- Collections: linux, sshd, nginx, iptables
- Bouncer: Cloudflare edge blocklist (CF_API_TOKEN required)

**Falco** (`enerv_falco`) — eBPF kernel monitor + `enerv_falcosidekick` router.
- Custom rule: Prompt Injection Detection (monitors n8n/Qdrant logs for "ignore previous instructions" / "system prompt")
- Custom rule: Vault Tampering Alert (unauthorized write to `/root/SOVRN/obsidian` outside Syncthing)
- Output: Telegram + n8n webhook → `retaliation_protocol.sh`

**Wazuh** (single-node, port 443) — SIEM + FIM + Active Response.
- Indexer + Server + Dashboard on `91.99.62.63`
- Admin: `admin` / `AgJ5*rkT1i1kRQTd12t4l97?KFDj8RNH` (rotate after first login)
- Agents: Hetzner host (active), Windows WSL2/Mac Mini (pending)

**Retaliation Protocol** (`/root/SOVRN/secops/retaliation/retaliation_protocol.sh`)
- Trigger: CRITICAL Falco/Wazuh alert
- Actions: (1) Stop compromised container, (2) Ban attacker IP in CrowdSec (720h), (3) Telegram alert
- Orchestrator: n8n webhook or direct SSH execution

### 13.4 .env required (fill before full activation)
```bash
# C:\telo\secops\.env → push to /root/SOVRN/secops/.env
CF_API_TOKEN=your_cloudflare_token
CS_LAPI_KEY=generate_via_cscli
N8N_WEBHOOK_URL=http://n8n.synergify.com/webhook/retaliation-engine
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

### 13.5 Integration into stack diagram
```
Human (Architect) → Hermes Agent → SecOps Shield
                                    ↓
                    [CrowdSec] ← [Falco] ← [Wazuh]
                       ↓            ↓          ↓
                  CF Edge      eBPF Kernel   SIEM/FIM
                       ↓            ↓          ↓
                    Block IP   Kill Container  Alert
```
**Rule:** No stateful skill executes without `dry_run_gate` validation + `--dry-run` confirmation when SecOps alert level > 1.

---
## 14. Hosting fabric
**Edge ($0/mo):**
- Cloudflare Pages (unlimited bandwidth, 500 builds/mo)
- Workers (100K req/day)
- R2 (10GB + zero egress)
- D1 (5GB + 5M rows read/day)
- Cloudflare DNS как authority для всех доменов
**Compute (€3.79/mo):**
- Hetzner CX23 (2 vCPU / 4GB / 40GB)
- Dokploy as PaaS (~350MB RAM idle)
- Docker: n8n + Karakeep + ArchiveBox + Postiz + Langfuse + FalkorDB + Qdrant + LearnDash WordPress
| Mail ($5/mo) |
- Fastmail Standard для branded email
- Альтернатива: Migadu Mini ($1.58/mo)
**Static affiliate sites:** Astro 5 + Pagefind + MDX → Cloudflare Pages.
**WordPress (когда client demands):** на той же Hetzner CX23, фронтированный Cloudflare proxy.
**GCP $300 free credit:** активировать на день 1 конкретного эксперимента (Vertex AI fine-tune или Neo4j AuraDB managed для priority-#6), бюджет-алёрт $250, walk away день 90.
**Никогда:** Surface Laptop как production server.
---
## 15. Voice — Handy primary (P-validation Loop 4)
**Установка:** `winget install cjpais.Handy` — fully offline, Whisper + Parakeet, system tray, push-to-talk.
**Layer 2 для LLM-cleanup:** Whispering (Tauri 2 + Svelte 5, ~22MB, custom prompts).
**Wispr Flow:** держать 2-недельный параллельный тест (письма Wispr 20 мар 2026 показывают, что вы продолжаете следить). Если Handy покрывает ≥80% UX (app-aware formatting — единственный реальный gap) — cancel Wispr ($144/yr saved).
---
## 16. Design
| Tool | Роль | Статус |
| --- | --- | --- |
| **Claude Design** | primary ideation, шипнут 17 апр 2026 | research preview, bugs flagged |
| **Pencil.dev (Code on Canvas)** | secondary, hybrid design+code with agents | watch — re-evaluate после GA |
| **Local FLUX-Q4 GGUF in ComfyUI** | book covers, marketing assets | RTX 4060 (~6–7GB VRAM с LoRA) |
| **Affinity Publisher** ($70 one-time) или **Scribus** | KDP composition | для priority-#3 |
| **Marp** | LLM-friendly slides, version-controlled | keep |
**Запрещено:** Stitch (Google) — sovereignty-hostile, watermarking. Pencil.dev v2 — superseded Code on Canvas (P6).
---
## 17. Tooling для проектных приоритетов
### Priority #1 — Local knowledge graph (foundation)
- **Phase 0 (Felix/ACE):** Obsidian vault, daily.md, Atlas/Workflows/ — разверните за 30 минут до всего остального
- **Phase 1 (graphiti slow path):** FalkorDB + Qdrant + BGE-M3 + Qwen3-8B + graphiti MCP v1.0 — только когда PARA упрётся
- **Web intake:** Karakeep (AGPL-3.0, AI tagging via Ollama) + ArchiveBox + SingleFile + MarkDownload
- **Evernote:** export → Joplin → Markdown → `~/life/Atlas/Archives/evernote/`, cancel renewal
### Priority #2 — Affiliate websites + AI agency
- **Sites:** Astro on Cloudflare Pages
- **WP когда client demands:** Hetzner CX23 + Dokploy + Docker WP
- **Agency-плейбуки:** n8n self-hosted (primary), Activepieces (license-allergic clients)
- **Web scraping (новое v3.3, P11):** Apify free tier, либо self-hosted `apify/crawlee` с Playwright/Puppeteer на той же Hetzner CX23.
### Priority #3 — Digital goods (books, courses)
- **Manuscript:** Quarto primary, Typst для technical books, Sigil для ePub QA
- **Covers:** local FLUX-Q4 GGUF in ComfyUI + Affinity Publisher / Scribus
- **Course platform:** LearnDash on Hetzner-hosted WP (0% platform fee)
- **TTS:** Kokoro 82M (Apache 2.0, top of HF TTS Arena) для default; Chatterbox-Turbo (MIT) для personal-voice clone
- **Substack-канал** как воронка (Loop 4, P12 опционально): weekly summary-newsletter из AI Ingest корпуса
### Priority #4 — Android apps + Telegram bots
- **App stack:** Kotlin Multiplatform + Compose Multiplatform
- **TG bots:** aiogram 3.x (Python) или grammY (TS, для Cloudflare Workers)
- **Hosting tier 1:** Cloudflare Workers + grammY + Workers KV
- **Hosting tier 2:** Hetzner CX23 + Caddy + aiogram + systemd + SQLite
- **Monetization:** Telegram Stars (XTR) с `bohd4nx/stars-payment` template
- **Dead options:** Pyrogram (abandoned), Fly.io free tier (closed Oct 2024)
### Priority #5 — YouTube + social automation
- **NotebookLM становится formal частью pipeline (новое v3.3, P7):** Hermes skill `publish.podcast` принимает doc/url, возвращает MP3 через Drive
- **Podcast tier:** NotebookLM → Spotify/Apple
- **YouTube:** authored show с cloned voice (Chatterbox-Turbo), 1–3 uploads/week, FFmpeg + local SDXL stills + Ken Burns pans
- **Не делать:** faceless AI factory (YouTube "inauthentic content" enforcement, янв 2026 wave демонетизировал 16 каналов / $10M ARR)
- **Social posting:** Postiz self-hosted (AGPL-3.0) на той же Hetzner CX23; n8n для custom
### Priority #6 — Game design + DeFi/blockchain
- **Game engine:** Godot 4.x + GDScript (MIT, zero royalties, mobile export from Win11)
- **AI gamedev:** Llama 3.3 8B Q4 для NPC dialog + SDXL/FLUX-Schnell для 2D + Tripo/Meshy free tier для 3D
- **Smart contracts:** Foundry only (Solidity, Base/Optimism EVM)
- **Keep-warm минимум:** ERC-20 deploy to Base Sepolia (8 ч), ERC-4337 paymaster sponsorship (12 ч)
- **Опционально:** Neo4j AuraDB managed для transaction graph (Loop 4 уточнение — вы подписаны на Neo4j-вебинары, fraud-webinar пересылали в Evernote)
### Priority #7 — Native Windows apps
- **Stack:** Tauri 2 + Rust (как у Handy / Whispering)
- **Local STT:** faster-whisper (CTranslate2, MIT) или Parakeet-TDT-v3 (NVIDIA, CC-BY-4.0)
- **Wispr clone PoC после Handy validation phase**
---
## 18. Tool matrix — финальная
| Tool | Verdict | Replace with |
| --- | --- | --- |
| Anthropic SDK | KEEP (за LiteLLM) | — |
| Antigravity (Google) | DEPRECATE (1-week validation, потом убрать) | Zed + Cline |
| NotebookLM | **ACTIVATE — pipeline** (P7) | — |
| Obsidian | **ACTIVATE — primary** | — |
| Claude Code CLI | KEEP, pay-as-you-go API | — |
| Claude Desktop | KEEP narrowly (MCP testing) | — |
| Claude Dispatch | DEPRECATE | OSS Telegram-relay (Felix Lee tutorial) |
| Claude Hooks | FIX → OpenLLMetry SDK | — |
| Superpowers plugin | KEEP | — |
| **Compound Engineering plugin** | **NEW v3.3 (P2)** | — |
| CrewAI | DEPRECATE для new code | Pydantic AI primary, LangGraph для DAG |
| Ollama | KEEP (через `ollama launch hermes`) | — |
| **HuggingFace** | **ACTIVATED** — HF Serverless 5th fallback (`router.huggingface.co/v1`) + `models.yaml` GGUF registry | — |
| OpenRouter | ACTIVATE | — |
| Microsoft Copilot | DEPRECATE | — |
| Evernote | EXPORT & DEPRECATE | Karakeep + SingleFile + ArchiveBox |
| Notion | MIGRATE | Obsidian + Dataview/Bases |
| Nimbalyst | KEEP narrowly | — |
| Zed | **ACTIVATE — primary** | — |
| VS Code | REPLACE | VSCodium + Cline + Continue.dev |
| Visual Studio | KEEP только если C++/.NET | uninstall иначе |
| Marp | KEEP | — |
| GitHub | KEEP + mirror critical в Codeberg | — |
| Git Bash, Python, Conda | KEEP | — |
| CMake, MSYS2 | KEEP только если C/C++ | — |
| Google Cloud SDK | DEPRECATE после $300 burn | — |
| Google AI Studio | DEPRECATE | OpenRouter / Gemini CLI |
| Wispr Flow | **PARALLEL TEST 2 weeks** (Loop 4 contradiction) | Handy + Whispering |
| Telegram | KEEP — primary control plane | — |
| Stitch (Google) | DEPRECATE | Claude Design / Paper.design |
| Paper.design | KEEP try | — |
| **Pencil.dev** | **WATCH** (Code on Canvas, P6) | — |
| Claude Design | ACTIVATE — research preview | — |
| **Apify (или Crawlee local)** | **NEW v3.3 (P11)** | — |
| **Neo4j AuraDB managed** | **NEW v3.3** (только для priority-#6) | — |
| FalkorDB local | ACTIVATE для graphiti | — |
| Hermes Agent | ACTIVATE — `ollama launch hermes` (P1) | — |
| Aider, Cline | ACTIVATE | — |
| LiteLLM | ACTIVATE с explicit `fallbacks:` | — |
| graphiti MCP v1.0 | ACTIVATE Phase 1 | — |
| Karakeep, ArchiveBox, n8n, Postiz | ACTIVATE on Hetzner | — |
| Handy (Tauri 2) | ACTIVATE primary voice | — |
| Substack channel | OPTIONAL (P12) | — |
---
## 19. Phased rollout (revised v3.3)
### Phase 0 — Stabilize foundations (Week 1, ~$0)
```javascript
# Ollama 0.21+ с Hermes (P1)
ollama launch hermes

# llama.cpp from CUDA 13.1 release (P-fix)
# download Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf

# Compound Engineering plugin (P2)
# install via Claude Code marketplace

# DeepVista skill schema (P3)
# add type/execution YAML to all existing SKILL.md

# Felix/ACE fast path (P4) — критичный shortcut
# create ~/life/{Efforts,Calendar,Atlas}/

# Ramp PM skill (P5)
# install architect.md

```
Дополнительно: Zed primary editor, OpenLLMetry SDK + Langfuse via Docker, fix/rip Claude Code hooks, Cloudflare DNS для всех доменов, cancel pending Wispr Flow renewal до Phase 4 evaluation.
### Phase 1 — Sovereign cloud + ingest pipeline (Weeks 2–3, ~$0–$10)
- Sign up Cerebras + Groq + NIM dev tier
- LiteLLM proxy с rotating pool + explicit `fallbacks:` (P-fix Loop 3)
- **Phase I ingest (Loop 4): дамп 211 писем → ****`~/life/Atlas/References/AI-Ingest/`**** PARA**
- Установка `ingest_email` skill через Hermes (DeepVista schema, --dry-run)
- LangGraph Postgres checkpointer для DAG workflows
### Phase 2 — Migrate data + host (Weeks 4–6, ~$5–10/mo)
- Notion → Obsidian (1 weekend, Claude Code cleanup pass)
- Evernote ENEX → Joplin → Markdown → `~/life/Atlas/Archives/evernote/`, cancel
- Hetzner CX23 + Dokploy provisioning
- Fastmail migration; 
- Karakeep + ArchiveBox + n8n + Postiz on Hetzner
- First Astro affiliate site on Cloudflare Pages
- **Phase II ingest (Loop 4): Cloudflare Worker + n8n + graphiti episodes**
- **Если PARA упёрся (1–2 weeks)** → запуск Phase 1 graphiti slow path
### Phase 3 — Revenue layer (Weeks 7–10, $9–10/mo)
- 2–3 Astro affiliate sites
- LearnDash WP setup на Hetzner если course planned
- First TG bot (aiogram + Cloudflare Workers или Hetzner)
- **Apify / Crawlee для lead-gen** (P11)
- GCP $300 credit на конкретный Vertex AI experiment, $250 budget alert, walk away day 90
- Grafana ops + Streamlit analyst, общий Postgres + Prometheus + Langfuse
- **Phase III ingest (Loop 4): Hermes weekly-digest в Telegram (понедельник 09:00)**
### Phase 4 — Future-proof + content (Weeks 11–14+, +$0–30/mo)
- KMP + CMP Android PoC
- Foundry + ERC-4337 keep-warm (8–12 ч)
- Godot 4.x toy project в spare cycles
- **Authored YouTube/podcast show** через Chatterbox-Turbo cloned voice (1–3/week)
- Wispr vs Handy 2-week parallel test → cancel loser (savings)
- **Substack channel запуск** (P12 опционально) — weekly digest как воронка для priority-#3
- Re-evaluate Claude Code Max только если измеренное использование >50M tok/мес
---
## 20. Budget tiers
### $0/mo PoC (existing subscriptions only)
- Local llama.cpp + Qwen3-Coder-30B-A3B + 9B + 8B
- Free pool: Cerebras + Groq + NIM + OpenRouter free + Cloudflare Workers AI + GitHub Models + Gemini CLI
- Cloudflare Pages/Workers/R2/D1
- Hermes + Aider + Cline + Compound Engineering + Claude Code Pro + Zed
- graphiti + Qdrant + FalkorDB + OpenLLMetry + Langfuse + Grafana + Streamlit (Docker Desktop)
- Karakeep + ArchiveBox + n8n + Postiz (Surface Laptop dev → Hetzner после Phase 2)
**Capability:** ~80% frontier-tier coding, full personal-KG, full agency stack для client demos.
### $20/mo (Claude Pro current state)
- Всё из $0
- Claude Pro для premium agentic + Claude Design preview
- **Caveat:** Claude Code on Pro removed 21 apr 2026 для new subscribers; existing users могут retain temporarily
### $30–60/mo (sovereignty-aligned recommended)
- Fastmail $5
- Hetzner CX23 €3.79
- OpenRouter $10 deposit (1K RPD, 29 free models)
- Anthropic API pay-as-you-go ~$15–40 через Aider/Cline (variable)
- (Опционально) Cursor Pro $20 если IDE worth it
**Capability:** более чем покрывает Claude Code Max, всё variable, walk-away anytime.
### $100/mo (Claude Code Max — НЕ рекомендуется по умолчанию)
**Только если** измеренное использование >50M frontier tokens/mo и cache-read economics dominate. Иначе deepens lock-in.
---
## 21. Open questions для Loop 5
1. **PARA → graphiti tipping point.** Какой количественный сигнал говорит «PARA упёрся, пора графити»? Гипотеза: >3 multi-hop queries/неделя где Markdown grep не справляется.
2. **Sender-ranking weights.** w1..w4 в relevance-decay job — теоретические; пересмотреть после 90 дней работы pipeline.
3. **CUDA 13.3+ status.** Если Anthropic / NVIDIA выпустят патч — переоценка safe versions.
4. **Pencil.dev Code on Canvas GA.** Re-evaluate как possible primary design tool.
5. **DeepVista CLI.** `github.com/DeepVista-AI/deepvista-cli` стоит попробовать — может дать готовые skills с правильной семантикой.
6. **Babbage early-access** (DeepVista) — активировать invite от 8 дек 2025.
7. **Anthropic ****`task_budget`**** beta.** Пока no community confirmation для long-running agentic loops.
8. **`facebookresearch/HyperAgents`**** re-license watch.** 6-month watch period (Loop 3).
9. **AntiGravity 1-week validation** — оставить или deprecate.
10. **Wispr Flow vs Handy 2-week parallel test** — итоговое решение в Phase 4.
---
## 22. Anthropic-bias accounting (final)
Loop 2 выявил три точки концентрированного байаса; в v3.3 каждая закрыта:
| Bias | v3.0/v3.1 | v3.3 закрытие |
| --- | --- | --- |
| Claude Code Max default | $100/mo recommended | API pay-as-you-go via Aider, walk-away anytime |
| Claude Dispatch desirable | activated | OSS Telegram-relay (Felix Lee tutorial) |
| Claude Design as primary | claimed primary | research preview ack, ideation only, FLUX/Pencil.dev secondary |
Архитектурный принцип после v3.3: **vendor-neutral substrate first** (LiteLLM + OpenLLMetry + MCP + local llama.cpp + graphiti), **best provider per task second**. Anthropic — commodity provider в пуле, не центр стека.
---
## 23. Source-of-truth lineage
- **Loop 1 (v3.0):** original architecture proposal
- **Loop 2 (v3.1):** sovereignty stress-test, 7H/7P/6F verdicts
- **Loop 3 (v3.2):** 5 hardware/integration patches (`--n-cpu-moe`, CUDA 13.1, FalkorDB, LiteLLM `fallbacks:`, `effort` parameter); HyperAgent track A–D analysis
- **Loop 4 (v3.3, this doc):** 12 P-patches from Gmail "AI Ingest" 211-message corpus mining
**Будущее:** Loop 5 — после 90 дней работы pipeline ingest, переоценка PARA→graphiti tipping point + sender-rank weights.
---
> *Печатать и хранить рядом с клавиатурой. Любой слой выше заменяется без перестройки соседних. Каждое v3.x — это checkpoint, а не финальная форма.*
Скажите, нужно ли:
1. Сохранить как `.docx` для папки проекта (могу сделать через docx skill в следующем тёрне)?
2. Добавить отдельный appendix с конкретными config-файлами (LiteLLM YAML, llama-server systemd unit, n8n workflow JSON)?
3. Отдельный одностраничный «Quick Reference Card» для печати?