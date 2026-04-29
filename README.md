# Agentic AI Project

This repository contains the setup for an autonomous AI development environment leveraging **Hermes Agent**, **LiteLLM**, and a **LLaMA server**. The core components currently running are:

- **LiteLLM proxy** (`litellm-config.yaml`) on port **4000** with rotating keys (Cerebras, Groq, NIM, OpenRouter) and a local fallback.
- **LLaMA server** (`Qwen3-Coder-30B-A3B`) on port **8080** (launched via `launch-llama-server.ps1`).
- **Gateway** (Telegram) already connected (PID 3121).
- **Reasoning level** set to `medium` in `config.yaml`.
- API keys for OpenRouter and GitHub are stored in `~/.hermes/.env`.

## What’s Included

- **Configuration files** (`config/`, `docker/`, `scripts/`).
- **Documentation** (`docs/`, `hermes/`).
- **Utility scripts** for launching services and setting up keys.

## Next Steps (To‑Do)

1. **README** – this file.
2. **Git initialization** – create a repository for version control.
3. **Weekly digest cron** – schedule a job that runs weekly to collect health‑check info or other metrics.

Feel free to extend the documentation, add more scripts, or adjust the cron job as needed.
