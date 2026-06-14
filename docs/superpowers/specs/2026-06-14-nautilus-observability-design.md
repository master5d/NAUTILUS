# NAUTILUS Observability Layer — Design Spec

- **Date:** 2026-06-14
- **Status:** Approved (design); pending implementation plan
- **Owner:** master5d
- **Module:** `NAUTILUS/labwatch` (evolves the existing single-host prototype into the fleet observability layer)
- **Supersedes:** the single-host, localhost-pinned labwatch model that broke when the always-on stack moved Surface → M4.

## 1. Problem & Goals

### Problem
The current labwatch was built when the whole lab ran on the Surface laptop. Every health probe is pinned to `127.0.0.1`, the wallet collector is a Windows-only PowerShell script, and the data model assumes one host. When the always-on stack moved to the M4 Mac Mini (Variant-A consolidation), that single-host assumption cracked: the dashboard shows phantom-red services that simply live on other hosts, and the wallets panel reads a file that doesn't exist on the M4. This is implementation drift caused by the absence of an explicit ecosystem-wide goal.

### Goal
A **quality, real-time observability layer for the entire NAUTILUS ecosystem**, available **on-demand on the laptop screen**, **security-first**, and **fully sovereign** (no SaaS, no data egress).

### Build vs Buy verdict
The LinearB "buy" conclusion is driven by **team-scale** failure points (identity resolution across people, org-chart drift, multi-persona, external benchmarks, AI-code governance). **None exist for a single-user mesh.** Remove them and the math returns to **build** — provided the architecture is fixed. The thing rotting today is not "too much code"; it is one false assumption (single-host). We therefore **build a re-architected bespoke layer** (Approach A) and **borrow mature libraries** (stdlib `hmac`/`json`/`sqlite3`, `jsonschema`, `psutil`, vendored `uPlot`) — never hand-rolling crypto, charting, or metrics collection. A full self-hosted OSS stack (Grafana + VictoriaMetrics + Loki + Alertmanager, "Approach B") is over-engineered for single-user scale and does not fit the current hardware budget (M4 16GB already running gateway+STT; Hetzner 4GB near-full). Approach C (hybrid bespoke + thin OSS for host metrics/charts) is the documented upgrade path if multi-week trends are needed later.

### Decisions locked during brainstorming
| Axis | Decision |
|------|----------|
| Scope | All four signal classes: (1) service health + host metrics, (2) LLM cost/usage/quotas/wallets, (3) logs & agent traces, (4) secops posture — plus an **advisory tier** (egress, deprecation radar, latency/fallback-rate, backup-freshness, reachability-matrix, pipeline health). |
| Form factor | **Hybrid: tray launcher on Surface → web view + native alerts.** |
| Temporal model | **Hybrid: lightweight always-on watchers (critical/security) that alert even when the dashboard is closed + on-demand point-in-time with live refresh; minimal history.** |
| Approach | **A — re-architected bespoke**, borrow small libraries, not stacks. |
| Transport auth | **Token + HMAC** (mTLS rejected as overkill for LAN). |
| Critical-alert escape | **Telegram CC channel** (sovereign bot) for `critical` severity. |
| Hard constraints | Sovereignty (0 SaaS, 0 data egress), security-first, fits M4 16GB / Hetzner 4GB resource budget. |

### Non-goals (YAGNI)
- No full time-series database; no multi-week/multi-month trend retention.
- No SaaS or cloud-hosted observability.
- No browser E2E test suite at the start.
- No mTLS.
- No team/multi-user features (identity resolution, RBAC, multi-persona views).

## 2. Architecture & Collection Model

**Core principle: push, not pull.** The central collector never makes arbitrary outbound requests. This converts the old `127.0.0.1` probe pin from a workaround into an architectural law and eliminates the SSRF surface.

