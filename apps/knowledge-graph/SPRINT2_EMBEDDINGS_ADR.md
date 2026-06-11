# ADR: Sprint 2 multimodal embeddings — sovereign jina-embeddings-v4

> **Status:** Accepted 2026-06-11 · **Scope:** Sprint 2 (not yet started) · **Decision owner:** master5d

## Context

Sprint 1 ships text-only embeddings via **`gemini-embedding-001`** (stable GA,
768-dim, Google AI Studio API key). Sprint 2 wants multimodal embeddings
(images, visual documents, eventually audio/video) — notably for the **KRILYB**
pipeline whose payload is charts, tables, and scanned manual pages.

Two viable paths were weighed (June 2026):

| | Gemini Embedding 2 (GA) | **jina-embeddings-v4 (chosen)** |
| --- | --- | --- |
| Modalities | text/image/video/audio/PDF, one space | text + images + **visual documents** (charts/tables/scans) |
| Hosting | Google API (same key KG uses) | **Self-hosted** — GGUF on llama-server / HF transformers on M4 |
| Sovereignty | deepens Google dependency | **removes Google dependency** ✓ |
| Effort | minimal | higher (serving setup) |
| Cost | paid/quota'd | local compute only |

## Decision

**Adopt jina-embeddings-v4 as the Sprint 2 embedding model**, self-hosted.

Rationale:
1. **Sovereignty-first** (SOVERN core principle) — removes the Google
   dependency the gateway is otherwise trying to shed (see
   `docs/gemini-cli-sunset-plan.md`).
2. **Visual-document strength matches the actual use case** — v4 is purpose-built
   for charts/tables/scanned pages, i.e. exactly KRILYB ebook digitization.
3. **Runs on existing local floor** — GGUF quants (~3-4 GB) fit the M4 16GB
   Mac Mini / `llama-server` with room to spare; no new infra.

## Technical facts (verified 2026-06-11)

- **Model:** `jinaai/jina-embeddings-v4`, 3.8B params, Qwen2.5-VL-3B backbone.
- **Dims:** 2048 single-vector, Matryoshka-truncatable to **[128, 256, 512,
  1024, 2048]**. Current KG uses **768 — NOT on the list** → dimension change is
  unavoidable. **Target 1024** (quality/storage balance, closest above 768).
- **Multi-vector mode:** 128-dim/token (late interaction) — out of scope for the
  Neo4j single-vector index in MVP.
- **GGUF caveat:** published GGUF variants (`text-retrieval`, `text-code`,
  `text-matching`, ~3.09B) are **TEXT-ONLY**. **Image / visual-doc embedding
  needs the full HF model via transformers** (Qwen2.5-VL, MPS on the M4) — GGUF
  alone does not cover the multimodal goal yet.

## Hard constraints for whoever implements Sprint 2

1. **Unified space = one model, one backend for BOTH text and images.** An
   image-query only matches text-nodes if both were embedded by the same model.
   Do **not** mix gemini-text + jina-image. Also avoid mixing GGUF (quantized)
   and transformers (full-precision) for the shared space unless verified to
   produce compatible vectors — safest is one backend for everything.
2. **Full graph re-embed is required.** Dim 768 → 1024 means the Neo4j vector
   index must be dropped and recreated, and every existing node re-embedded.
   Plan a one-shot migration script + downtime window.
3. Keep `truncate_dim` pinned in code (1024) — accidental dim drift silently
   breaks the index.

## Open questions to resolve at Sprint 2 kickoff

- **Serving stack:** full jina-v4 via transformers+MPS on M4, vs MLX port, vs a
  thin embedding microservice the Next.js app calls (mirror current `embed()`
  contract). Benchmark image-embed throughput on the M4 before committing.
- **Audio/video:** v4 does not natively embed audio/video. Defer to a later
  layer — CLAP for audio, frame-sampling + image-embed for video — as a separate
  modality bridge, not part of the initial jina-v4 cutover.
- **Fallback:** if full jina-v4 is too heavy on the M4, fall back to
  `jina-clip-v2` (lighter, image+text only) — still sovereign, drops visual-doc
  quality.

## Consequences

- `src/lib/embeddings.ts` `embed()` contract stays (returns `number[]`), but
  swaps backend Google → local jina-v4 and dim 768 → 1024.
- `src/lib/neo4j.ts` vector index dim 768 → 1024; re-embed migration.
- `GOOGLE_GENERATIVE_AI_API_KEY` no longer needed for embeddings (GraphRAG LLM
  `gemini-2.5-flash` may still use it, or move to the LiteLLM gateway too).
- KG becomes fully offline-capable for embeddings — aligns with "Autonomy Under
  Failure."
