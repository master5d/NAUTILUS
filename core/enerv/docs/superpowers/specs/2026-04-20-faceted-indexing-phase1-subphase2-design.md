# Faceted Indexing Phase 1, Sub-phase 1.2: Claude Code Plugin + Folder Navigation

> **Status:** Design approved — ready for implementation plan  
> **Date:** 2026-04-20  
> **Scope:** Native Claude Code plugin with `/facet-current` slash command for quick folder metadata and child navigation

---

## Goal

Enable users to quickly inspect a folder's faceted metadata and browse indexed children via a Claude Code slash command. Plugin resolves context intelligently (active file → CWD → override) and delegates all heavy lifting to Python backend.

---

## Architecture

### Two-Layer Design

**Layer 1: Python Backend** (`tools/commands/current_info.py`)
- New Click command: `facet current-info <path>`
- Validates folder exists on filesystem
- Reads `index.jsonl` from appropriate root to find folder metadata
- Walks filesystem to gather stats (file/folder counts, size, last-modified)
- Returns structured JSON with metadata, stats, and indexed children

**Layer 2: JavaScript Plugin** (`~/.claude/plugins/facet-current/plugin.js`)
- Defines `/facet-current` slash command
- Resolves context: active file's parent folder → CWD fallback → user-provided path override
- Calls Python command via subprocess
- Parses JSON response
- Renders user-friendly UI with metadata header, stats, and browsable children list

### Data Flow

```
User interaction:
  /facet-current                    (uses active file/CWD)
  /facet-current /custom/path       (explicit override)
    ↓
Plugin context resolution
    ↓
Subprocess call: python -m tools facet current-info <resolved-path>
    ↓
Python validates + reads index + walks folder
    ↓
JSON response with metadata + stats + children
    ↓
Plugin renders formatted output
```

---

## Components

### Python Command: `current_info.py`

**Input:**
- `path` argument (string, required)

**Processing:**
1. Validate folder exists; fail if missing
2. Determine root (tech: `C:\telo\`, knowledge: `E:\`)
3. Read `.facets/index.jsonl` from that root
4. Search index for matching folder entry (by absolute path)
5. Extract metadata if found; otherwise mark `indexed: false` with reason `"pending_indexing"`
6. Walk folder structure:
   - Count immediate children (files and folders)
   - Calculate total size in bytes
   - Get last-modified timestamp of folder
7. For each child, include in output:
   - Name, type (file/folder)
   - Whether it's indexed (present in index.jsonl)
   - For folders: file count, last-modified
   - For files: size, last-modified
8. Sort children: indexed first, then by name

**Output (JSON):**
```json
{
  "path": "/absolute/path/to/folder",
  "indexed": true,
  "metadata": {
    "identifier": "proj-20260420-3f9a",
    "title": "Project Name",
    "type": "project",
    "status": "active",
    "team": "ai",
    "created": "2026-04-20",
    "updated": "2026-04-20"
  },
  "stats": {
    "file_count": 12,
    "folder_count": 3,
    "last_modified": "2026-04-20T10:30:00.000000",
    "total_size_bytes": 45678
  },
  "children": [
    {
      "name": "src",
      "type": "folder",
      "indexed": true,
      "file_count": 8,
      "last_modified": "2026-04-20T09:15:00.000000"
    },
    {
      "name": "tests",
      "type": "folder",
      "indexed": false,
      "file_count": 3,
      "last_modified": "2026-04-19T14:20:00.000000"
    },
    {
      "name": "README.md",
      "type": "file",
      "indexed": false,
      "size_bytes": 1234,
      "last_modified": "2026-04-15T14:20:00.000000"
    }
  ]
}
```

**Exit codes:**
- `0`: Success (indexed or unindexed folder, both valid)
- `1`: Folder doesn't exist
- `2`: Other errors (corrupted index, etc.)

### JavaScript Plugin: `facet-current.js`

**Slash command:**
```
/facet-current [<path>]
```

**Context resolution:**
1. Try to get active file from Claude Code API
2. If available, use its parent directory
3. Fallback: use working directory (`.`)
4. If user provides `<path>`, override with that
5. If all fail, show error: "Unable to determine folder context"

**Rendering:**
1. Call Python command with resolved path
2. Parse JSON response
3. Render UI block containing:
   - **Header:** Folder name + indexed status badge (✓ indexed / ⏳ pending)
   - **Metadata card** (if indexed):
     - Title, Type, Status, Team
     - Created/Updated dates
   - **Metadata card** (if not indexed):
     - "Pending indexing — run `facet index` to add metadata"
   - **Stats section:**
     - File count, Folder count
     - Last modified
     - Total size (human-readable: KB, MB, GB)
   - **Children list:**
     - Sortable by name/type
     - Indexed items highlighted with ✓
     - Folder icon + file icon
     - For folders: show child file count
     - For files: show size

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Folder doesn't exist | Fail with error message; exit code 1 |
| Folder exists, not indexed | Return metadata as `null`, mark `indexed: false`, show stats and children anyway |
| No context (no active file, no CWD, no override) | Use `.` as fallback; if that fails, show error |
| index.jsonl missing | Treat all folders as unindexed; still show filesystem stats |
| index.jsonl corrupted | Log warning; treat as missing; don't crash |

---

## Testing Strategy

**Python command tests:**
- Unit: path validation, root detection, JSON structure
- Integration: read real index.jsonl, walk real folder, verify stats accuracy
- Edge cases: empty folders, deeply nested, special characters, symlinks, permissions

**Plugin tests:**
- Context resolution: active file → CWD → override
- Subprocess invocation and output parsing
- UI rendering (mock JSON response)
- Error display (missing folder, unindexed, connection errors)

**End-to-end:**
- User types `/facet-current` with active file in indexed folder → shows full metadata
- User types `/facet-current /unindexed/folder` → shows pending status but still lists children
- User types `/facet-current /nonexistent` → shows error

---

## Implementation Notes

- **State:** No persistent state needed; command is stateless query
- **Performance:** Index lookup is O(n) scan; acceptable for typical folder counts (<10k entries)
- **Backward compatibility:** No breaking changes; pure addition to CLI and plugin ecosystem
- **Dependencies:** Reuses existing `index.jsonl` format and root detection logic from Phase 1.1

---

## Success Criteria

- [ ] `facet current-info` command correctly reads index and returns valid JSON
- [ ] Plugin resolves context correctly (3 modes: active file, CWD, override)
- [ ] UI renders metadata and children with proper visual hierarchy
- [ ] Error cases handled gracefully (unindexed folders still show content)
- [ ] All unit + integration tests pass
- [ ] Plugin tested manually with indexed and unindexed folders
