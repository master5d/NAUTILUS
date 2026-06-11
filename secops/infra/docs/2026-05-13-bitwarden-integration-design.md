# Bitwarden CLI Integration Design

**Date:** 2026-05-13  
**Status:** Approved  
**Scope:** Install bw CLI + Claude Code session hook + secops pipeline credential management

---

## Problem

Credentials for projects (Vercel, GitHub PAT, Neo4j, Google AI, Cloudflare) are scattered across `.env` files, `setx` env vars, and Windows Credential Manager with no single source of truth. The secops `docker-compose.yml` needs CF credentials that currently live in `secops/.env` (blocked by Claude Code deny list). An audit is needed before migration.

---

## Approach: Session Hook (Approach A)

A startup hook unlocks Bitwarden vault, fetches secrets into process env vars, then immediately re-locks. Claude Code and docker-compose consume env vars — neither calls `bw` directly.

---

## Section 1: bw CLI Installation

- Download `bw.exe` from official Bitwarden GitHub releases (`bitwarden/clients`)
- Place at `C:\telo\scripts\bw.exe`
- Add `C:\telo\scripts` to user PATH permanently via `setx`
- Verify: `bw --version`

No global system changes. Binary is isolated to project scripts directory.

---

## Section 2: Claude Code Integration

**File:** `C:\telo\scripts\bw-unlock-hook.ps1`

**Flow:**
1. Read master password from Windows Credential Manager (`bitwarden-master` entry)
2. `BW_SESSION = bw unlock --raw $master_pass`
3. Fetch each secret into env var:
   - `$env:VERCEL_API_KEY`   ← `bw get password "telo/vercel-ai-gateway"`
   - `$env:GITHUB_PAT`       ← `bw get password "telo/github-pat"`
   - `$env:NEO4J_PASSWORD`   ← `bw get password "telo/neo4j-auradb"`
   - `$env:GOOGLE_AI_KEY`    ← `bw get password "telo/google-ai-studio"`
   - `$env:CF_API_TOKEN`     ← `bw get password "telo/cloudflare"`
   - `$env:CF_ACCOUNT_ID`    ← parsed from `bw get notes "telo/cloudflare"` (JSON notes)
   - `$env:CF_ZONE_ID`       ← parsed from same notes item
4. `Remove-Variable BW_SESSION` — token destroyed after fetch
5. `bw lock` — vault locked immediately

**Security properties:**
- Master password lives only in Windows Credential Manager, never in files
- `BW_SESSION` destroyed immediately after secret fetch — not present in env
- Vault is locked before any user-facing work begins
- Claude Code sees only final env vars, never vault access

**Hook registration** in `~/.claude/settings.json`:
```json
{
  "event": "SessionStart",
  "command": "pwsh -File C:\\telo\\scripts\\bw-unlock-hook.ps1"
}
```

---

## Section 3: Secops Pipeline Integration

**docker-compose passthrough** — `secops/docker-compose.yml` reads from process env, not from `.env` file:

```yaml
crowdsec-cloudflare-bouncer:
  environment:
    CF_ACCOUNT_ID: ${CF_ACCOUNT_ID}
    CF_ZONE_ID: ${CF_ZONE_ID}
    CF_API_TOKEN: ${CF_API_TOKEN}
```

`secops/.env` is retired (or reduced to non-secret config like `GID`).

**Audit script:** `C:\telo\scripts\bw-audit.ps1`
- Scans known env vars (VERCEL_API_KEY, GITHUB_PAT, NEO4J_PASSWORD, CF_*, GOOGLE_AI_KEY)
- Checks Windows Credential Manager entries
- Scans for `.env*` files in `C:\telo` subtree (reports paths only, no values)
- Reports migration status: what's in Bitwarden vs. what's still elsewhere

**Bitwarden vault structure** (all items under `telo/` folder):
```
telo/cloudflare          password=CF_API_TOKEN, notes={"CF_ACCOUNT_ID":"...","CF_ZONE_ID":"..."}
telo/github-pat          password=GITHUB_PAT
telo/vercel-ai-gateway   password=VERCEL_API_KEY
telo/neo4j-auradb        password=NEO4J_PASSWORD
telo/google-ai-studio    password=GOOGLE_AI_KEY
```

---

## Full Session Flow

```
Claude Code start
  → SessionStart hook: bw-unlock-hook.ps1
      → Credential Manager → master_pass
      → bw unlock → BW_SESSION (ephemeral)
      → fetch secrets → $env:* vars
      → BW_SESSION destroyed
      → bw lock
  → Claude Code session runs with env vars available
  → docker-compose up reads same env vars
  → secops containers start with correct credentials
Claude Code stop
  → env vars released with process memory
```

---

## Out of Scope

- Bitwarden Secrets Manager (BSM) — separate product, not needed for personal setup
- Automatic vault item creation — user populates `telo/` folder manually before first run
- SSH key management via Bitwarden — deferred to Track 2 identity hardening

---

## Prerequisites

- Bitwarden desktop app installed with existing vault
- `cmdkey` entry `bitwarden-master` created before first hook run
- `telo/` folder and items populated in Bitwarden vault before running hook
