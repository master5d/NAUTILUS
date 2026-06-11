# SecOps — NAUTILUS security surface

Merged from `C:\telo\Efforts\Ongoing\SecOps` on **2026-06-11** (old project dir retired, `meta.json` recycled). Dashboard surface: **Labwatch → SecOps panel** (http://localhost:4002), backed by `posture.json` + live local checks.

## Layout

| Path | What |
|---|---|
| `guides/` | Living security docs: plugin inventory (security lens), semgrep SAST setup, GenAI best-practices cheat-sheet, crypto-asset protection playbook |
| `guides/SecOps Notes/` | Webpage snapshot archive (~1.5 MB) — **gitignored**, disk-only |
| `infra/` | Docker stack (CrowdSec + Cloudflare bouncer, Falco + Falcosidekick), Wazuh installer, n8n retaliation playbook — **Hetzner/Linux-target, not deployed locally** |
| `infra/scripts/` | Bitwarden CLI integration (DORMANT, see `infra/BITWARDEN.md`) + `bw.exe` (gitignored, 122 MB) |
| `posture.json` | Manually-maintained posture register (pending rotations, accepted risks) — feeds the Labwatch SecOps panel |

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
