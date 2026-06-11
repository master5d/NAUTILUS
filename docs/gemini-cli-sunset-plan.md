# Gemini CLI sunset — migration plan

> **Deadline:** 2026-06-18 · **Author:** audit follow-up 2026-06-11 · **Status:** actioned (orchestrator) + recommendations (API path)

## What is actually ending

Google sunsets the **Gemini CLI free tier** (OAuth via personal Google account,
~60 RPM / ~1000 RPD) on **2026-06-18**. Free/Pro/Ultra Code-Assist users are
pushed to **Antigravity CLI** (closed-source, Go) whose free tier is ~20 req/day.

**Two distinct Gemini dependencies in NAUTILUS — only one is hit:**

| Dependency | Channel | Hit 06-18? | Action |
| --- | --- | --- | --- |
| `gemini` orchestrator agent (`gemini -p`) | CLI OAuth free tier | **YES — dies** | **Removed from orchestrator** (this change) |
| Hermes brain `google/gemini-3-flash-preview` | `GEMINI_API_KEY` via LiteLLM | No (Flash API survives) | Keep; already has fallback chain |
| knowledge-graph embeddings + `gemini-2.5-flash-lite` | `GEMINI_API_KEY` (`@ai-sdk/google`) | No | De-risk later (see below) |
| n8n ingest workflow | `google/gemini-3-flash-preview` via LiteLLM | No | No change |

The paid/API-key path to Gemini is explicitly unaffected — Google's statement
keeps API-key access "uninterrupted." A separate April-2026 change made only
**Pro** models paid; **Flash** (what NAUTILUS uses) stays on the free tier with
tightened quota (already reflected: 15 RPM / 1500 RPD in `quotas.json`).

## Decision: drop the Gemini CLI orchestrator agent

Why remove rather than repoint:

1. **Antigravity CLI (official successor) doesn't fit the orchestrator
   contract** — verified `agy.exe` v1.0.7 2026-06-11: it *can* run headless
   (`-p`/`--print`, exit 0, model responds), but (a) the answer goes to a brain
   transcript jsonl (`~/.gemini/antigravity-cli/brain/<newest>/.system_generated/
   logs/transcript.jsonl`), **not stdout**, and (b) headless print does a single
   planner turn and **halts at an approval gate on multi-step/file-edit tasks**
   that `--dangerously-skip-permissions` does NOT override (it's model behavior).
   `swarm` agents (claude/codex/hermes) must execute autonomously and return on
   stdout — agy does neither. (Earlier "TTY-only" shorthand was imprecise; see
   `reference_headless_agent_clis`.)
2. **Gemini Flash is still reachable** — via Hermes, whose brain *is*
   `google/gemini-3-flash-preview` through the LiteLLM API key. Need Gemini's
   1M-context Flash for a task? `swarm -Agent hermes "…"`.
3. **No capability loss** — `claude` (default) / `codex` (gpt-5.5) / `hermes`
   (Gemini Flash API) fully cover orchestration. The standalone CLI slot was
   redundant once its free quota dies.

Orchestrator now: `claude` · `codex` · `hermes`.

## Hermes brain — keep Gemini Flash, lean on fallback

`litellm-config.yaml` already routes:

```
google/gemini-3-flash-preview → fast-pool → hf-llama-70b → local-fallback
```

So if the Gemini **API** free tier degrades, Hermes auto-falls to Cerebras
(`qwen-3-235b`, ~1000 TPS) then HF then local — no manual intervention. Keep
Gemini Flash as primary for now: its 1M context beats Cerebras free (8K cap)
and Groq for long-context ingest. **Trigger to flip primary → `fast-pool`:**
sustained 429s on Gemini in `labwatch` usage, or a further free-tier cut.

## knowledge-graph — embeddings already on stable (docs synced 2026-06-11)

The runtime code was **already** on stable models — only the docs lagged:

- `src/lib/embeddings.ts` uses **`gemini-embedding-001`** (stable GA, 768-dim
  via `outputDimensionality`), not the `-exp-*` preview. ✓
- `src/app/api/graphrag/route.ts` uses **`gemini-2.5-flash`** (stable), not a
  `-preview-*` snapshot. ✓
- Fixed stale `gemini-embedding-exp-03-07` / `flash-lite-preview` references in
  the KG `CLAUDE.md` + `README.md` so future agents don't regress to exp models
  (Google pulls `exp`/`preview` snapshots without notice; an embedding-model
  change forces a full graph re-embed — vector space differs).
- Remaining (real, future): Sprint 2 multimodal embeddings — **decided
  2026-06-11 to go sovereign with self-hosted `jina-embeddings-v4`** (not Gemini
  Embedding 2, which is now GA but deepens Google dependency). Removes the
  Google embedding dependency entirely. Full decision +
  constraints: `apps/knowledge-graph/SPRINT2_EMBEDDINGS_ADR.md`.

## Checklist

- [x] Remove `gemini` agent from `config/orchestrator.json`
- [x] README agent list trimmed Gemini → Claude/Codex/Hermes
- [x] Document Hermes fallback as the Gemini-Flash access path
- [x] KG embeddings already on stable `gemini-embedding-001`; synced stale docs
- [x] `.gitmodules` added for github-pages submodule (clone --recursive works)
- [ ] (watch) flip Hermes brain to `fast-pool` if Gemini API 429s spike in labwatch
- [ ] (optional) drop `C:\agents\Gemini` CLI install after 06-18 if unused
