# Faceted Indexing Phase 1, Sub-phase 1.1: Hook System + Auto-Indexing

> **Status:** Design approved — ready for implementation plan  
> **Date:** 2026-04-20  
> **Scope:** SessionStart hook + hybrid debounce auto-indexing for tech and knowledge roots

---

## Goal

Enable automatic index rebuilding on every Claude Code session start, with smart debouncing per root to balance freshness (tech) vs. resource efficiency (knowledge).

---

## Architecture

### Three Components

**1. New `facet auto-index` CLI Command** (extends Phase 0)

Reads both roots' `.last-index` timestamps, applies hybrid debounce logic, rebuilds indexes as needed.

**Behavior:**
- Reads `.facets/.last-index` from both `C:\telo\` and `E:\`
- Applies debounce thresholds:
  - Tech root: rebuild if ≥3 minutes since last index
  - Knowledge root: rebuild if ≥60 minutes since last index
- Rebuilds `index.jsonl` for roots that need it (calls existing `IndexAggregator`)
- Updates `.last-index` timestamp in each root's `.facets/` directory
- Returns JSON summary with indexing results

**Entry point:**
```
facet auto-index
```

**Output (JSON):**
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
  "timestamp": "2026-04-20T15:30:42.123456"
}
```

**2. SessionStart Hook** (Claude Code harness)

Invokes `facet auto-index` at session start.

**Behavior:**
- Runs `facet auto-index` on every Claude Code session initialization
- Parses JSON response (optional: cache result in memory for diagnostics)
- Silently succeeds — no user-facing output unless an error occurs
- If command fails, logs error to semantic log but does not block session start

**3. Debounce Strategy**

Each root manages its own debounce independently via `.last-index` timestamp file.

| Root | Debounce Threshold | Rationale |
|------|-------------------|-----------|
| Tech (`C:\telo\`) | 3 minutes | High churn, high value for agents; active development workspace |
| Knowledge (`E:\`) | 60 minutes | Low churn, knowledge changes slowly; no need for aggressive reindexing |

---

## Files to Create / Modify

### Phase 0 Extension (CLI)

- **Create:** `tools/commands/auto_index.py`
  - Implements `auto_index` command with hybrid debounce logic
  - Returns JSON summary

- **Modify:** `tools/cli.py`
  - Import and register `auto_index` command with facet group

### Phase 1 (Hooks)

- **Create:** `.claude/hooks/sessionstart.sh`
  - Bash script that invokes `facet auto-index`
  - Handles error cases gracefully

- **Modify:** `.claude/settings.json`
  - Register SessionStart hook with command and trigger condition

---

## Data Flow

```
┌─ SessionStart Event ──────────────────────┐
│                                            │
│  Hook: Run `facet auto-index`              │
│                                            │
│  ├─ Read .facets/.last-index (tech)       │
│  ├─ Read .facets/.last-index (knowledge)  │
│  │                                        │
│  ├─ Tech debounce check: ≥3 min?         │
│  ├─ Knowledge debounce check: ≥60 min?   │
│  │                                        │
│  ├─ IF tech needed:                       │
│  │   └─ Call IndexAggregator(tech_root)   │
│  │       └─ Scan meta.json files          │
│  │       └─ Write index.jsonl             │
│  │       └─ Update .last-index            │
│  │                                        │
│  ├─ IF knowledge needed:                  │
│  │   └─ Call IndexAggregator(knowledge)   │
│  │       └─ Scan meta.json files          │
│  │       └─ Write index.jsonl             │
│  │       └─ Update .last-index            │
│  │                                        │
│  └─ Return JSON summary                   │
│                                            │
└─ Hook logs result (optional) ──────────────┘
           ↓
    Session continues with fresh index
```

---

## Debounce Implementation Details

### `.last-index` File Format

ISO 8601 timestamp, one per line, written by `IndexAggregator`:
```
2026-04-20T15:25:18.456789
```

### Time Calculation

```python
now = datetime.now()
last_index_time = datetime.fromisoformat(last_index_str)
elapsed_seconds = (now - last_index_time).total_seconds()
should_rebuild = elapsed_seconds >= (threshold_minutes * 60)
```

### Threshold Values

- **Tech:** 3 minutes (180 seconds)
- **Knowledge:** 60 minutes (3,600 seconds)

### Edge Cases

- **Missing `.last-index` file:** Always rebuild (first-run or corrupted state)
- **Clock skew (system time jumped backward):** Rebuild anyway (safety)
- **`.facets/` doesn't exist:** Skip that root (not initialized yet)

---

## Testing Strategy

### Unit Tests
- Debounce logic: time calculations with mocked `datetime`
- Edge cases: missing files, clock skew, invalid timestamps
- JSON output format validation

### Integration Tests
- Hook invocation in mock Claude Code session
- Real index rebuild (creates/updates `index.jsonl`)
- Verifies `.last-index` timestamp written correctly

### Manual Testing
- Run `facet auto-index` manually, inspect output
- Start real Claude Code session, verify index updates
- Check tech and knowledge roots index independently

---

## Success Criteria

✅ `facet auto-index` command exists and runs without errors  
✅ Hybrid debounce logic works (tech 3min, knowledge 60min independently)  
✅ SessionStart hook runs automatically on session init  
✅ Index rebuilds only when thresholds elapsed  
✅ `.last-index` timestamp updates correctly  
✅ All tests pass (unit + integration)  
✅ No user-facing output in normal operation  

---

## Non-Goals (Phase 1.1)

- Schema validation (Phase 1.2+)
- Auto-migration of new folders (Phase 1.3)
- Claude Code plugin / slash commands (Phase 1.2)
- Knowledge auto-classification (Phase 2)