```
┌─ Surface (dev) ──────┐        ┌─ M4 (always-on) ───────────────────┐
│ reporter ─┐          │        │  collector (labwatch core)         │
│ tray ◀────┼─ SSH ────┼──────▶ │   • POST /ingest  (auth+HMAC, LAN) │
│  (tunnel mgr,         │        │   • watchers (rules engine)        │
│   indicator, alerts)  │        │   • sqlite: latest + thin history  │
└──────────┬───────────┘        │   • GET /  web-view (localhost)    │
           │ push every ~30s     │  reporter (self, LaunchDaemon)     │
           ▼ (POST own snapshot) └──────────────▲─────────────────────┘
                                                 │ pinned-allowlist pull (1 URL)
                                    ┌─ Hetzner (public) ──────┐
                                    │ reporter → snapshot file │
                                    │   behind CF tunnel (auth)│
                                    └──────────────────────────┘
```

- **Each host observes only itself.** A `reporter` on each host probes its own `localhost` (now semantically correct — they are its own services) plus host metrics (psutil/native), then POSTs a signed JSON snapshot to the central collector.
- **The center only receives.** `/ingest` is the single entry point: bearer-token + HMAC, bound to the LAN. It stores the latest snapshot per host plus thin sqlite history and never scrapes outward.
- **Hetzner is the one special case** (behind a different NAT; the center cannot push to it): its reporter writes a snapshot to an authenticated path behind the existing Cloudflare tunnel, and the collector pulls **one hardcoded allowlist URL**. The invariant holds: no data-derived outbound requests, only a fixed allowlist.
- **Web view stays localhost-only on M4.** Surface reaches it through an SSH tunnel managed by the tray. No new dashboard port is exposed on the LAN.
- **Stale is a signal.** If a host stops pushing (silence beyond the threshold), the collector marks it down and raises an alert. A dead reporter is visible automatically.

## 3. Components & Interfaces

Each component has one responsibility, a stable contract, and is independently testable.

| Component | Lives on | Responsibility | Contract (in → out) |
|-----------|----------|----------------|---------------------|
| **reporter** | every host (M4 / Surface / Hetzner / 64GB) | collect **only its own local** state, sign it, send it | cron/interval → `POST /ingest {host, ts, sig, payload}` |
| **collector** | M4 (labwatch core) | accept/verify snapshots, store latest + history, serve aggregate | `POST /ingest` → sqlite; `GET /api/state` → unified JSON |
| **watchers** | inside collector | evaluate incoming snapshots + stale-detection against rules → active alerts | report/tick → `GET /api/alerts` |
| **web-view** | served by collector (localhost) | visualize unified state + history + alerts | `GET /` (HTML, vendored JS) |
| **tray** | Surface | SSH tunnel lifecycle, colored indicator, native toast on new alert | poll `/api/state` + `/api/alerts` → tray UI |

**Stable boundaries:**
- **`collector_payload` schema** — the versioned contract a reporter sends. A reporter does not know how data is rendered; the collector does not know how the reporter obtained it. Either side's internals can change without breaking the other.
- **`/api/state`** — the single source for web-view and tray: `{ hosts: {...}, alerts: [...], generated }`.
- **`/api/alerts`** — separate, so the tray can poll cheaply (active alerts only).
- **`/api/history?metric=&host=&window=`** — thin rollup series for charts.

**Reused from current labwatch (working code is not thrown away):**
- `usage.db` + `usage_stats()` → the `domain` part of the M4 reporter.
- `quotas.json`, `hardware.json`/`econ`, `secops_state()` → also M4 `domain`.
- `collect-wallets.ps1` → becomes the **Surface reporter** (same collection logic, now pushes to the center instead of writing a local file the M4 cannot see — this is the correct fix for the broken wallets panel).
- Current `_probe` (127.0.0.1 pin) → moves into the reporter, where localhost probing is finally semantically correct.

**New code:** `reporter` (shared scaffold + per-host collection plugins), `watchers` (rules engine), `tray`, the payload schema.

## 4. Data Model & Flow

**Payload contract (reporter → `/ingest`):**
```jsonc
{
  "schema_version": 1,
  "host": "m4",                          // m4 | surface | hetzner | node-64gb
  "ts": "2026-06-14T18:30:00Z",          // UTC, collection moment
  "sig": "hmac-sha256(payload, host_key)",
  "payload": {
    "services":   [{ "name": "litellm", "port": 4000, "up": true, "latency_ms": 12 }],
    "host_metrics": { "cpu_pct": 18, "ram_used_gb": 6.4, "ram_total_gb": 16,
                      "disk_pct": 41, "temp_c": 47, "power_w": 9 },
    "domain": { /* host-specific, optional */ }
  }
}
```

