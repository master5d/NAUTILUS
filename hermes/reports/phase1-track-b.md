# Phase 1 Track B — Docker MCP Toolkit Setup Report
**Date:** 2026-04-28 | **Status:** ✅ Partial — GitHub MCP done, Langfuse MCP skipped

---

## What Was Done

### Docker MCP Toolkit CLI
- **Version:** v0.40.4 (already installed with Docker Desktop 29.4.1)
- **Profile created:** `agentic_ai` with `github-official` server
- **Note:** Docker Desktop secrets API (keychain) is inaccessible from WSL/PowerShell CLI — requires GUI pipe (`dockerBackendApiServer`). Workaround: env file.

### GitHub MCP Server ✅
- **Image:** `ghcr.io/github/github-mcp-server` (official, v1.0.3)
- **Method:** stdio via Docker container, wrapper script at `/root/.hermes/bin/github-mcp.sh`
- **Tools:** 41 tools enabled in Hermes
- **Auth:** `GITHUB_TOKEN` from `~/.hermes/.env` → `GITHUB_PERSONAL_ACCESS_TOKEN` in container
- **Config:** saved to `~/.hermes/config.yaml`

**Wrapper script** (`/root/.hermes/bin/github-mcp.sh`):
```bash
#!/bin/bash
TOKEN=$(grep ^GITHUB_TOKEN /root/.hermes/.env | cut -d= -f2)
(sleep 0.5; cat) | docker run --rm -i -e GITHUB_PERSONAL_ACCESS_TOKEN="$TOKEN" ghcr.io/github/github-mcp-server
```

### Langfuse MCP Server ⚪ Skipped
- No official Docker image exists for Langfuse MCP
- Community image `shreyammaity/langfuse-mcp` is arm64 (wrong architecture for x86_64)
- Langfuse observability works directly via SDK callbacks in LiteLLM — MCP wrapper not needed for Phase 1

---

## Docker MCP Profile (Windows PowerShell)

Profile `agentic_ai` available for Claude Desktop and other MCP clients:
```powershell
# Test profile (dry-run)
docker mcp gateway run --profile agentic_ai --transport sse --port 3001 --dry-run

# Run live (loads 41 GitHub tools)
# Note: requires Docker Desktop secrets GUI to set github.personal_access_token
# OR set env var: $env:GITHUB_PERSONAL_ACCESS_TOKEN = (gh auth token)
```

---

## Currently Running Containers

| Container | Image | Port | Status |
|-----------|-------|------|--------|
| langfuse | langfuse/langfuse:2 | 3000 | ✅ Up 6h |
| langfuse-db | postgres:16-alpine | 5432 (internal) | ✅ Up 6h |
| github-mcp (on-demand) | ghcr.io/github/github-mcp-server | stdio only | ✅ Starts per request |

---

## Hermes MCP Status

```bash
hermes mcp list  # shows: github (41 tools)
```

GitHub tools available to Hermes:
- `get_me`, `search_repositories`, `list_issues`, `create_pull_request`
- `push_files`, `get_file_contents`, `search_code`, `list_commits`
- ... 41 tools total

---

## Port Map (no conflicts)

| Port | Service |
|------|---------|
| 3000 | Langfuse UI |
| 3001 | Docker MCP Gateway (when running) |
| 4000 | LiteLLM proxy |
| 8080 | llama-server (Qwen3-Coder) |

---

## Next Steps

1. **Test GitHub MCP in Hermes:** `hermes chat -q "Use GitHub MCP to get my profile (get_me)"`
2. **Langfuse MCP:** Monitor for official image release at github.com/langfuse/langfuse
3. **Docker Desktop secret:** Open Docker Desktop GUI → Settings → Dev Environments → Secrets → add `github.personal_access_token` for profile-based gateway
