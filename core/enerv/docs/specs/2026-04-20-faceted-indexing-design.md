# Faceted Indexing System for telo & Knowledge Vault

- **Status:** Design approved — ready for implementation plan
- **Date:** 2026-04-20
- **Author:** Sasha (via Claude Code brainstorming session)
- **Scope:** Global indexing and organization of project folders across tech and knowledge domains

---

## 1. Context & Problem

telo currently holds 34 active folders with inconsistent naming conventions (mix of spaces, kebab-case, CamelCase, Cyrillic). A backlog of 100+ additional folders is planned, covering two distinct content classes:

- **Tech** — code projects, agents, micro-scripts, sandboxes (e.g., `embedding-agent`, `card-benefits-hub`, `WhisperDesk`)
- **Knowledge** — personal knowledge vaults, topics of study, practices (e.g., `Egypt Vault`, `Liver Flush`, `Юнгианский Подход`, `Каббала`)

Without a system:
- Agents cannot efficiently filter/rank projects by attributes
- No machine-readable metadata for CI/automation
- No inheritance of context from department/portfolio to child projects
- Cyrillic / free-form knowledge folders don't map cleanly to a faceted convention designed for code repos

## 2. Goals & Non-Goals

### Goals
1. **Agent-friendly search** — deterministic filtering by facets + semantic ranking
2. **CI / automation** — validated metadata, machine-readable schema, hook-driven updates
3. **Heterogeneous content support** — technical projects AND knowledge vaults under one conceptual system, two physical roots
4. **Preserve free-form knowledge folder names** — Cyrillic, spaces, human-readable stays intact
5. **Scalable to 150+ folders** with parent-chain inheritance for context reuse

### Non-Goals
- Not a replacement for git, Notion, or Obsidian — this is an indexing/metadata layer on top of the filesystem
- Not automatic semantic enrichment of existing content (Phase 2+)
- Not an attempt to unify content types into a single schema — dual schema is intentional

## 3. Architecture

### Two parallel roots

```
C:\telo\ENERV\ ← STANDALONE REPO (git-tracked)
├── .git/
├── README.md
├── docs/
│   ├── specs/                 ← this spec lives here
│   └── plans/                 ← implementation plans
├── tools/                     ← Python CLI package
│   ├── cli.py
│   ├── facet_new.py
│   ├── facet_classify.py
│   ├── facet_validate.py
│   ├── facet_index.py
│   ├── pyproject.toml
│   └── schemas/
│       ├── tech.schema.json
│       └── knowledge.schema.json
├── plugin/                    ← Claude Code plugin wrapper
│   ├── commands/              (slash commands)
│   ├── hooks/                 (SessionStart, Stop)
│   └── plugin.json
└── templates/                 ← canonical FACETS.md templates

C:/telo/              ← TECH root (strict naming)
├── .facets/
│   ├── FACETS.md              ← facet glossary (allowed values)
│   ├── schema.json            ← JSON Schema for tech meta.json
│   └── index.jsonl            ← aggregated index (one line per folder)
├── _portfolios/               ← portfolio containers (prefix _)
│   └── ai-development/
│       └── meta.json          (type: portfolio)
├── _departments/              ← department containers
│   └── ai/
│       └── meta.json          (type: department)
├── _tools/facet/              ← CLI tools live here
├── project__ai__active__card-benefits-hub/
│   └── meta.json              (parent: "_departments/ai")
├── agent__ai__active__cia-investigator/
│   └── meta.json
└── micro__personal__active__bio-reflection/
    └── meta.json

E:\                            ← KNOWLEDGE root (SHARED external drive, NOT dedicated)
├── .facets/                   ← isolated service directory (only location we write to)
│   ├── FACETS.md
│   ├── schema.json            ← knowledge schema (different from tech)
│   ├── scope.json             ← EXPLICIT whitelist of top-level dirs to index
│   ├── .facetsignore          ← exclude patterns (glob-style)
│   ├── index.jsonl            ← public index
│   ├── index-private.jsonl    ← private index (not synced, local only)
│   └── operations.log         ← audit trail of every write operation
│
│  ─── Whitelisted knowledge content (via scope.json) ───
├── Wellness & Biohacking/     ← existing; will be indexed as vault
├── Познание/                  ← existing; Cyrillic vault
├── DIGITAL LIBRARY/           ← existing; vault container
├── Client Cases/              ← existing; vault — flagged sensitive by default
├── LifeBook Vault/            ← migrated from C:\telo\
│
│  ─── NOT indexed (outside scope.json) ───
├── AI/                        (file collection — not knowledge entities)
├── Applications/              (installers)
├── Archived Files/            (opt-in later if needed)
├── Music Library/             (media)
├── Pictures/                  (media)
├── Video/                     (media)
├── $RECYCLE.BIN/              (Windows system — .facetsignore default)
└── System Volume Information/ (Windows system — .facetsignore default)
```

