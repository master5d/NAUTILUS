# Facet System — Quick Reference

One-page cheat sheet for common tasks.

---

## Setup

```bash
# Initialize root
python -m tools facet init C:\telo

# Create folder with metadata
python -m tools facet new C:\telo\my-project --type project --title "My Project"

# Build index
python -m tools facet index C:\telo
```

---

## Common Commands

| Task | Command | Notes |
|------|---------|-------|
| Show folder info | `facet current-info <path>` | Returns JSON with metadata, stats, children |
| Create folder | `facet new <path> --type <type> --title <title>` | Type: project, topic, agent, script, etc. |
| Index root | `facet index <path>` | Scans all folders, builds index.jsonl |
| Auto-index both | `facet auto-index` | Smart debouncing: tech 3min, knowledge 60min |
| Validate folder | `facet validate [<path>]` | Check metadata validity |
| Move folder | `facet migrate <src> <dest>` | Move between roots, update index |
| Audit root | `facet audit <path>` | Find orphaned/missing metadata |

---

## Claude Code Plugin

```
/facet-current [<path>]
```

- No `<path>`: uses active file's parent or CWD
- With `<path>`: shows that folder's metadata
- Output: markdown with metadata, stats, children list

---

## Roots

| Root | Path | Purpose |
|------|------|---------|
| Tech | `C:\telo\` | Code, projects, agents |
| Knowledge | `E:\` | Knowledge vaults, topics |

---

## Meta.json Fields

```json
{
  "identifier": "proj-20260421-a1b2",
  "title": "My Project",
  "type": "project",
  "status": "active",
  "team": "ai",
  "created": "2026-04-21",
  "updated": "2026-04-21"
}
```

---

## Typical Workflow

```bash
# 1. Initialize root once
python -m tools facet init C:\telo

# 2. Create folders as needed
python -m tools facet new C:\telo\project-a --type project --title "Project A"
python -m tools facet new C:\telo\project-b --type project --title "Project B"

# 3. Index once (or use auto-index on Claude Code SessionStart)
python -m tools facet index C:\telo

# 4. Query in Claude Code
/facet-current C:\telo\project-a
# → Shows metadata, stats, children
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Folder not found" | Check folder exists, use absolute path |
| "⏳ Pending indexing" | Run: `facet new ...` then `facet index ...` |
| Index out of sync | Run: `facet index C:\telo` |
| Validation fails | Fix `meta.json`, re-index |

---

## File Locations

| File | Location | Purpose |
|------|----------|---------|
| Index | `.facets/index.jsonl` | Aggregated metadata (newline-delimited JSON) |
| Config | `.facets/config.json` | Root settings |
| Last-index timestamp | `.facets/.last-index` | Debouncing for auto-index |
| Folder metadata | `meta.json` | Per-folder metadata (hidden file) |

---

## Key Numbers

| Item | Value | Notes |
|------|-------|-------|
| Tech root debounce | 3 minutes | Rebuild if ≥3 min since last index |
| Knowledge debounce | 60 minutes | Rebuild if ≥60 min since last index |
| Index format | JSONL | Newline-delimited JSON (one folder per line) |

---

## Learn More

- Full guide: [`USAGE.md`](USAGE.md)
- Design: [`docs/specs/`](docs/specs/)
- Implementation: [`docs/plans/`](docs/plans/)

---

**Phase 1.2 | 2026-04-21**
