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

1. **Antigravity CLI (official successor) is TTY-only** — cannot run headless,
   so it can't be a `swarm`-dispatchable orchestrator agent (per
   `reference_headless_agent_clis`).
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

## knowledge-graph — latent embedding risk (separate sprint)

Independent of 06-18, but worth flagging:

- **`gemini-embedding-exp-03-07` is an experimental model** — Google retires
  `exp` models on short notice. Migrate to **stable `gemini-embedding-001`**
  (drop-in, same API key) before it's force-deprecated. Re-embedding the graph
  is required on any embedding-model change (vector dims/space differ).
- Sovereign fallback option: local embeddings via `llama-server` or Cloudflare
  Workers AI `bge-*` — removes the Google dependency entirely for the KG.
- This lives with the knowledge-graph app (Sprint 2+), not the gateway.

## Checklist

- [x] Remove `gemini` agent from `config/orchestrator.json`
- [x] README agent list already lists Claude/Codex/Hermes/Gemini → trim Gemini
- [x] Document Hermes fallback as the Gemini-Flash access path
- [ ] (KG team) migrate `gemini-embedding-exp-03-07` → `gemini-embedding-001`
- [ ] (watch) flip Hermes brain to `fast-pool` if Gemini API 429s spike in labwatch
- [ ] (optional) drop `C:\agents\Gemini` CLI install after 06-18 if unused
