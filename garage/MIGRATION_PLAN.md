# Migration plan — laptop-independence (no-floor + Variant-A consolidation)

> **Goal:** zero always-on services on the Surface. The lab survives the laptop
> being off/asleep/rebooting. **Variant:** no always-on local LLM floor (clouds
> carry inference; capable floor returns later on a 64GB+ node) **+ Variant-A
> consolidation:** all always-on local work runs on the single M4; both M2s are
> sold. **Status:** in progress (updated 2026-06-17). Phase 0 ✅ done · Phase 1
> 🟡 mostly done (M4 control plane LIVE; Echo→STT wiring + Surface-off cutover
> test outstanding) · Phases 2–5 ⬜ not started. Per-phase detail below.

## Why no floor

An 8-14B local model is far weaker than the free clouds already in rotation
(Cerebras qwen-3-235b ~1000 TPS, Groq llama-3.3-70b). It only ever served as a
mediocre emergency backstop. So we drop it and split the architecture cleanly by
role instead of forcing a weak model onto a 16GB Mac:

- **Single local node** (gateway, dashboard, STT, ingest) — **M4 16GB**. With no
  local LLM these all fit (~6.5GB steady / ~9GB peak of 16GB).
- **Inference** — clouds now (free→paid); a *capable* local floor later on a
  **64GB+ node** (30B-A3B / 70B-Q4), never a weak 8B.
- **2× M2 8GB → SOLD** — no role once edge work fits the M4; labwatch verdict says
  they don't pay off as inference. ~$560 back.
