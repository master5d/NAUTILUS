# 🔧 Garage — NAUTILUS hardware fleet & workload topology

**Garage** is the canonical registry of every compute unit in the SOVERN/NAUTILUS
estate and the source of truth for *what runs where*. It answers two questions:

1. **What hardware do we have?** → `fleet.json` (CMDB: specs, network, power, status, cost)
2. **What runs on it, and where should it run?** → `workloads.json` (service → host mapping)

## Files

| File | What |
| --- | --- |
| `fleet.json` | Every unit: Surface workstation, Mac Mini M4, 2× Mac Mini M2 (SOVERN-01/02), Hetzner CX22, peripherals. Superset of `labwatch/hardware.json`. |
| `workloads.json` | Each service with `host_now`, `host_target`, and `always_on` flag. |
| `MIGRATION_PLAN.md` | Phased plan to make the stack laptop-independent. |

## Tiers

- **workstation** (`surface`) — dev only; **hosts zero always-on services** (target state).
- **local_always_on** (`m4-16gb`, `sovern-01`, `sovern-02`) — headless nodes that never sleep; the sovereign floor.
- **cloud** (`hetzner-sovern-hub`) — public-facing production behind Cloudflare Tunnel.

## The core objective

> The system must be independent of whether the Surface laptop is on or off.

Today the Surface carries the entire always-on stack (LiteLLM gateway, 30B
llama-server, labwatch, vault watcher, a docker stack, Hermes, Ollama). When the
laptop sleeps or reboots, the lab goes dark. Garage moves that load to the
always-on local fleet + Hetzner; see `MIGRATION_PLAN.md`.

**Current variant: no-floor + Variant-A consolidation.** No always-on local LLM
in the interim — clouds (free→paid) carry inference. With no model on the M4, ALL
always-on local work (gateway, labwatch, STT, KG ingest) consolidates onto the
**single M4**; both M2s are **sold** (~$560). A capable local floor
(30B-A3B/70B) returns later on a planned 64GB+ unified-memory node (`fleet.json`
→ `planned-64gb-node`), not a weak 8B. Tradeoff: the M4 is a single point of
failure for the local tier — accepted (cloud backstop covers inference).

## Relationship to labwatch

`labwatch/hardware.json` is the **inference-cost subset** (the 3 Mac Minis, for
the $/Mtok calculator). `garage/fleet.json` is the **full estate**. Keep them in
sync for the Mac Minis; a future refactor could have labwatch read fleet.json.

## Cross-references

- Node onboarding (SSH, FileVault, hardening): memory `project_sovern_macmini_nodes`
- Cloud infra (Hetzner, Cloudflare, tunnels): memory `project_sovern_infra`
- Inference economics: `labwatch/hardware.json` + Labwatch `:4002`
