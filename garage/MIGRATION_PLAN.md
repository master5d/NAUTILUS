# Migration plan — laptop-independence (no-floor variant)

> **Goal:** zero always-on services on the Surface. The lab survives the laptop
> being off/asleep/rebooting. **Variant:** no always-on local LLM floor — clouds
> carry inference now; a capable local floor returns later on a planned 64GB+
> node. **Status:** plan (2026-06-11), not yet executed.

## Why no floor

An 8-14B local model is far weaker than the free clouds already in rotation
(Cerebras qwen-3-235b ~1000 TPS, Groq llama-3.3-70b). It only ever served as a
mediocre emergency backstop. So we drop it and split the architecture cleanly by
role instead of forcing a weak model onto a 16GB Mac:

- **Control plane** (gateway, dashboard) — light, always-on → **M4 16GB**.
- **Inference** — clouds now (free→paid); a *capable* local floor later on a
  **64GB+ node** (30B-A3B / 70B-Q4), never a weak 8B.
- **Edge** (audio, vault data) — **M2 ×2**.
- **Public** — **Hetzner**.
- **Dev + on-demand local power** — **Surface** (30B when it's on).

**Accepted tradeoff:** this weakens SOVRN principle #1 ("100% offline if every
cloud goes dark") to "offline only when the Surface 30B is up" — *until* the
64GB node lands and restores a proper always-on local floor. Failure backstop in
the interim is **paid cloud**, not free-local.

## Target topology

```
┌─ workstation ───────────┐   ┌─ control plane (always-on, LAN) ─┐
│ Surface Studio 2        │   │ Mac Mini M4 16GB                  │
│  • dev                  │──▶│   LiteLLM gateway + labwatch      │
│  • on-demand 30B (local │   │   (+ Hermes?)  — NO local model   │
│    power, when powered) │   │   permanent home; doesn't move    │
└─────────────────────────┘   └──────────────────────────────────┘
                                         │ routes to
        ┌────────────────────────────────┼─────────────────────────────┐
        ▼                                 ▼                             ▼
┌─ inference ─────────┐   ┌─ edge (always-on, LAN) ─┐   ┌─ public (cloud) ────────┐
│ FREE clouds first   │   │ M2 #1 SOVERN-01: STT    │   │ Hetzner CX22(→32?)      │
│ (Cerebras/Groq/NIM) │   │ M2 #2 SOVERN-02: ingest │   │  n8n · Langfuse ·       │
│ → paid cloud backstop│  │  (blocked: FileVault)   │   │  Dokploy · CF tunnel    │
│ → [later] 64GB node  │  └─────────────────────────┘   └─────────────────────────┘
│   30B-A3B/70B floor  │
└──────────────────────┘
```

---

## Phase 0 — prerequisites

1. **Onboard the M4** (not a node yet): static DHCP reservation, SSH key, harden
   (disable sleep, NOPASSWD sudo) per the SOVERN-01 pattern. Record IP/MAC in
   `fleet.json`.
2. **Unblock SOVERN-02** (FileVault pre-boot): HDMI + USB keyboard (or ~$15
   MS2109 capture) to type the FileVault password once, enable Remote Login, set
   a DHCP reservation.
3. Static reservations for all three Macs.

## Phase 1 — control plane to the M4 (the critical lift)

1. Install on the M4: Python + LiteLLM + labwatch + port_broker. **No
   llama-server, no model.**
2. Move provider API keys to the M4 user env (macOS keychain / gitignored env).
3. Repoint `litellm-config.yaml` for **no floor**:
   - **remove `local-fallback` from `default_fallbacks`**; set it to e.g.
     `["hf-llama-70b"]` or a paid alias.
   - chain tails that pointed at `local-fallback` → `hf-llama-70b` / paid.
   - add `power-local` → Surface 30B, present in fallbacks only (tolerated-down).
4. Update `config/services.json` to the M4 host:port (gateway + labwatch).
5. **Cutover test:** start the M4 control plane, **power the Surface off**, and
   confirm an agent call routes M4 gateway → free clouds (then paid if exhausted);
   labwatch loads; nothing errors on the absent local floor or 30B.

## Phase 2 — edge daemons to the M2 fleet

1. **SOVERN-01:** STT (Parakeet/Whisper) + healthchecks/cron. Point Echo's
   transcription at it.
2. **SOVERN-02** (once unblocked): KG ingest worker (pending the vault question)
   / redundancy.
3. Single-process daemons only — 8GB M2s (SOVERN-01 already idles ~7.4/8GB).

## Phase 3 — consolidate cloud, kill local docker

1. **Decommission the Surface local docker stack** — Langfuse + n8n already run
   in Hetzner prod; remove the redundant local copies; point tracing at
   `logs.synergify.com`.
2. **KG Neo4j:** if queryable 24/7 is required, move off the laptop → M4 (has
   headroom with no local model) or Hetzner-upgraded. Sprint 2 jina-v4 re-embed
   is the natural moment.
3. **Drop Ollama** on the Surface.

## Phase 4 — vault-watcher (independence blocker)

The KG ingest watches the Obsidian vault **on the laptop**. Pick: (a) accept
on-demand ingest (laptop-up only — simplest; rest of stack still independent);
(b) relocate the canonical vault to a Mac/SanDisk an M2 watches (true
independence); (c) push-on-save hook from the laptop to an M2 worker.
Recommendation: ship (a), revisit if 24/7 ingest becomes a need.

---

## Phase 5 — the 64GB+ node (restores the real local floor)

When the new box lands, it becomes the **always-on inference floor** running a
*capable* model (30B-A3B comfortably, 70B-Q4 feasible) — restoring SOVRN
principle #1 properly. The M4 keeps the control plane (gateway doesn't move);
the 64GB box is pure inference behind the gateway.

### Buying criteria — what actually matters for local LLM

**For LLM, system RAM alone is the wrong metric.** What runs a model is either
**Apple unified memory** or **GPU VRAM** — not a big DDR pool next to a small GPU.

- ✅ **Apple Silicon, 64GB+ unified (recommended)** — Mac Studio M4 Max 64GB,
  Mac Mini M4 Pro 64GB, or used M1/M2 Max Studio 64GB. Unified memory = usable
  model memory; Metal is well-supported; idle power is tiny (always-on friendly);
  fits the existing Mac fleet/ops. 30B-A3B is MoE (3B active) → runs fast on
  Apple Silicon; 64GB also opens 70B-Q4 and larger MoE.
- ⚠️ **x86 + GPU** — only worth it if the **GPU has ≥24GB VRAM** (e.g. RTX
  3090/4090 24GB → 30B-Q4 on-GPU; 70B needs 2×24GB or a 48GB card). A 64GB-RAM
  PC with an 8GB GPU runs 30B only on CPU (slow) — system RAM doesn't fix that.
  Higher idle power, more heat, less always-on friendly.
- ❌ **64GB RAM, no real GPU** — avoid for this purpose; CPU inference of 30B is
  too slow to be a useful always-on floor.

Rule of thumb: **VRAM/unified ≥ model size at Q4 + ~20% headroom.** 30B-A3B Q4
≈ 18GB → 32GB unified is the floor, 64GB gives comfort + 70B-Q4 headroom.

### When it arrives

1. Install llama-server (Metal) + a 30B-A3B or 70B-Q4 GGUF on the 64GB node.
2. Add it to `litellm-config.yaml` as `local-floor` (always-on); restore it to
   the fallback chain tails / `default_fallbacks` ahead of paid.
3. Re-evaluate the M4: it can stay the control-plane host (clean separation), or
   the 64GB box can absorb the gateway too and the M4 frees up for on-demand dev
   inference or resale (per the labwatch inference-economics verdict).
4. Surface 30B becomes purely a dev convenience (no longer the only local option).

---

## Definition of done (interim, no-floor)

Power the Surface **off** and verify from the workstation or phone:
- [ ] agent/LLM calls succeed (M4 gateway → free clouds → paid backstop)
- [ ] labwatch `:4002` loads
- [ ] STT works (M2 node)
- [ ] n8n / Langfuse / public up (Hetzner — already independent)
- [ ] expected losses only: no always-on local inference, no 30B (until 64GB node)

## Open decisions for the architect

1. **Hermes 24/7?** yes → M4 with the gateway; no → on-demand.
2. **KG Neo4j home:** M4 (free, has headroom now) vs Hetzner upgrade?
3. **Vault watcher:** (a)/(b)/(c) above.
4. **64GB node:** Apple Silicon (recommended) vs x86+big-GPU; new vs used.
5. **M2 #2 / M4 after the 64GB node:** redundancy, repurpose, or sell (labwatch
   verdict: Macs don't pay off as pure inference, but earn their keep as
   always-on edge/control-plane).
