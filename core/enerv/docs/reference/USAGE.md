# Facet System Usage Guide

Complete guide to using the Faceted Indexing System for personal project and knowledge folders.

---

## Quick Start

### Installation

The ENERV is a Python CLI tool. No special installation needed—use directly from the repository:

```bash
cd C:\telo\ENERV
python -m tools facet --help
```

### First Steps

1. **Initialize a root** (tech or knowledge):
   ```bash
   python -m tools facet init C:\telo
   ```
   Creates `.facets/` directory with index and config.

2. **Create a folder with metadata**:
   ```bash
   python -m tools facet new "C:\telo\my-project" --type project --title "My Project"
   ```
   Generates `meta.json` with folder metadata.

3. **Build the index**:
   ```bash
   python -m tools facet index C:\telo
   ```
   Scans all folders, aggregates metadata into `index.jsonl`.

4. **Query folder info** (Claude Code or CLI):
   ```bash
   python -m tools facet current-info C:\telo\my-project
   ```
   Returns folder metadata, stats, and children.

---

## Root Structure

The ENERV manages two independent roots:

| Root | Path | Purpose | Use For |
|------|------|---------|---------|
| **Tech** | `C:\telo\` | Code, projects, agents, scripts | Development work, automation, builds |
| **Knowledge** | `E:\` | Knowledge vaults, topics, practices | Learning, research, PKM (personal knowledge management) |

Each root has:
- `.facets/index.jsonl` — Aggregated metadata from all folders
- `.facets/.last-index` — Timestamp of last index rebuild (for debouncing)
- `.facets/config.json` — Root-specific settings

---

## Commands Reference

### `facet init <root-path>`

Initialize a root directory with Facet metadata layer.

**Usage:**
```bash
python -m tools facet init C:\telo
```

**What it does:**
- Creates `.facets/` directory (hidden on Windows)
- Initializes `config.json` with root settings
- Creates empty `index.jsonl` (populated on first index run)

**Options:**
- None (auto-detects root type: tech or knowledge)

**Example:**
```bash
python -m tools facet init E:\  # Initialize knowledge root
```

---

### `facet new <path> --type <type> --title <title>`

Create a new folder with metadata.

**Usage:**
```bash
python -m tools facet new C:\telo\project-x --type project --title "Project X"
```

**Parameters:**
- `path` — Absolute folder path (created if doesn't exist)
- `--type` — Folder type: `project`, `topic`, `agent`, `script`, etc.
- `--title` — Human-readable name for the folder

**What it does:**
- Creates folder at `path` if it doesn't exist
- Generates `meta.json` with:
  - Unique identifier (auto-generated)
  - Title, type, status, team
  - Created/updated timestamps
- Sets folder to hidden (Windows)

**Status field:** Defaults to `active`. Can be `active`, `archived`, `paused`.

**Team field:** Defaults to `ai`. Used for filtering/grouping.

**Example:**
```bash
python -m tools facet new E:\knowledge\machine-learning --type topic --title "Machine Learning" --team ai
```

---

### `facet index <root-path>`

Scan folder tree and aggregate metadata into `index.jsonl`.

**Usage:**
```bash
python -m tools facet index C:\telo
```

**What it does:**
- Walks entire root tree
- Finds all `meta.json` files
- Aggregates into newline-delimited JSON (`index.jsonl`)
- Updates `.last-index` timestamp

**Performance:**
- Typical: 100-500ms for 50-100 folders
- No incremental mode (full rebuild each time)

**Example:**
```bash
python -m tools facet index C:\telo  # Index tech root
python -m tools facet index E:\              # Index knowledge root
```

---

### `facet auto-index`

Automatically index both roots with smart debouncing.

**Usage:**
```bash
python -m tools facet auto-index
```

**What it does:**
- Checks both roots' last-index timestamps
- Tech root: rebuilds if ≥3 minutes since last index
- Knowledge root: rebuilds if ≥60 minutes since last index
- Updates `.last-index` for each root independently
- Returns JSON summary

**Output:**
```json
{
  "tech": {
    "indexed": true,
    "reason": "3.5 minutes elapsed",
    "entry_count": 34
  },
  "knowledge": {
    "indexed": false,
    "reason": "45 minutes elapsed (60 min threshold)",
    "entry_count": 10
  },
  "timestamp": "2026-04-21T14:30:42.123456"
}
```

**Integration:** Runs automatically on Claude Code SessionStart (via hook).

**Example:**
```bash
python -m tools facet auto-index  # Indexes roots if thresholds exceeded
```

---

### `facet current-info <path>`

Show folder metadata and filesystem statistics.

**Usage:**
```bash
python -m tools facet current-info C:\telo\my-project
```

**Parameters:**
- `path` — Absolute or relative folder path

**Output:** JSON with:
- `path` — Absolute folder path
- `indexed` — Boolean (true if folder has metadata in index)
- `metadata` — Object with title, type, status, team, dates (or null if unindexed)
- `stats` — File count, folder count, total size, last-modified
- `children` — List of immediate children with indexed status

**Exit codes:**
- `0` — Success (indexed or unindexed)
- `1` — Folder doesn't exist
- `2` — Other error

**Example:**
```bash
# Show indexed project
python -m tools facet current-info C:\telo\my-project

