# Claude Code Plugins — SecOps Inventory

**Snapshot:** 2026-06-06 · **Scope:** Windows 11 Claude Code harness (`~/.claude/settings.json` → `enabledPlugins`)

Point-in-time inventory of installed plugins from a security lens. Plugins are
trust-extending: an MCP-backed one opens an **outbound network + token surface**;
a hook-registering one **executes code inside the agent loop** on tool use or
session events. This doc tracks what's enabled, why, and what was deliberately removed.

## Security dimensions
- **MCP** — runs a server, talks to an external API → egress + usually an auth token.
- **Hooks** — registers `SessionStart` / `PostToolUse` / `UserPromptSubmit` commands that run automatically.
- **Auth** — holds a credential (token/OAuth). Note *where* it lives (settings.json env = leak-prone; dedicated config file = safer).

## Enabled (25, as of 2026-06-06)

| Plugin | MCP | Hooks | Auth / notes |
|---|---|---|---|
| semgrep | ✅ `semgrep mcp` | ✅ PostToolUse scan + SessionStart/UserPromptSubmit inject | token in `~/.semgrep/settings.yml` (not env). See `claude-code-sast-semgrep.md` |
| cloudflare | ✅ api/bindings/builds/observability/docs | — | OAuth (per-server `/mcp` login) |
| figma | ✅ | — | OAuth/token |
| posthog | ✅ | — | API key |
| playwright | ✅ (browser) | — | egress-guard watches navigate; drives a real browser |
| chrome-devtools-mcp | ✅ (browser) | — | pinned `@0.21.0`; egress-guard watches `navigate_page` |
| serena | ✅ (semantic LSP) | — | local; can `execute_shell_command` |
| context7 | ✅ (docs) | — | fetches lib docs (egress) |
| notion | ✅ | — | API token |
| telegram | ✅ | — | bot token (ENERV + managed bots) |
| firecrawl | ✅ (scrape) | — | `fc-*` key; egress-guard watches firecrawl tools |
| superpowers | — | ✅ SessionStart | skills engine; markdown + scripts |
| compound-engineering | — | possible | skills/agents engine |
| claude-md-management | — | — | CLAUDE.md upkeep |
| skill-creator | — | — | skill authoring |
| impeccable | — | — | **audited** markdown-only (no executables) |
| personal-skills (sasha) | — | — | own repo `master5d/claude-personal-skills` |
| frontend-design | — | — | skills |
| agent-sdk-dev | — | — | SDK scaffolding |
| code-modernization | — | — | legacy-analysis skills |
| atomic-agents | — | — | agent patterns |
| cli-anything | — | — | CLI wrapper skills |
| playground | — | — | HTML prototypes |
| rust-analyzer-lsp | — | — | LSP (local) |
| typescript-lsp | — | — | LSP (local) |

> MCP/hook flags are best-effort from the plugin set + observed `/mcp` servers; verify a plugin's `.mcp.json` / `hooks/hooks.json` in its cache dir before trusting a row for high-stakes decisions.

## Removed / disabled
- **github** (`github@claude-plugins-official`) — MCP retired 2026-05-30 after a token-leak incident (the `GITHUB_PERSONAL_ACCESS_TOKEN` env var was a literal dup of gh's keyring token and got printed to stdout). Briefly re-enabled 2026-06-04, then **fully uninstalled 2026-06-06** (`claude plugin uninstall`; cache → Recycle Bin). GitHub access is **gh CLI only** now (`master5d`, keyring, no env-var secret). Reinstalling re-creates the leak surface + needs a Copilot sub — don't, unless there's a concrete reason.

## Complementary controls (not plugins)
- **gitleaks** — secrets at commit time (blocking pre-commit hooks + `~/.claude/gitleaks.toml`).
- **egress-guard hook** — logs/flags outbound URLs for `WebFetch|Bash|firecrawl|chrome-devtools navigate`.
- **permission deny list** (`~/.claude/settings.json`) — blocks reads of `.ssh/`, `.aws/`, `**/.env*`, `**/*.pem`, gh `hosts.yml`, browser profiles, etc.
- **supply-chain pins** — `chrome-devtools-mcp@0.21.0`; plugins installed from a fixed marketplace set.

## Hygiene rules learned
- **Don't `pip install` MCP-tool CLIs into global Python** — they downgrade shared deps (semgrep pulled down `mcp`/`click`, breaking `facet-indexing`/`huggingface-hub`). Use **pipx/uv tool** for isolation.
- **Prefer tokens in a tool's own config file over a Windows env var** — env vars are easy to accidentally echo (the github leak). semgrep's `settings.yml` model is the good pattern.

## See also
- `claude-code-sast-semgrep.md` (semgrep deep-dive)
- `genai-security-best-practices-cheat-sheet.md`
- Memory: `reference_secops_hardening.md` (full deployed state), `reference_plugin_ecosystem.md` (why each plugin)
