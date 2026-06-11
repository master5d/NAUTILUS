# SecOps — NAUTILUS security surface

Merged from `C:\telo\Efforts\Ongoing\SecOps` on **2026-06-11** (old project dir retired, `meta.json` recycled). Dashboard surface: **Labwatch → SecOps panel** (http://localhost:4002), backed by `posture.json` + live local checks.

## Layout

| Path | What |
|---|---|
| `guides/` | Living security docs: plugin inventory (security lens), semgrep SAST setup, GenAI best-practices cheat-sheet, crypto-asset protection playbook, **ai-chat-guard-playbook.md** (runtime-защита продуктовых LLM-чатов: whitelist guard, safe/attack/unclear, layered context, промпты в БД) |
| `guides/SecOps Notes/` | Webpage snapshot archive (~1.5 MB) — **gitignored**, disk-only |
| `infra/` | Docker stack (CrowdSec + Cloudflare bouncer, Falco + Falcosidekick), Wazuh installer, n8n retaliation playbook — **Hetzner/Linux-target, not deployed locally** |
| `infra/scripts/` | Bitwarden CLI integration (DORMANT, see `infra/BITWARDEN.md`) + `bw.exe` (gitignored, 122 MB) |
| `hooks/` | `agent-config-guard.py` (injection/memory scan) + `claude-posture-audit.py` (supply-chain + agency lint) — SessionStart/PostToolUse hooks |
| `baselines/` | `claude-posture-baseline.json` — approved plugin/MCP/marketplace/hook snapshot for drift attestation |
| `posture.json` | Manually-maintained posture register (rotations, accepted risks, agent attack classes, deploy targets, open findings) — feeds the Labwatch SecOps panel |

## Audit 2026-06-11 — findings & dispositions

| # | Finding | Severity | Disposition |
|---|---|---|---|
| 1 | Hardcoded CrowdSec LAPI key in `infra/crowdsec/cloudflare-bouncer.yaml` | Medium | **Fixed** — parametrized to `${CROWDSEC_LAPI_KEY}`, value moved to gitignored `infra/.env`, compose passes it through. Key never entered git. Regenerate via `cscli bouncers add` on (re)deploy. |
| 2 | `infra/.env` holds live secrets (Telegram bot token, CF token + IDs) | High if committed | **Contained** — covered by `.gitignore` (`.env`); protected from agent reads by permission deny list. Long-term: migrate to vault per `BITWARDEN.md` pending list. |
| 3 | `bw.exe` 122 MB binary in `infra/scripts/` | Repo hygiene | **Contained** — `*.exe` gitignored. Note: `BITWARDEN.md` claimed `C:\telo\scripts\bw.exe` — that path never existed anymore; this copy is the only one. Doc updated. |
| 4 | Bouncer container lacked `no-new-privileges` | Low | **Fixed** — added `security_opt` to both services (semgrep CWE-732). |
| 5 | `read_only: true` not set on crowdsec/bouncer containers | Info | **Accepted** — both write to volumes/logs; revisit at deploy time with tmpfs. |
| 6 | Infra stack (CrowdSec/Falco/Wazuh) designed 2026-05-11..13, never deployed (Docker absent locally; targets Hetzner) | Info | **Documented** — status `designed`, tracked in `posture.json`. Wazuh `config.yml` duplicate `nodes:` line **fixed 2026-06-11**. |
| 7 | `retaliation_protocol.sh` interpolated `$ATTACKER_IP`/`$CONTAINER_NAME` unquoted from webhook input | Medium (at deploy) | **Fixed 2026-06-11** — vars quoted, `set -euo pipefail`, IP-format + container-name validation before docker/cscli. |
| 8 | Stale path references after merge (`C:\telo\secops\`, `C:\telo\scripts\`) | Info | **Fixed 2026-06-11** — `start-secops.ps1` uses `$PSScriptRoot`-relative hook path; bw-scripts headers stay historical (dormant), canonical paths in `BITWARDEN.md` banner. |

Live controls на машине (проверяются дашбордом автоматически): gitleaks (scoop) + `~/.claude/gitleaks.toml`, semgrep 1.165.0 (pipx) + login, egress-guard hook + `egress.jsonl`, permission deny list. Полная картина: `guides/claude-code-plugins-secops.md` и memory `reference_secops_hardening`.

## agent-config-guard (hooks/agent-config-guard.py)

Closes the **agent-config-injection** + **memory-poisoning** classes (status `covered` in `posture.json`) — the gap semgrep/gitleaks don't touch. Stdlib Python, no network, logs to `~/.claude/semantic-logger/agent-guard.jsonl`.

- **SessionStart** (advisory, never blocks): scans global + project `CLAUDE.md`/`AGENTS.md`/`GEMINI.md` and the project's auto-memory `*.md`; emits a warning block as additionalContext iff findings.
- **PostToolUse** Write/Edit (blocks via exit 2 on HIGH only): scans the written agent-context file; high-confidence injection → Claude gets a blocking error.
- **Tiers** — HIGH: invisible Unicode (zero-width / bidi override / Unicode-Tag smuggling), exfil/remote-exec command patterns (`curl|bash`, `iwr|iex`, private-key→network), imperative override hidden in an HTML comment. MED (advisory, fenced-code-exempt): visible override phrases (`ignore previous instructions`, `do not tell the user`, `reveal your system prompt`, …).
- **False-positive controls** — fenced code blocks exempt from the MED tier; `agent-guard:allow` suppresses a line; `agent-guard:ignore-file` skips a whole file (used on 3 security memory docs that legitimately quote payloads). Verified clean against the full 68-file real corpus 2026-06-11.
- **Selftest** — `python hooks/agent-config-guard.py selftest`: embedded fixture corpus, 24 cases (one per detection family + one per FP control). Run after ANY regex/tier change; non-zero exit = a detector regressed. 24/24 green 2026-06-11.

Wired in `~/.claude/settings.json` (SessionStart `startup|resume|clear` + PostToolUse `Write|Edit`). Registered, not yet exercised by a live restart — takes effect next session.

## claude-posture-audit (hooks/claude-posture-audit.py)

Closes the **mcp-supply-chain** + **excessive-agency** classes (status `covered`). SessionStart advisory, stdlib, read-only. Two families:

- **Absolute policy rules** (history-independent): `defaultMode == bypassPermissions` (HIGH), dangerous `allow` wildcards (`Bash(*)`, `Read(**)`, …), `deny`-list gaps (missing `.ssh`/`.env`/`.aws`/key coverage), `skipDangerousModePermissionPrompt`.
- **Drift vs committed baseline** (`baselines/claude-posture-baseline.json`): new plugin / marketplace / user-MCP-server / Desktop-MCP-server / enabled `.mcp.json` server (HIGH = trust extension), plugin pin (gitCommitSha) change (MED), hook-command add/change (HIGH = new auto-exec).

`accepted` array in the baseline suppresses acknowledged finding ids (logged, not surfaced). Re-approve a deliberate config change with `python hooks/claude-posture-audit.py baseline`. Manual one-off: `… report`.

**Two findings surfaced on first run, ACCEPTED 2026-06-11 as intentional** (`defaultMode = bypassPermissions` + `skipDangerousModePermissionPrompt = true` — enables prompt-free autonomous agent runs). Both ids live in `baseline.accepted` (audit silent, still logged) and in `posture.json` → `accepted_risks`; `open_posture_findings` is empty.