`domain` by host:
- **m4** → `usage` (from usage.db), `quotas`, `econ`, `secops`, `fallback_rate`, gateway p50/p95.
- **surface** → `wallets` (Codex/Gemini/Antigravity), on-demand 30B status.
- **hetzner** → n8n/Langfuse/Neo4j health, CF tunnel, Postgres, disk.
- **advisory** (computed by the collector, not a reporter) → deprecation radar, backup freshness, reachability matrix.

**Storage (single sqlite DB `labwatch.db` on M4):**

| Table | Purpose | Retention |
|-------|---------|-----------|
| `snapshots` | raw latest payload per host (latest) | 1 row/host (upsert) |
| `history` | thin rollup points (cpu/ram/up/cost) every ~5 min | 7–14 days, auto-prune |
| `alerts` | active + recently-resolved incidents | 30 days |
| `usage` | existing (LiteLLM callback) — unchanged | as today |

Thin history, **not** a TSDB: fixed rollup fields, cron prune, tens of MB.

**Flows:**
1. **Ingest:** reporter → `POST /ingest` → HMAC + token check → upsert `snapshots` → tick watchers → (every 5 min) write `history`.
2. **Staleness:** on each `GET /api/state`, the collector marks a host `stale` if `now - ts > 90s` (3× interval); stale raises a `host-silent` alert.
3. **Read:** web-view/tray → `GET /api/state` assembles latest per host + open alerts into one JSON; charts → `GET /api/history`.
4. **Advisory:** a separate watcher tick (~10 min) computes derived signals (deprecation dates, backup mtime, reachability) into state.