# Show unindexed folder (still returns stats and children)
python -m tools facet current-info C:\telo

# Missing folder → error
python -m tools facet current-info /nonexistent → exit code 1
```

---

### `facet validate [<path>]`

Validate metadata structure and consistency.

**Usage:**
```bash
python -m tools facet validate C:\telo\my-project
```

**Parameters:**
- `path` (optional) — Folder to validate. If omitted, validates current directory.

**Checks:**
- `meta.json` exists and is valid JSON
- Required fields present: identifier, title, type, status, team, created, updated
- Field formats correct (dates in ISO 8601, etc.)
- Identifier format matches spec

**Example:**
```bash
python -m tools facet validate  # Validate current folder
python -m tools facet validate E:\knowledge\topic  # Validate specific folder
```

---

### `facet migrate <source> <dest>`

Move a folder between roots and update metadata/index.

**Usage:**
```bash
python -m tools facet migrate C:\telo\old-project E:\archived\old-project
```

**What it does:**
- Moves folder from source to destination
- Updates paths in all references
- Re-indexes both roots
- Preserves metadata

**Example:**
```bash
# Archive a project to knowledge root
python -m tools facet migrate C:\telo\completed-project E:\archive\completed-project
```

---

### `facet audit`

Audit the entire index for consistency and issues.

**Usage:**
```bash
python -m tools facet audit C:\telo
```

**Checks:**
- All folders in index still exist on filesystem
- All folders on filesystem have metadata
- Metadata consistency (required fields, formats)
- Orphaned or stale entries

**Output:** Report of issues found.

**Example:**
```bash
python -m tools facet audit C:\telo  # Check tech root for issues
```

---

## Claude Code Plugin: `/facet-current`

Quick folder navigation in Claude Code editor.

### Usage

**In Claude Code, type:**
```
/facet-current [<path>]
```

**Context resolution (in order):**
1. If `<path>` provided, use that folder
2. If file is open/active, use its parent directory
3. Otherwise, use current working directory

### Output

Markdown display with:
- Folder name + indexed status badge (✓ indexed / ⏳ pending)
- Metadata card (if indexed) or "pending indexing" message
- Statistics: file/folder counts, size, last modified
- Children list: files and folders with icons, indexed status, details

### Examples

**Case 1: Show current working directory**
```
/facet-current
```
→ Shows metadata for CWD (or parent of active file)

**Case 2: Show specific folder**
```
/facet-current C:\telo\my-project
```
→ Shows metadata for that folder

**Case 3: Unindexed folder**
```
/facet-current C:\telo
```
→ Shows ⏳ Pending indexing badge, but still lists children and stats

**Case 4: Missing folder**
```
/facet-current /nonexistent
```
→ Shows error: "Folder not found"

---

## Meta.json Schema

Each indexed folder contains `meta.json` with required fields:

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

**Field Reference:**

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `identifier` | string | `proj-20260421-a1b2` | Unique ID (auto-generated, format: `{type}-{date}-{random}`) |
| `title` | string | `My Project` | Human-readable name |
| `type` | string | `project`, `topic`, `agent` | Folder category |
| `status` | string | `active`, `archived`, `paused` | Current state |
| `team` | string | `ai`, `data`, `backend` | Team/domain classification |
| `created` | date | `2026-04-21` | ISO 8601 creation date |
| `updated` | date | `2026-04-21` | ISO 8601 last update date |

**Custom fields:** You can add additional fields as needed (they'll be preserved in index).

---

## Index File Format

`index.jsonl` is a newline-delimited JSON file. Each line is one folder's metadata:

```
{"path": "C:\\telo\\project-a", "identifier": "...", "title": "..."}
{"path": "C:\\telo\\project-b", "identifier": "...", "title": "..."}
{"path": "E:\\knowledge\\topic-1", "identifier": "...", "title": "..."}
```

**Why JSONL?**
- Streaming reads (can process large indexes line-by-line)
- Append-friendly (no JSON structure rewriting)
- Human-readable
- Standard format for log/event data

---

## Workflows

### Setting Up a New Root

```bash
# 1. Initialize root
python -m tools facet init C:\telo

# 2. Create first folder with metadata
python -m tools facet new C:\telo\my-project --type project --title "My Project"

