# SOVERN AI Lab — Budget & Capacity

> **As of:** 2026-06-10 · machine-readable source: `labwatch/quotas.json` · live view: `labwatch` (http://localhost:4002)
> Все цифры — verified free-tier лимиты на дату выше. Провайдеры режут квоты без предупреждения (Google, дек-2025) — пересверять при деградации.

## TL;DR — чем платим за разработку

| Слой | Ресурс | Дневная ёмкость | Роль |
|---|---|---|---|
| Оркестратор | Claude Code (подписка) | 5-час окно + 2 недельных капа (удвоены 2026-05-06) | Мозг: планирование, код, ревью |
| Второй пилот | Codex CLI (ChatGPT plan) | token-based, остаток `/status` | Параллельные задачи, second opinion |
| Cloud pool | Cerebras + Groq + NIM + OpenRouter + Gemini | ≈1.1M+ tok/day суммарно | Массовка: Hermes, hooks, n8n, batch |
| Local floor | llama-server Qwen3-Coder-30B-A3B :8080 | ∞ (железо) | Суверенный пол, fallback последней инстанции |

**Стоимость в деньгах: $0/мес** (подписки Claude/ChatGPT — sunk cost; $10 OpenRouter — разовый депозит за разблокировку 1000 RPD).

## Провайдеры (через LiteLLM gateway, порт динамический — см. `config/services.json`)

| Провайдер | RPM | RPD | TPM | TPD | Заметки |
|---|---|---|---|---|---|
| **Cerebras** | 30 | — | 60K | **1M** | Король free tier, ~1000 TPS; ctx порезан до 8192 |
| **Groq** | 30 | 1000 | 12K | **100K** | TPD — реальный потолок: ≈100 средних вызовов/день, не 1000 |
| **NVIDIA NIM** | 40 | — | — | — | Credits-based (1000 на signup, до 5000); без daily cap |
| **OpenRouter :free** | 20 | 1000 | — | — | 1000 RPD разблокировано депозитом $10 |
| **Google AI Studio** | 15 | 1500 | 1M | — | gemini-3-flash-preview; брейн Hermes |
| **HF Inference** | — | — | — | — | ~$0.10/мес кредитов — emergency only |
| **Local (llama-server)** | ∞ | ∞ | ∞ | ∞ | Безлимит, ограничен железом; always reachable (SOVRN §1) |

Free TPD-ёмкость с явными капами: **1.1M tok/день** (Cerebras 1M + Groq 100K). NIM/OpenRouter/Gemini добавляют сверху ёмкость, ограниченную RPM/RPD, а не токенами.

## Агенты

| Агент | Auth | Лимиты | Статус |
|---|---|---|---|
| Claude Code | подписка | 5h rolling + 2 weekly caps; численно — `/usage` в CLI. **Промо Fable 5:** бесплатно в подписке 2026-06-09 → 06-22, но считается ≈2× Opus против лимитов (не безлимит); с 06-23 — usage credits $10/$50 за Mtok | 👑 default-оркестратор |
| Codex CLI | ChatGPT plan | token-based (с 2026-04); остаток — `/status` | Запасной оркестратор |
| Hermes | LiteLLM gateway | квоты provider pool ↑ | Единственный агент с полным usage-трекингом в Labwatch |
| Gemini CLI | Google OAuth | 60 RPM / 1000 RPD | ⚠️ **FREE TIER УМИРАЕТ 2026-06-18** → Antigravity ~20 req/day (−98%) |
| Antigravity (agy) | Google | ~20 req/day | TTY-only, headless не оркестрируется |

## Политика расходования (для Claude-оркестратора)

1. **Дорогой интеллект — на архитектуру.** Claude/Codex токены тратим на планирование, ревью, сложный код. Не на bulk-операции.
2. **Массовку — в pool.** Суммаризация, классификация, draft-генерация → `fast-pool` через gateway (shuffle: Cerebras/Groq/NIM/OpenRouter).
3. **Groq беречь.** 100K TPD сгорает за ~100 вызовов — Groq хорош для коротких быстрых вызовов (hooks), не для длинных контекстов.
4. **Длинный контекст → Cerebras нельзя** (ctx 8192). Длинные промпты в pool пойдут на Groq/NIM/OpenRouter или провалятся в fallback.
5. **Reasoning** (`reasoning` model group) — Groq qwen3-32b, fallback на local.
6. **Локальный пол всегда жив.** llama-server :8080 — последний fallback каждой цепочки; если он лежит, чинить первым.
7. **Gemini CLI не делать оркестратором** — free tier отключают 2026-06-18.
8. **Окно Fable 5 (до 2026-06-22) тратить умно.** Fable 5 жжёт подписку ≈2× быстрее Opus — гонять его на задачах, где мощность реально нужна (архитектура, сложный рефакторинг), а не на рутине; weekly caps никто не отменял. После 06-22 — обратно на Opus 4.8 как рабочую лошадь.

## Мониторинг

- **Dashboard:** `labwatch` в PowerShell (поднимает сервер + открывает http://localhost:4002)
- **Переключение оркестратора:** кнопки на дашборде или `swarm -Switch codex`
- **Диспатч задачи:** `swarm "задача"` → активный агент headless
- **Сырые данные:** `labwatch/usage.db` (SQLite), пишется callback'ом `config/usage_logger.py`
- **Подписочные агенты** не выгружают usage численно: Claude → `/usage`, Codex → `/status`

## Атрибуция трафика

Запрос через gateway атрибутируется агенту по (в порядке приоритета): заголовок `x-sovern-agent` → Bearer-ключ (`sk-claude`, `sk-codex`, `sk-hermes`, `sk-gemini`, `sk-antigravity`, `sk-n8n`, `sk-hooks`) → `user` поле → `unattributed`.
