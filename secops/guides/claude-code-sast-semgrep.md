# Local SAST in the Claude Code loop — Semgrep

**Added:** 2026-06-04 · **Scope:** Windows 11 Claude Code harness, all `C:\telo` projects

## Why
Closes a gap in the existing posture. The toolchain now has two complementary
real-time layers in the coding loop:

| Layer | Tool | Catches |
|---|---|---|
| Secrets | **gitleaks** (`gitleaks protect --staged` pre-commit hooks + `~/.claude/gitleaks.toml`) | leaked API keys, tokens, credentials |
| Code vulns (SAST) | **semgrep** (`semgrep@claude-plugins-official`) | injection, unsafe deserialization, path traversal, weak crypto, OWASP-class bugs |

Semgrep guides Claude Code to write secure code *as it edits* and scans diffs
for exploitable patterns — the "continuously scan for vulnerabilities" item from
the GenAI cheat-sheet (Practice #5), now automated in-loop rather than manual.

## Install (Windows reality — fixed 2026-06-06)
The plugin only registers an MCP server that runs `semgrep mcp`; it does **not**
install the `semgrep` binary. From 2026-06-04→06 the binary was missing, so the
server failed to spawn (`/mcp` showed `-32000`) — the feature never actually ran.

Fixed by installing the CLI **isolated via pipx** (semgrep 1.165.0 runs natively
on Windows now — OCaml core works; older "WSL/Docker only" lore is stale):
```powershell
pipx install semgrep      # lands in ~\.local\bin (on persistent User PATH)
pipx ensurepath
```
Do NOT `pip install semgrep` into global Python — it downgrades shared deps
(`mcp`, `click`), breaking `facet-indexing` / `huggingface-hub`. pipx isolates it.
Pro engine / registry-auth rules need `semgrep login` (optional; OSS rules work
without it). Restart Claude Code after install so the plugin picks up PATH.

**Logged in 2026-06-06** — `semgrep login` done (token in `~/.semgrep/settings.yml`,
not an env var). This unblocks the plugin's PostToolUse `Write|Edit` scan hook,
which otherwise hard-fails with "No SEMGREP_APP_TOKEN found" and blocks edits.

## Usage
- Installed as a Claude Code plugin (user scope) + pipx CLI binary. Activates next session.
- Invoke on a diff/branch before review; pairs with `superpowers:requesting-code-review`
  and `ce-code-review` as an additional, rules-based signal (7,000+ rules).
- Keep it advisory inside the RIPER **REVIEW** mode — a finding is input to
  judgment, not an auto-block.

## Relationship to other controls
- **gitleaks** → secrets (commit-time gate, blocking).
- **semgrep** → code vulnerabilities (review-time, advisory).
- **egress-guard hook** → outbound URL monitoring (runtime).
- **permission deny list** (`~/.claude/settings.json`) → blocks reads of secret files.

Together: secrets, code, egress, and filesystem access each have a control.

## See also
- `claude-code-plugins-secops.md` (plugin inventory from a security lens)
- `genai-security-best-practices-cheat-sheet.md` (Practice #5: detect/remove AI risks)
- Memory: `reference_secops_hardening.md` (full deployed state)
