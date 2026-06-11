# Migration plan — make NAUTILUS laptop-independent

> **Goal:** zero always-on services on the Surface. The lab survives the laptop
> being off, asleep, or rebooting. **Status:** plan (2026-06-11), not yet executed.

## Target topology

```
┌─ workstation ───────────────┐   ┌─ local always-on (LAN) ──────────────────────┐
│ Surface Laptop Studio 2     │   │ Mac Mini M4 16GB  →  "always-on local brain"  │
│  • dev work                 │   │    LiteLLM gateway + 8-14B llama-server floor │
│  • OPTIONAL 30B power model  │──▶│    + labwatch + (Hermes)                       │
│    (only when powered on)   │   │ Mac Mini M2 #1 (SOVERN-01) → edge daemons:     │
│  • NOTHING depends on it    │   │    STT (Parakeet) · KG ingest · cron · health  │
└─────────────────────────────┘   │ Mac Mini M2 #2 (SOVERN-02) → redundancy/2nd    │
                                   └────────────────────────────────────────────────┘
                                            │
                                   ┌─ cloud (public) ──────────────────────────────┐
                                   │ Hetzner CX22 (→CX32?) behind Cloudflare Tunnel │
                                   │   n8n prod · Langfuse v2 · Dokploy · (Neo4j?)  │
                                   └────────────────────────────────────────────────┘
```

## The one hard constraint

**The 30B local model cannot move to the Mac fleet.** Qwen3-Coder-30B-A3B at Q4
is ~16-18 GB; the M4 has 16 GB unified shared with macOS, the M2s have 8 GB.
So:
- **Always-on local floor → an 8B (comfortable) or 14B (tight) on the M4.**
- **30B stays on the Surface as an on-demand power tier** — in LiteLLM rotation
  only while the laptop is up; the router skips it when it's down.

This is the central trade: full laptop-independence costs you the always-on 30B.
Free clouds (Cerebras qwen-3-235b ~1000 TPS, Groq 70B) remain the high-quality
path; the M4 8-14B is the offline floor. If an always-on local 30B is
non-negotiable, that needs new hardware (e.g. a 32-64GB Mac/mini-PC) — out of
scope here.

---

## Phase 0 — unblock prerequisites (do first)

1. **Onboard the M4** — it isn't a node yet. Reserve a static IP at the router,
   install SSH key, run the SOVERN-01 hardening (disable sleep, NOPASSWD sudo for
   pmset/etc.). Record IP/MAC back into `fleet.json`.
2. **Unblock SOVERN-02** — it's stuck at the FileVault pre-boot screen. Attach
   HDMI + USB keyboard (or a ~$15 MS2109 capture card), type the FileVault
   password once, enable Remote Login, set a DHCP reservation. Until then it's
   not in the pool.
3. **Static DHCP reservations** for all three Macs (M4, .123, .154) so addresses
   don't move under the services that point at them.

## Phase 1 — move the gateway + floor to the M4 (the critical lift)

1. Install on the M4: Python + LiteLLM, `llama-server` (Metal build) with an
   8B or 14B Q4 GGUF, the labwatch server, the port_broker.
2. Move provider API keys to the M4's user env (macOS keychain or a gitignored
   env sourced at launch — mirror `setup-litellm-keys.ps1`).
3. Repoint `litellm-config.yaml`:
   - `local-fallback` / `local` → M4 llama-server (8-14B).
   - add `power-local` → Surface 30B (in fallbacks only, tolerated-down).
   - `LANGFUSE_HOST` → Hetzner `https://logs.synergify.com` (stop using local).
4. Update `config/services.json` to the M4's host:port (gateway + labwatch).
5. **Cutover test:** start everything on the M4, then **power the Surface off**
   and confirm: an agent call routes through the M4 gateway → free clouds and the
   M4 floor; labwatch loads; nothing errors on the missing 30B.

## Phase 2 — edge daemons to the M2 fleet

1. **SOVERN-01:** stand up the STT service (Parakeet/Whisper) + KG ingest worker
   + healthchecks/cron. Point the Echo app's transcription at it.
2. **SOVERN-02** (once unblocked): redundancy — second STT/ingest, or a backup
   gateway that can take over if the M4 is down.
3. Keep these to single-process daemons — the 8 GB M2s can't do more.

## Phase 3 — consolidate the cloud tier & kill local docker

1. **Decommission the Surface local docker stack** — Langfuse + n8n already run
   in prod on Hetzner; remove the redundant local copies (memory already flagged
   the local Langfuse stack for teardown). Point all tracing at Hetzner.
2. **KG Neo4j:** if the graph must be queryable 24/7, move Neo4j off the laptop.
   M4 has headroom (gateway + 8B + Neo4j ~2GB fits 16GB tightly — measure); or
   size Hetzner up to CX32/CX42 and host it there. The Sprint 2 jina-v4 re-embed
   (768→1024) is the natural moment.
3. **Drop Ollama** on the Surface (legacy; floor is llama-server now).

## Phase 4 — resolve the vault-watcher question

The KG ingest watches the Obsidian vault **on the laptop** — it can't be
laptop-independent while the source lives there. Pick one:
- **(a) Accept on-demand ingest** — vault sync only runs when the laptop is up
  (simplest; the rest of the stack is still independent).
- **(b) Relocate the canonical vault** to the SanDisk-on-a-Mac or a synced
  location an M2 watches (true independence; biggest change).
- **(c) Push-on-save** — a laptop hook pushes changed notes to an M2 ingest
  worker (laptop still the source, but ingest is decoupled).

Recommendation: ship (a) now, revisit (b)/(c) if 24/7 ingest becomes a need.

---

## Definition of done

Power the Surface **off** and verify, from the workstation or phone:
- [ ] agent/LLM calls succeed (gateway on M4 → free clouds + M4 floor)
- [ ] labwatch `:4002` loads
- [ ] STT works (M2 node)
- [ ] n8n / Langfuse / public services up (Hetzner — already independent)
- [ ] only loss is the optional 30B power model (expected)

## Open decisions for the architect

1. **Hermes 24/7?** If yes → runs on M4; if only during work → leave on-demand.
2. **KG Neo4j home:** M4 (free, tight) vs Hetzner upgrade (€ cost, clean separation)?
3. **Vault watcher:** option (a) / (b) / (c) above.
4. **SOVERN-02:** redundancy node, or sell it (per `labwatch` inference-economics
   verdict the M2s don't pay off as inference — but as always-on edge daemons
   they earn their keep)?
