# HuggingFace Integration — SOVRN v3.3

**Date:** 2026-05-08
**Status:** approved
**Scope:** A (Hub/registry) + B (Free Serverless Inference in LiteLLM)
**Out of scope:** Fine-tuning pipeline (C), HF Spaces (D) — separate sprints

---

## Overview

Two new layers added to SOVRN without changing existing stack:

1. **Registry layer** — `huggingface_hub` CLI as single source for GGUF model downloads, pinned by commit hash via `~/.hermes/models.yaml`
2. **Inference layer** — HF Serverless Inference API as 5th fallback in LiteLLM (after Cerebras → Groq → NIM → OpenRouter)

```
MODEL GATEWAY — LiteLLM
  local:  llama.cpp → Qwen3-Coder-30B-A3B
  cloud:  Cerebras → Groq → NIM → OpenRouter → HF Serverless  ← new
                                                      ↑
                                          huggingface_hub CLI
                                          (model registry, pin by hash)
                                                      ↑
                                          HF_TOKEN (single, propagated everywhere)
```

---

## Section 1: HF_TOKEN Propagation

Single read-only token from `hf.co/settings/tokens`. Propagated to three locations:

| Location | Method |
|---|---|
| WSL `~/.bashrc` | `export HF_TOKEN=...` |
| Hermes `~/.hermes/.env` | `HF_TOKEN=...` (entry already exists, fill value) |
| Windows env | `$env:HF_TOKEN` in PowerShell profile or system env |

`hf-transfer` already installed (pulled by tinker-atropos). Enable via:

```bash
export HF_HUB_ENABLE_HF_TRANSFER=1   # added to ~/.bashrc
```

---

## Section 2: Model Registry — models.yaml

File: `~/.hermes/models.yaml`

```yaml
models:
  - name: Qwen3-Coder-30B-A3B
    repo: unsloth/Qwen3-Coder-30B-A3B-GGUF
    revision: abc123def        # commit hash — never "main"
    file: Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf
    path: /mnt/c/Users/sasha/models/
```

Download command:
```bash
huggingface-cli download <repo> <file> \
  --revision <hash> \
  --local-dir <path>
```

**Pin discipline:** revision is always a full commit hash. Updating to a new version = explicit `hf pin` command that rewrites the hash in manifest. No silent drift.

---

## Section 3: LiteLLM — HF as 5th Fallback

Add to `litellm-config.yaml`:

```yaml
model_list:
  # ... existing models unchanged ...

  - model_name: hf-hermes-70b
    litellm_params:
      model: huggingface/NousResearch/Hermes-3-Llama-3.1-70B
      api_key: os.environ/HF_TOKEN
      api_base: https://api-inference.huggingface.co/v1

  - model_name: hf-qwen-72b
    litellm_params:
      model: huggingface/Qwen/Qwen2.5-72B-Instruct
      api_key: os.environ/HF_TOKEN
      api_base: https://api-inference.huggingface.co/v1

router_settings:
  fallbacks:
    - cerebras-model: [groq-model, nim-model, openrouter-model, hf-hermes-70b]
```

**Model rationale:**
- `Hermes-3-Llama-3.1-70B` — Nous Research (same authors as Hermes Agent), strong instruction-following
- `Qwen2.5-72B-Instruct` — consistent output style with local Qwen3, familiar to the stack

**Cold start:** 5–30s on first request — acceptable for fallback position, not primary.

---

## Section 4: Hermes Skill — hf-models

File: `~/.hermes/skills/hf-models/SKILL.md`

```yaml
---
name: HF Model Manager
type: tool
execution: stateful
description: Download, pin, and verify GGUF models from HuggingFace Hub.

## Side Effects
- Writes to ~/.hermes/models.yaml
- Downloads files to /mnt/c/Users/sasha/models/

## Commands
- hf status   → show models.yaml, current hashes, disk usage
- hf check    → compare local hashes with latest on Hub
- hf download <model-name>  → download via manifest with progress
- hf pin <model-name> <hash>  → update revision in models.yaml
---
```

Implementation: shell wrapper around `huggingface-cli`. No custom Python. Stateful because it writes to `models.yaml` and disk.

---

## Implementation Order

1. Create HF token (read-only)
2. Propagate `HF_TOKEN` to all three locations
3. Add `HF_HUB_ENABLE_HF_TRANSFER=1` to `~/.bashrc`
4. Create `~/.hermes/models.yaml` with current model pinned to its commit hash
5. Add two HF models to `litellm-config.yaml` as 5th fallback
6. Restart LiteLLM, verify fallback chain
7. Create `~/.hermes/skills/hf-models/SKILL.md`
8. Test all four Telegram commands

---

## What Does Not Change

- llama.cpp launch parameters
- Cerebras → Groq → NIM → OpenRouter fallback order
- Hermes orchestration and gateway
- Cloudflare / Hetzner hosting
- All existing LiteLLM model entries