### Key architectural decisions
1. **Two physical roots** — `C:\telo\` (tech) and `E:\` (knowledge, shared drive) — each with its own `.facets/` directory. On shared drives, `scope.json` + `.facetsignore` restrict what the system touches — non-knowledge folders (Pictures, Music, Video, Applications, etc.) stay completely outside scope.
2. **Shared core schema** — identifier, title, type, status, created, updated, language, parent, tags
3. **Divergent extension schemas** per root (tech: team/tech/priority; knowledge: subject_area/source_type/modality/maturity)
4. **Reference-based parent inheritance** — child `meta.json` has `parent: "<path-relative-to-root>"` (e.g., `"_departments/ai"` in tech root, `"Wellness & Biohacking"` in knowledge root); agents resolve and merge at query time; `null` if no parent
5. **Aggregated index (`index.jsonl`)** — one JSON-line per folder; enables fast offline filtering without walking the tree
6. **`.facets/` directory** — single source of truth for schema, glossary, and index in each root

## 4. Meta.json Schema

### Common core (both roots)

```json
{
  "identifier": "proj-20260420-3f9a",
  "title": "Card Benefits Hub",
  "type": "project",
  "status": "active",
  "parent": "_departments/ai",
  "created": "2026-04-20",
  "updated": "2026-04-20",
  "language": ["en"],
  "tags": ["credit-cards", "ai-backend"]
}
```

**Required for all types:** `identifier`, `title`, `type`, `status`, `created`, `updated`

### Tech extensions

```json
{
  "team": "ai",
  "domain": ["fintech", "personal-finance"],
  "tech": ["nextjs", "vercel", "ai-sdk"],
  "priority": "P2",
  "confidentiality": "personal",
  "links": {
    "repo": "github.com/sasha/card-benefits-hub",
    "deploy": "https://...",
    "docs": "README.md"
  }
}
```

### Knowledge extensions

```json
{
  "subject_area": "wellness",
  "source_type": ["book", "course", "summit"],
  "modality": ["text", "audio", "video"],
  "maturity": "exploring",
  "links": {
    "notes": "notes.md",
    "sources": ["https://..."]
  }
}
```

### Entity types — required extensions matrix

| Type | Root | Required extras |
|---|---|---|
| `project` | tech | team, domain, tech |
| `agent` | tech | team, domain |
| `micro` | tech | — (core only) |
| `sandbox` | tech | — (core only) |
| `department` | tech | team |
| `portfolio` | tech | — |
| `vault` | knowledge | subject_area |
| `topic` | knowledge | subject_area, source_type |
| `practice` | knowledge | subject_area, modality, maturity |

### Identifier format

`<type-prefix>-<YYYYMMDD>-<4hex>`

Examples: `proj-20260420-3f9a`, `agent-20260420-a2c1`, `topic-20260420-8b1c`

- Unique across both roots
- Date segment = creation date
- 4-hex suffix = random, prevents collisions on same-day creation

## 5. Naming Conventions

### Tech root — strict faceted names

**Format:** `<type>__<team>__<status>__<slug>`

**Rules:**
- `type` ∈ {project, agent, micro, sandbox, department, portfolio} — matches `type` field in meta.json
- `team` — from glossary (ai, infra, research, wellness, personal, client-work, meta) — matches `team` field in meta.json
- `status` ∈ {active, paused, archive, sandbox, wip} — matches `status` field in meta.json
- `slug` — lowercase Latin, 2–4 words, kebab-case
- `__` (double underscore) separates facet part from slug
- `_departments/`, `_portfolios/` — underscore-prefixed service containers (entities of `type=department` / `type=portfolio`)

**Note:** `department` is both an entity type (container folder) and a conceptual grouping. The **folder name slot** uses `team` (the facet), not the entity type — they're separate concepts.

**Examples:**
```
project__ai__active__card-benefits-hub
project__infra__archive__old-lifebook
agent__ai__active__cia-investigator
micro__personal__active__bio-reflection
sandbox__ai__sandbox__llm-router-test
```

### Knowledge root — free-form names

**Format:** `<Human-Readable Name>` — as convenient

**Allowed:**
- Any characters (Cyrillic, spaces, uppercase)
- Length up to 80 characters

**Forbidden:**
- Windows-reserved: `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`

**Examples:**
```
Каббала/
Юнгианский Подход/
Liver Flush/
Body Electric Summit 2019/
Mayan Lunar Calendar Vault/
```

Facets are **not** encoded in the name — they live **only** in `meta.json`.

### Migration rule for existing 34 folders

- **Tech folders with English names** — renamed to faceted format (`card-benefits-hub` → `project__ai__active__card-benefits-hub`)
- **Folders with spaces/Cyrillic** — `facet_classify` script determines:
  - Contains `.git`, `package.json`, `*.ts/*.py/*.cs` → **tech root**, renamed
  - Contains mostly `.md`, pdf, media → **knowledge root**, name preserved

## 6. Facets Glossary (FACETS.md)

### Tech root

- **type:** `project`, `agent`, `micro`, `sandbox`, `department`, `portfolio`
- **status:** `active`, `paused`, `archive`, `sandbox`, `wip`
- **team / department:** `ai`, `infra`, `research`, `wellness`, `personal`, `client-work`, `meta`
- **domain:** array — open-ended (`fintech`, `personal-finance`, `healthcare`, `devtools`, `pkm`, `voice`, `mobile`, `web`, `neurodivergence`, …)
- **tech:** array — open-ended (`nextjs`, `react`, `nodejs`, `python`, `dotnet`, `wpf`, `ai-sdk`, `vercel`, `neo4j`, `serilog`, …)
- **priority:** `P0`, `P1`, `P2`, `P3`, `P4`
- **confidentiality:** `public`, `personal`, `internal`, `sensitive`

### Knowledge root

- **type:** `vault`, `topic`, `practice`
- **status:** `active`, `exploring`, `dormant`, `archive`
- **subject_area:** `wellness`, `biohacking`, `esoteric`, `metaphysics`, `psychology`, `psychotherapy`, `spirituality`, `personal-development`, `history`, `science`, `art`, `language`
- **source_type:** array — `book`, `course`, `summit`, `method`, `practice`, `lecture`, `podcast`, `video`, `article`, `experience`
- **modality:** array — `text`, `audio`, `video`, `experiential`, `ritual`, `meditation`, `bodywork`
- **maturity:** `exploring`, `learning`, `practicing`, `integrating`, `teaching`
- **language:** array — `en`, `ru`, `multi`

### Vocabulary policy

- **Closed** for categorical fields (type, status, subject_area, priority, confidentiality, maturity) — validated against enum
- **Open** for tag-like arrays (domain, tech, tags) — free additions allowed
- New closed-vocabulary value → PR edit to `FACETS.md` + `schema.json`
- Aliases supported for migration (e.g., `wellness-biohacking` → `biohacking`)

## 7. Automation & Tooling

### Distribution model: dual — standalone CLI + Claude Code plugin

The toolkit is packaged **two ways** from a single source (`ENERV/` repo), so it works across harnesses:

1. **Standalone Python CLI** — `pip install -e ./tools/` → `facet` binary available globally. Works in any shell/harness (Warp, VSCode terminal, Cursor, plain bash).
2. **Claude Code plugin** (`ENERV/plugin/`) — wraps the CLI as slash commands + hooks. Tight Claude Code integration:
   - `/facet-new`, `/facet-query`, `/facet-current`, `/facet-validate`
   - `SessionStart` hook → `facet index --incremental`
   - `Stop` hook → auto-bump `updated` for edited projects

### Tools source: `C:\telo\ENERV\tools\`

```
ENERV/tools/
├── cli.py                   # unified entry point (click-based)
├── facet_new.py             # create new folder + meta
├── facet_classify.py        # suggest classification for existing folder
├── facet_validate.py        # JSON Schema validation
├── facet_index.py           # rebuild .facets/index.jsonl
├── schemas/
│   ├── tech.schema.json
│   └── knowledge.schema.json
└── pyproject.toml           # deps: jsonschema, click, pyyaml
```

### 1. `facet-new` — create new folder

```bash
facet-new project ai active card-benefits-hub
# → creates C:/telo/project__ai__active__card-benefits-hub/
# → + meta.json with auto-filled identifier, created, updated
# → + 000-index.md template
```

Interactive mode for knowledge:
```bash
facet-new topic "Каббала" --root knowledge --parent "Esoteric"
# prompts for subject_area, source_type, modality
```

### 2. `facet-classify` — classify existing folder

Analyzes folder contents and suggests classification:
- `.git`, `package.json`, `*.ts/*.py/*.cs` → tech
- Mostly `.md`, pdf, media → knowledge
- Cyrillic + spaces in name → knowledge candidate
- Outputs suggested `meta.json` for review

### 3. `facet-validate` — JSON Schema validation

- Validates all `meta.json` against corresponding schema
- Checks required fields, enum values, parent path existence, identifier uniqueness
- Run manually or as pre-commit hook
- Failure → exit code 1 + readable report

### 4. `facet-index` — rebuild aggregated index

**Refresh policy: incremental + debounce 5min + manual force**

- **Default (hook-driven)** — `facet index` runs incrementally AND debounced:
  - Reads `.facets/.last-index` timestamp
  - If <5 minutes since last run → skip entirely (index considered fresh)
  - Else → walk root, compare folder mtimes against index, update only changed entries
- **Manual force** — `facet index --force` → full rebuild regardless of debounce/mtime
- **Incremental detail** — for each folder: if `folder mtime > index entry.updated` → re-read `meta.json`, update line in JSONL
- Updates `updated` field in each `meta.json` based on folder content mtime
- Writes `.facets/.last-index` (ISO timestamp) on success
- Optional Phase 2: embedding generation → `.facets/embeddings.parquet`

**Typical cost:**
- Debounced skip: <10ms
- Incremental (no changes): ~100ms for 150 folders
- Incremental (10 folders changed): ~200ms
- `--force` full rebuild: 1–3s for 150 folders

### 5. Hook integration

- **SessionStart hook** — `facet-index --incremental` (fast, updates before agent starts)
- **Stop hook** — if agent edited files under `<project>/`, bump `updated` in that `meta.json`

### 6. `facet` — unified query CLI (agent-facing)

```bash
facet query --root tech --type project --team ai --status active
facet query --root knowledge --subject-area psychology --language ru
facet resolve proj-20260420-3f9a           # → full path + merged meta
facet resolve --with-parents proj-...       # → child + parent chain merged
facet related proj-20260420-3f9a           # → siblings by team/domain
facet set proj-20260420-3f9a status archive # → atomic update + rename (tech)
```

JSON output by default — easy to parse in tool calls.

## 8. Agent Integration

### Discovery flow

1. **Facet filter (fast, <50ms)** — read `index.jsonl`, apply filters → candidate list
2. **Semantic rank (optional)** — `embedding-agent` integration, rerank candidates by query relevance
3. **Deep dive** — agent reads `000-index.md` + `README.md` for top-N only

### Context injection

- `.claude/commands/facet-current.md` — slash command showing `meta.json` for cwd
- `UserPromptSubmit` hook — if cwd inside a known project, inject `meta.json` (~200 tokens)
- `MEMORY.md` — reference entry pointing to `.facets/FACETS.md` in each root

### Safety & confidentiality

**Default policy:** new items are created with `confidentiality: personal` (user's private machine, not for public sharing but indexed normally).

**Sensitive upgrade:** user manually sets `confidentiality: sensitive` on individual items as they identify them (ad-hoc, no automatic rules). Typical candidates:
- Personal therapy notes / shadow work / trauma material
- Medical diagnoses, health records
- Financial details with real identifiers
- Personal journal entries
- Any topic user wants hidden from agent-driven global search

**Index split:**
- `.facets/index.jsonl` (public) — excludes items where `confidentiality == "sensitive"`
- `.facets/index-private.jsonl` (gitignored, local only) — contains everything
- Agents in public contexts (GitHub triage, shared sessions) see public index only
- Agents on user's local machine can opt-in to private index with explicit `--include-private` flag

**No automatic classification** — user reviews and tags sensitive items explicitly over time. Avoids false positives that would incorrectly hide useful content.

## 9. Roadmap & Phasing

### Phase 0 — MVP (Week 1)
- Create `.facets/` directories in both roots
- Write `FACETS.md` and `schema.json` for both roots
- Implement `facet_new.py`, `facet_validate.py`, `facet_index.py`
- Migrate 5–10 tech projects as pilot
- Validation confirms schema correctness on pilot set

### Phase 1 — Full tech migration (Week 2)
- Implement `facet_classify.py`
- Migrate all 34 tech folders
- Migrate first 10 knowledge folders
- Install SessionStart + Stop hooks
- Add `/facet-current` slash command

### Phase 2 — Semantic layer (Week 3+)
- Integrate `embedding-agent` for ranking
- Implement parent-chain resolution (`facet resolve --with-parents`)
- Split public/private indices

### Phase 3 — Bulk knowledge migration (ongoing)
- Batch-classify 100+ knowledge folders
- Optional dashboard for visual overview

## 10. Safety Guarantees

The system operates on shared drives (`C:\` contains unrelated software; `E:\` contains media, applications, and personal archives). Safety is a first-class design requirement.

### Hard guarantees (written into the toolkit)

1. **No delete operations, ever.** The toolkit has zero `rm`, `unlink`, `shutil.rmtree` calls. Archived items get `status: archive` in their `meta.json`; the folder stays. Removal is user-driven through native OS tools.

2. **No modification of non-meta files.** The toolkit only writes to:
   - `.facets/*` (service directory)
   - `meta.json` inside whitelisted folders
   - `000-index.md` (only if created by `facet-new`; never overwrites existing)
   
   User `.md`, pdf, media, source code, configs are read-only from the system's perspective.

3. **Explicit scope via `scope.json`.** On `E:\`, the system indexes ONLY folders listed in `.facets/scope.json`. Everything outside (`Pictures/`, `Music Library/`, etc.) is invisible to the tool. Adding a new top-level folder to the scope is explicit user action.

4. **`.facetsignore` defaults for Windows.** Auto-excluded patterns: `$RECYCLE.BIN/`, `System Volume Information/`, `~*`, `$*`, `Thumbs.db`, `.DS_Store`.

5. **Dry-run is the default for first 30 days.** `facet-new`, `facet-classify`, migration operations run with `--dry-run` by default. Real writes require explicit `--apply`. Config flag `FACET_DEFAULT_DRYRUN` in `.facets/config.json` controls this.

6. **Operations journal (`.facets/operations.log`).** Every write operation appends a JSONL entry: `{timestamp, operation, target, before_snapshot, after_snapshot}`. Enables full audit and manual rollback.

7. **No automatic renaming of existing folders.** Migration of 34 tech folders is a **separate, interactive command** (`facet migrate`) that shows a preview diff and requires explicit per-folder (or `--batch-confirm`) user approval. Knowledge folders are never renamed — names stay free-form.

8. **Pre-flight audit command.** `facet audit` is a pure-read command that reports current state (what's scoped, what's ignored, what has meta.json, what's orphaned) without making changes. **Always runnable; always safe.**

9. **Per-folder default confidentiality.** `scope.json` supports `default_confidentiality` per top-level entry — propagated to all descendant `meta.json` files on creation. `Client Cases/` gets `sensitive` by default so client data never enters the public index by accident.

10. **Hidden-by-default on creation (Windows).** Every file the toolkit creates gets the Windows hidden attribute (`attrib +h` via `SetFileAttributesW`) so user's Explorer view stays clean:
    - `.facets/` — hidden at root level
    - `meta.json` — hidden inside every folder where created
    - `000-index.md` — hidden
    - Applied atomically as part of the create operation (one syscall after `write`)
    - CLI, terminal, git, IDE all see these files normally (hidden is Explorer-only)
    - Reversible with `attrib -h` at any time; toolkit also provides `facet unhide <path>` helper
    - On non-Windows (rare for this user) — no-op; files are already hidden by dotfile convention if renamed (out of scope for Phase 0)

### Recommended first-use flow

```bash
# Day 1 — read-only exploration
facet audit --root knowledge          # see what's on E:\ and what's in scope
facet audit --root tech               # see current tech layout

# Day 1 — scope decision
facet scope add "Wellness & Biohacking" --root knowledge
facet scope add "Познание" --root knowledge
# ... one at a time, user reviews each

# Day 2+ — dry-run experiments
facet new project ai active test-project --dry-run  # previews, does nothing
facet classify "Some Existing Folder" --dry-run     # suggests classification

# When ready — apply
facet new project ai active real-project --apply
```

### Recovery

If anything goes wrong:
- `operations.log` contains every action with timestamps and before/after — manually reversible
- `.facets/migration-backup.json` (created by `facet migrate`) stores original folder names before batch rename
- Git history of `ENERV/` repo tracks changes to schema/scope/tooling itself
- No state outside `.facets/` directory and `meta.json` files — nuke `.facets/` and everything returns to original filesystem state (except any renames, which migration-backup reverses)

### What this system is NOT

- Not a backup system — doesn't duplicate your files
- Not a sync system — doesn't upload anywhere
- Not a cleanup tool — doesn't delete or move files
- Not a live file watcher — only runs when invoked (hooks, CLI, or manual)

## 11. Decisions Log

All open questions from initial brainstorming have been resolved:

| # | Question | Decision | Date |
|---|---|---|---|
| 1 | Knowledge root location | `E:\` (external storage drive) | 2026-04-20 |
| 2 | Existing `LifeBook Vault` | Migrates into knowledge root at `E:\LifeBook Vault\` | 2026-04-20 |
| 3 | Sensitive subject areas — default list | No automatic rules. User tags items `confidentiality: sensitive` ad-hoc as they identify them. New items default to `personal`. | 2026-04-20 |
| 4 | Tool packaging | Dual: standalone Python CLI (`pip install`) + Claude Code plugin wrapper. Single source in `ENERV/` repo. Works across harnesses (Warp, Claude Code, VSCode, Cursor). | 2026-04-20 |
| 5 | Index refresh strategy | Incremental + 5-minute debounce on hook-driven runs + `--force` flag for manual full rebuild. `.facets/.last-index` tracks timestamp. | 2026-04-20 |
| 6 | Git tracking scope | Single standalone repo `C:\telo\ENERV\` containing tooling, docs, schemas, and plugin. Not tracking the tech/knowledge roots themselves (they have their own sub-repos where applicable). | 2026-04-20 |
| 7 | `Client Cases/` confidentiality | **Auto-flagged `confidentiality: sensitive` by default** during initial scope setup. `scope.json` entry includes `"default_confidentiality": "sensitive"` for this folder. All descendants inherit unless explicitly overridden. | 2026-04-20 |
| 8 | Meta storage strategy | **Option A for both roots**: `meta.json` lives inside each folder (data locality, meta travels with folder on move/rename). Windows hidden attribute applied on creation so Explorer view stays clean. Rejected Option B (centralized entries) to keep meta and content together. | 2026-04-20 |

## 12. Success Criteria

- All 34 existing tech projects have valid `meta.json` conforming to schema
- `facet query` returns results in <100ms on full index
- Agent can filter `type=project AND team=ai AND status=active` deterministically
- Knowledge folders with Cyrillic names preserved; metadata in `meta.json` only
- Pre-commit validation catches schema violations before index corruption
- Hook-driven `updated` bumps work correctly across multi-file agent edits