- **Public** — **Hetzner**.
- **Dev + on-demand local power** — **Surface** (30B when it's on).

**Accepted cost of consolidation:** the M4 is a single point of failure for the
local tier. Tolerable — the inference backstop is cloud anyway, and the future
64GB node adds a second always-on box.

**Accepted tradeoff:** this weakens SOVRN principle #1 ("100% offline if every
cloud goes dark") to "offline only when the Surface 30B is up" — *until* the
64GB node lands and restores a proper always-on local floor. Failure backstop in
the interim is **paid cloud**, not free-local.

## Target topology

```
┌─ workstation ───────────┐   ┌─ single local node (always-on, LAN) ─┐
│ Surface Studio 2        │   │ Mac Mini M4 16GB                      │
│  • dev                  │──▶│   LiteLLM gateway + labwatch         │
│  • on-demand 30B (local │   │   + STT (Parakeet) + KG ingest       │
│    power, when powered) │   │   (+ Hermes?)  — NO local LLM model  │
└─────────────────────────┘   └──────────────────────────────────────┘
                                         │ routes to
        ┌────────────────────────────────┼─────────────────────────────┐
        ▼                                 ▼                             ▼
┌─ inference ─────────┐   ┌─ SOLD ──────────────────┐   ┌─ public (cloud) ────────┐
│ FREE clouds first   │   │ M2 #1 SOVERN-01 → sell  │   │ Hetzner CX22(→32?)      │
│ (Cerebras/Groq/NIM) │   │ M2 #2 SOVERN-02 → sell  │   │  n8n · Langfuse ·       │
│ → paid cloud backstop│  │  (~$560 back)           │   │  Dokploy · CF tunnel    │
│ → [later] 64GB node  │  └─────────────────────────┘   └─────────────────────────┘
│   30B-A3B/70B floor  │
└──────────────────────┘
```

---

## Phase 0 — prerequisites ✅ DONE (2026-06-14)

1. [x] **Onboard the M4** — SSH key (`id_ed25519_sovern`, alias `m4`), hardened
   (`pmset` sleep 0 / autorestart 1 / womp 1; scoped NOPASSWD sudoers), IP/MAC
   recorded in `fleet.json`. Status `onboarded-live-2026-06-14`. The *only*
   always-on local box. **Note:** addressed via **manual static IP on Wi-Fi**
   (192.168.1.148), not a router DHCP reservation — survives reboot/room-move on
   the same SSID. Router reservation still listed as optional belt-and-suspenders.
2. [ ] **Wipe SOVERN-02 for resale** — still stuck at FileVault pre-boot; not yet
   wiped (deferred to Phase 2, no service role so not blocking).
3. [~] **Static address for the M4** — done via manual Wi-Fi IP (above); router
   DHCP reservation for `.148` still PENDING (user) but non-blocking.

## Phase 1 — stand up the M4 as the single local node (the critical lift) 🟡 MOSTLY DONE

1. [x] Install on the M4: LiteLLM `:4000` + labwatch `:4002` + STT (Parakeet)
   `:4100`, all as LaunchDaemons (`com.sovern.litellm` / `.labwatch` / `.stt`),
   **no llama-server / no LLM model**. KG ingest worker **not yet** moved (blocked
   on vault location — see Phase 4).
2. [x] Provider API keys on the M4 (`.env.gateway` sourced by the LiteLLM daemon,
   gitignored). ⚠ Gateway has **no `LITELLM_MASTER_KEY`** yet — LAN-trust only;
   harden by adding one.
3. [~] Repoint `litellm-config.yaml` for **no floor** — Windows→M4 gateway→free-cloud
   completion verified OK, so routing works; confirm `default_fallbacks` /
   chain-tails no longer point at `local-fallback` and `power-local`→Surface 30B
   is fallback-only.
4. [x] `config/services.json` points at the M4 gateway + labwatch.
5. [ ] Point Echo's transcription path at the M4 STT endpoint (`:4100`) — PENDING.
6. [ ] **Cutover test:** start the M4, **power the Surface off**, confirm agent
   call routes M4 gateway → free clouds (→ paid); labwatch loads; STT transcribes;
   no errors on the absent local floor / 30B — PENDING (user).

## Phase 2 — decommission and sell the M2s ⬜ NOT STARTED

1. Confirm nothing points at SOVERN-01 (192.168.1.123) anymore — remove its
   `~/.ssh/config` alias + DHCP reservation; migrate any edge job to the M4.
2. **Wipe both M2s** (Recovery → Disk Utility erase / DFU restore), sign out of
   iCloud/Find My first so they're sellable (Activation Lock off).
3. **Sell** (~$280 each, ~$560 total). Update `fleet.json` status → sold.

## Phase 3 — consolidate cloud, kill local docker ⬜ NOT STARTED

1. **Decommission the Surface local docker stack** — Langfuse + n8n already run
   in Hetzner prod; remove the redundant local copies; point tracing at
   `logs.synergify.com`.
2. **KG Neo4j:** if queryable 24/7 is required, move off the laptop → M4 (has
   headroom with no local model) or Hetzner-upgraded. Sprint 2 jina-v4 re-embed
   is the natural moment.
3. **Drop Ollama** on the Surface.

## Phase 4 — vault-watcher (independence blocker) ⬜ NOT STARTED

The KG ingest watches the Obsidian vault **on the laptop**. Pick: (a) accept
on-demand ingest (laptop-up only — simplest; rest of stack still independent);
(b) relocate the canonical vault to a Mac/SanDisk an M2 watches (true
independence); (c) push-on-save hook from the laptop to an M2 worker.
Recommendation: ship (a), revisit if 24/7 ingest becomes a need.

---

## Phase 5 — the 64GB+ node (restores the real local floor) ⬜ NOT STARTED

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
- [ ] STT works (M4 node)
- [ ] n8n / Langfuse / public up (Hetzner — already independent)
- [ ] both M2s wiped + sold
- [ ] expected losses only: no always-on local inference, no 30B (until 64GB node)

## Open decisions for the architect

1. **Hermes 24/7?** yes → M4 (co-located); no → on-demand.
2. **KG Neo4j home:** M4 (has headroom: gateway+labwatch+STT+ingest+Neo4j ~2GB
   still fits 16GB, but getting full) vs Hetzner upgrade. If Sprint 2 also runs
   jina-v4 embeddings locally (+4-8GB), the M4 gets tight → Neo4j → Hetzner.
3. **Vault watcher:** (a)/(b)/(c) above.
4. **64GB node:** Apple Silicon (recommended) vs x86+big-GPU; new vs used.
5. ~~M2 fate~~ **DECIDED: both M2s sold** (Variant A consolidation). Only
   re-open if M4 gets memory-tight from local jina-v4 embeddings — then keeping
   one M2 for ingest could be reconsidered (but ingest is light; unlikely).
