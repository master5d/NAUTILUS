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

Use the  command to manage local GGUF models from HuggingFace Hub.

Examples:
- "hf status" — show registered models and their disk usage
- "hf check" — check if newer versions are available on HuggingFace Hub
- "hf download Qwen3-Coder-30B-A3B" — download the model per manifest
- "hf pin Qwen3-Coder-30B-A3B abc123def456..." — pin to a specific commit hash
