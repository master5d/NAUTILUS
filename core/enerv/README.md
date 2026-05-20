# ENERV

Faceted indexing and metadata system for personal project and knowledge folders.

## What this is

A two-root metadata layer that lets AI agents filter and rank content across:

- **Tech root** (`C:\telo\`) — code projects, agents, micro-scripts, sandboxes
- **Knowledge root** (`E:\`) — knowledge vaults, topics, practices (personal knowledge management)

Each folder gets a `meta.json` following a shared core schema with type-specific extensions. A shared CLI (`facet`) handles creation, classification, validation, indexing, and querying.

Distribution is dual: standalone Python CLI for universal shell use + Claude Code plugin wrapper for tight harness integration.

## Status

- **2026-04-21** — Phase 1.2 complete ✅
  - Python backend: `facet current-info` CLI command (8 tasks, 17 tests passing)
  - Claude Code plugin: `/facet-current` slash command (5 tasks)
  - Integration testing verified (1 task)
  - See [`docs/specs/`](docs/specs/) for design documents
  - See [`docs/plans/`](docs/plans/) for implementation plans

## Getting Started

- **Quick start:** See [`QUICK-REFERENCE.md`](QUICK-REFERENCE.md) (one-page cheat sheet)
- **Full guide:** See [`USAGE.md`](USAGE.md) (complete reference with workflows)
- **Phase 1.1:** See [`tools/commands/README-auto-index.md`](tools/commands/README-auto-index.md)

## Structure

```
ENERV/
├── docs/
│   ├── specs/      # design documents
│   └── plans/      # implementation plans
├── tools/          # Python CLI (source of truth)
│   └── schemas/    # JSON Schema files
├── plugin/         # Claude Code plugin wrapper
└── templates/      # canonical FACETS.md and index templates
```