# 3. Build index
python -m tools facet index C:\telo

# 4. Query in Claude Code
/facet-current C:\telo\my-project
```

### Batch Creating Folders

```bash
# Create multiple folders with metadata
python -m tools facet new C:\telo\agent-1 --type agent --title "Agent 1"
python -m tools facet new C:\telo\agent-2 --type agent --title "Agent 2"
python -m tools facet new C:\telo\script-1 --type script --title "Script 1"

# Index all at once
python -m tools facet index C:\telo
```

### Archiving a Project

```bash
# Move to archive folder
python -m tools facet migrate C:\telo\completed-project E:\archive\completed-project

# Verify
python -m tools facet audit C:\telo  # Check tech root
python -m tools facet audit E:\              # Check knowledge root
```

### Validating System Health

```bash
# Check both roots
python -m tools facet audit C:\telo
python -m tools facet audit E:\

# Rebuild indexes if needed
python -m tools facet index C:\telo
python -m tools facet index E:\
```

---

## Troubleshooting

### "Folder not found" Error

```bash
python -m tools facet current-info /nonexistent
# Error: Folder not found: /nonexistent
```

**Fix:** Verify folder exists on filesystem and use absolute or correct relative path.

---

### "Pending indexing" Status

```bash
/facet-current C:\telo\new-folder
# Shows: ⏳ Pending indexing
```

**Fix:** Create metadata for the folder:
```bash
python -m tools facet new C:\telo\new-folder --type project --title "New Folder"
python -m tools facet index C:\telo
```

---

### Index Out of Sync

```bash
python -m tools facet audit C:\telo
# Reports: Orphaned entries, missing metadata, etc.
```

**Fix:** Rebuild the index:
```bash
python -m tools facet index C:\telo
```

---

### Metadata Validation Fails

```bash
python -m tools facet validate C:\telo\my-project
# Error: Invalid field format
```

**Fix:** Edit `meta.json` to match schema, then re-index:
```bash
python -m tools facet index C:\telo
```

---

## Performance Tips

1. **Index Debouncing:** Use `facet auto-index` instead of manually running `facet index`—it respects thresholds (3 min for tech, 60 min for knowledge).

2. **Batch Operations:** Create multiple folders first, then index once:
   ```bash
   # ✅ Efficient
   python -m tools facet new folder1 ...
   python -m tools facet new folder2 ...
   python -m tools facet index C:\telo
   
   # ❌ Inefficient (indexes 3 times)
   python -m tools facet new folder1 ... && facet index
   python -m tools facet new folder2 ... && facet index
   ```

3. **Avoid Frequent Migrations:** Moving folders is cheap (just path updates), but re-indexes both roots.

4. **Keep `meta.json` Small:** Metadata is copied to `index.jsonl`, so minimal custom fields = faster indexing.

---

## API Integration

### Python

Import the core modules:

```python
from tools.core.index import IndexAggregator
from tools.core.meta import MetaFile
from tools.core.config import Config

# Rebuild index for a root
aggregator = IndexAggregator(root_path, facets_dir, debounce_minutes=0)
aggregator.rebuild(force=True)

# Read metadata
meta = MetaFile.read(Path("meta.json"))
print(meta["title"])
```

### JSON/CLI

All commands return JSON (use `| jq` for parsing):

```bash
python -m tools facet current-info C:\telo\my-project | jq .metadata
```

---

## FAQ

**Q: Can I use Facet with version control (git)?**  
A: Yes. Add `.facets/` to `.gitignore` to avoid syncing indexes—they rebuild on each root. Commit `meta.json` files so collaborators see metadata.

**Q: What if I delete a folder without using `facet migrate`?**  
A: Run `facet audit` to detect orphaned entries, then `facet index` to rebuild. No manual cleanup needed.

**Q: Can I use custom metadata fields?**  
A: Yes. Add any fields to `meta.json`; they'll be preserved in `index.jsonl`. Schema validation only checks required fields.

**Q: How do I query the index programmatically?**  
A: Read `index.jsonl` line-by-line (each line is valid JSON). For AI agents: use `/facet-current` in Claude Code or the Python API.

**Q: Does Facet support nested folder hierarchies?**  
A: Facet treats each folder independently (flat structure). You can organize nested folders naturally; each can have its own `meta.json`.

---

## See Also

- [`docs/specs/`](docs/specs/) — Design specifications
- [`docs/plans/`](docs/plans/) — Implementation plans
- [`tools/commands/README-auto-index.md`](tools/commands/README-auto-index.md) — `facet auto-index` deep dive
- [`tools/commands/README-current-info.md`](tools/commands/README-current-info.md) — `facet current-info` details

---

**Version:** Phase 1.2 (2026-04-21)  
**Status:** Stable (auto-index + current-info verified with 17 tests passing)