**Freshness semantics on UI:** every host block carries `ts` + a `live / stale / down` badge, so freshness is always explicit (the direct fix for today's "data is stale" mystery).

## 5. Security Model

Threat model: home LAN is **semi-trusted** (other devices, IoT); the internet is hostile; secrets must never leak into payloads, UI, or logs.

**Reporter → collector authentication (two layers):**
- **Bearer token** per host (`Authorization: Bearer <host_token>`) — rejects strangers on the LAN.
- **HMAC-SHA256** payload signature with a per-host key — tamper/replay protection even if a token is observed. Verified with stdlib `hmac.compare_digest` (constant-time; no custom crypto).
- **Anti-replay:** `ts` included in the signature + a ±120s window; the collector rejects stale/future timestamps. Optional nonce cache.
- Keys: per host, drawn from the **unified key store** below.

### Unified key management

All NAUTILUS mesh secrets — the LiteLLM gateway master key, gateway provider keys, and observability reporter/ingest keys — follow **one convention**, so there is a single mental model and a single rotation path across the mesh. This resolves the prior open question (LiteLLM `LITELLM_MASTER_KEY` vs reporter tokens) by making them instances of the same scheme rather than two ad-hoc systems.

**Convention:**
- **Location:** one gitignored secrets dir per host, `~/.config/nautilus/secrets/`, mode `700`; each secret a single file, mode `600`. Existing `~/nautilus/.env.gateway` is migrated/symlinked under this root so there is exactly one secrets tree per host.
- **Naming:** `<service>.<purpose>` — e.g. `litellm.master_key`, `observability.ingest_key` (the per-host HMAC+bearer key; the bearer token is derived from it via a labeled HKDF so one stored secret yields both the token and the HMAC key — no second file to rotate).
- **Registry (collector only, M4):** `~/.config/nautilus/secrets/observability.keyring.json` (mode `600`, gitignored) maps `host → key_id → key_material` plus `created`/`rotated` timestamps. The collector loads it at startup and on `SIGHUP`.
- **Generation:** keys are 32 bytes from `secrets.token_bytes(32)` (CSPRNG), base64url-encoded. One helper, `nautilus-keys` (a small CLI), does `gen`, `rotate`, `list`, `revoke` — never echoing material to stdout (silent-capture standing principle); it writes files and prints only key IDs/fingerprints.
- **Rotation:** dual-key overlap — a new `key_id` is added to the keyring and pushed to the host; reporters sign with the newest key but the collector accepts any non-revoked key during an overlap window, then the old `key_id` is revoked. Zero-downtime, and the same procedure covers `litellm.master_key`.
- **Rotation surfacing:** key `created`/`rotated` ages feed the `deprecation-soon` watcher (a key older than its policy max-age raises a `warning`), so rotation debt is observable in the same dashboard — closing the loop with secops posture.
- **Boundaries unchanged:** keys never enter payloads, logs, or the web view (see "Secrets never enter observability"). Browser-exposed `NEXT_PUBLIC_*` (KG) is explicitly out of this store — it is non-secret by definition.

**Ingest hardening:**
- **Body size cap** (~256 KB) → 413 on exceed (mirrors the STT service).
- **Schema validation** of the incoming payload (`jsonschema`); unknown fields/types → 400; `additionalProperties: false`.
- **Safe JSON parsing** (stdlib `json`; no eval/pickle, no object deserialization).
- Ingest bound to LAN; dashboard (`GET /`) bound to **localhost only**.

**Transport & exposure:**
- **Web view localhost-only on M4** → Surface via **SSH tunnel** (key auth, `IdentitiesOnly`), tunnel managed by the tray. No new dashboard port on the LAN.
- **Hetzner pull:** exactly one hardcoded allowlist URL behind the CF tunnel, with bearer auth; no data-derived addresses (anti-SSRF invariant).
- Web-view HTTP headers: `Content-Security-Policy` (self, no inline-eval), `X-Content-Type-Options: nosniff`; **no external CDN — JS/CSS vendored locally** (egress-zero + no CDN supply-chain).

**Secrets never enter observability:**
- Payloads carry **facts, not secrets**: statuses, numbers, service names. No tokens/keys/env values, enforced by schema.
- The **secops domain** reports *state* (a pending rotation exists, gitleaks clean/dirty, an expiry date) — **never the values themselves**. Masking happens in the reporter before sending.
- Collector logs never write signed payload bodies; errors are secret-free (standing principle).

**Critical-alert escape hatch:** `critical` security alerts (egress anomaly, secops breach) also go to the existing **Telegram CC channel**, reaching the user even when Surface is off. Sovereign (own bot), not SaaS.

**Net gain vs today:** the center physically cannot be an SSRF vector (receive-only + one allowlist pull); a compromised LAN device cannot forge a snapshot (HMAC); the dashboard is never left LAN-exposed; secrets never enter the observability system at all.

## 6. Watchers & Alerting

Watchers are a **declarative rules engine** inside the collector. Rules live in `watchers.json` (editable without code changes). Each rule: `id`, `signal`, `condition`, `severity`, `channels`, `cooldown_s`, `debounce`.

```jsonc
{
  "id": "service-down",
  "signal": "hosts.*.services[].up",
  "condition": "== false",
  "severity": "critical",
  "channels": ["tray", "telegram"],
  "cooldown_s": 300,
  "debounce": 2
}
```

**Starter rule set:**

| Rule | Condition | Severity | Channels |
|------|-----------|----------|----------|
| `service-down` | any service `up=false` | critical | tray + telegram |
| `host-silent` | no snapshot > 90s | critical | tray + telegram |
| `secops-breach` | gitleaks dirty / new finding | critical | tray + telegram |
| `egress-anomaly` | outbound outside allowlist | critical | tray + telegram |
| `disk-pressure` | disk > 90% | warning | tray |
| `ram-pressure` | ram > 90% (M4 always-on) | warning | tray |
| `fallback-spike` | free→paid share > threshold | warning | tray |
| `deprecation-soon` | death date < 7 days (Gemini CLI, exp models, tokens) | warning | tray |
| `backup-stale` | vault mirror mtime > 48h | warning | tray |

**Alert lifecycle:** `firing` → (condition clears) → `resolved` (lingers 30 min in `alerts` so the user sees what happened). Dedup by `id`+`host`. **Cooldown** suppresses repeats. **Debounce** requires N consecutive confirmations before firing (e.g. service-down needs 2 ticks so a single timeout does not wake Telegram).

**Delivery channels:**
- **tray (Surface)** — polls `/api/alerts`, colors the indicator (green/amber/red = max severity), native toast on new `firing`. Works while Surface is on.
- **Telegram CC channel** — `critical` only, via the existing bot. One message on `firing`, one on `resolved`; rate-limited by cooldown.

**Testability:** the rules engine is a pure function `(state, rules) → alerts`, exercised on state fixtures without network or hardware.

## 7. Phasing

No big-bang; the current labwatch keeps working throughout.

| Phase | Work | Result |
|-------|------|--------|
| **0** | Bootstrap the **unified key store** + `nautilus-keys` helper (migrate `.env.gateway` under it); extract payload schema + `/ingest` (token+HMAC+validation) into the collector; M4 reporter (localhost probes + psutil) pushes to itself | Single secrets convention live; M4 reports through the new path; web-view reads `snapshots`; old localhost probes removed |
| **1** | Surface reporter (evolution of `collect-wallets.ps1` + host metrics) → **wallets panel fixed correctly**; tray launcher (tunnel + indicator) | Surface visible; broken panel alive; tray works |
| **2** | Watchers + `/api/alerts` + Telegram escape | Proactive alerts |
| **3** | Hetzner reporter (behind CF tunnel, pinned pull) + advisory tier (deprecation/backup/reachability) | Full fleet coverage |
| **4** | Web-view redesign: per-host blocks with live/stale/down + charts (vendored uPlot) from `/api/history` | Final UI |
| **5** *(opt.)* | 64GB-node reporter when acquired | Drop-in (same contract) |

Each phase is a separate iteration; the system is functional at every step.

## 8. Error Handling

- **Host offline / reporter crashed** → snapshot goes stale → `host-silent` alert; UI paints the host `down` with last `ts`. Never silently green.
- **Reporter cannot reach collector** → local retry with backoff + spool the snapshot to a small file and resend; the reporter does not crash.
- **Invalid/expired payload** → `400/401`, secret-free log, a "rejected ingests" metric (detects attack or key drift).
- **Hetzner pull unavailable** → that host goes `stale`; it does not bring down the whole `/api/state` (per-host failure isolation).
- **sqlite locked/corrupt** → collector responds degraded (last-good from memory) and raises `collector-degraded`.
- **Telegram unavailable** → the alert still reaches the tray and is queued for resend; Telegram is not a critical path.

## 9. Testing

Layered; unit tests use no network or hardware.

- **rules-engine** — pure `(state, rules) → alerts`; fixtures for down/stale/breach/flap → deterministic alerts. The heart of the test suite.
- **payload validation** — a table of good/bad payloads (oversize, bad HMAC, stale ts, unknown field) → expected codes.
- **collector ingest→state** — in-memory sqlite, feed snapshots → correct `/api/state` + staleness.
- **reporter collectors** — mocked sources (fake psutil/usage.db) → a valid payload against the schema.
- **integration smoke** — bring up collector + a fake reporter on localhost, run one push→state→alert cycle.
- **tray/web-view** — a light check that they render the `/api/state` contract (no browser E2E at the start).

## 10. Build vs Buy in code

We **build** bespoke (contract, collector, watchers, reporter scaffold) and **borrow libraries** (`hmac`/`json`/`sqlite3` stdlib, `jsonschema`, `psutil`, vendored `uPlot`) — we do not write our own crypto, charting, or metrics collection. This is the article's lesson applied at the right granularity: buy the commodity primitives, build the sovereign domain brain.

## 11. Open Questions / Future

- Approach C upgrade path (thin OSS for host metrics/charts) if multi-week trend retention is later required.
- 64GB inference node reporter (Phase 5, drop-in).
- ~~Whether the LiteLLM `LITELLM_MASTER_KEY` work and the reporter token scheme should share a key-management convention.~~ **Resolved:** unified under one convention — see §5 "Unified key management."
- Reachability-matrix UX (how to visualize "who can reach whom" compactly).
