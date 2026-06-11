# Bitwarden CLI Integration

> **STATUS: DORMANT** (hooks disabled 2026-05-18 — no active workflow + bw 2026.4.1 session-token regression; see memory `reference_bitwarden_integration`). Scripts preserved for revival. Paths below referencing `C:\telo\scripts\` / `C:\telo\secops\` are historical — everything now lives in `NAUTILUS\secops\infra\scripts\` (incl. `bw.exe`, gitignored).

Secrets are managed via Bitwarden CLI. No plaintext credentials in `.env` files or `setx` vars.

## How it works

Claude Code SessionStart hook (`bw-unlock-hook.ps1`) unlocks the vault, fetches secrets into process env vars, then immediately locks. SessionEnd hook clears everything.

## Setup state (2026-05-14)

- `bw.exe` v2026.4.1 installed at `C:\telo\scripts\bw.exe`
- Master password encrypted via DPAPI at `~/.claude/bw-master.dpapi`
- Vault login: `bw login --apikey` (email/password blocked by FIDO2 — use API key from vault.bitwarden.com → Settings → Security → Keys)
- SessionStart/SessionEnd hooks registered in `~/.claude/settings.json`

## Vault structure

All items in `telo/` folder:

| Item | Env var(s) |
|------|-----------|
| `telo/cloudflare` | `CF_API_TOKEN` (password), `CF_ACCOUNT_ID` + `CF_ZONE_ID` (notes JSON) |
| `telo/github-pat` | `GITHUB_PAT` |
| `telo/vercel-ai-gateway` | `VERCEL_API_KEY` |
| `telo/neo4j-auradb` | `NEO4J_PASSWORD` |
| `telo/google-ai-studio` | `GOOGLE_AI_KEY` |

Notes format for `telo/cloudflare`:
```json
{"CF_ACCOUNT_ID":"...","CF_ZONE_ID":"..."}
```

## Scripts

| Script | Purpose |
|--------|---------|
| `C:\telo\scripts\bw-unlock-hook.ps1` | SessionStart hook — unlock → fetch 7 secrets → lock |
| `C:\telo\scripts\bw-lock-hook.ps1` | SessionEnd hook — clear session file + User env vars |
| `C:\telo\scripts\bw-audit.ps1` | Audit — reports migration status of all secrets |
| `C:\telo\scripts\bw-vault-populate.ps1` | Interactive — prompts for secrets, creates vault items |
| `C:\telo\secops\start-secops.ps1` | Wrapper — loads BW secrets then runs `docker compose up` |

## For new agents / fresh setup

1. Install `bw.exe` to `C:\telo\scripts\` and add to PATH
2. Run `bw login --apikey` (get client_id + client_secret from vault.bitwarden.com)
3. Store master password: `pwsh -File C:\telo\scripts\bw-vault-populate.ps1` (first run handles DPAPI setup too — see plan)
4. Actually store DPAPI: run the DPAPI block from `docs/superpowers/plans/2026-05-13-bitwarden-integration.md` Task 2
5. Hooks are already registered in `~/.claude/settings.json` — restart Claude Code to activate

## Starting secops stack

```powershell
pwsh -File C:\telo\secops\start-secops.ps1
```

Automatically sources BW secrets before `docker compose up -d`.

## Pending

- `C:\telo\secops\.env` — migrate GID and any remaining vars to vault, then delete
- `.env.local` files in Efforts/ projects — migrate project secrets to vault items
