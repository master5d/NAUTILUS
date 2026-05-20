# Migration Lessons Learned & Repo Improvements
## Real-World Testing Revealed Critical Gaps

**Date:** 2026-04-22  
**Scope:** embedding-agent migration test + facet-current skill validation  
**Status:** 8 major issues identified, 3 categories of improvements needed

---

## Errors Encountered During Migration

### 1. ❌ Incorrect CLI Interface Documentation

**What Happened:**
- SKILL.md documented: `facet new --path "..." --title "..." --type project`
- Actual CLI requires: `facet new [TYPE] [TEAM] [STATUS] [SLUG] --root ROOT --apply`
- Result: Command failed immediately with confusing error

**Root Cause:**
- Documentation was aspirational (designed but not implemented)
- OR CLI interface changed without updating docs
- No test coverage to validate documentation accuracy

**Impact:** Users following SKILL.md would hit immediate failure when trying to index a new project.

---

### 2. ❌ Commands Requiring --root with No Default

**What Happened:**
```bash
facet index --force  # ❌ Failed: Missing option '--root'
facet index --root "C:\telo" --force  # ✅ Success
```

- `facet index` requires explicit `--root`
- `facet audit` requires explicit `--root`
- No default to current directory or environment variable

**Root Cause:**
- CLI designed for multi-root support but no "current root" tracking
- No sensible default when only one root exists (C:\telo)

**Impact:** Verbose commands, easy to forget, common user error.

---

### 3. ❌ Index Not Auto-Updated After meta.json Creation

**What Happened:**
1. Created `.facets/meta.json` manually
2. Ran `facet current-info` → still showed `indexed: false`
3. Ran `facet index --force`
4. Ran `facet current-info` again → STILL showed `indexed: false`

**Root Cause:**
- Index build ran (printed "✅ Indexed 12 entries") but embedding-agent wasn't included
- No cache invalidation or timestamp checking
- Unclear if index actually re-scanned the directory or used stale state

**Impact:** User confusion about whether migration worked. No feedback about what was indexed.

---

### 4. ❌ Corrupted index.jsonl with Silent Failures

**What Happened:**
- Last entry in index.jsonl was: `{"File-Date": "2024-05-16"}`
- Should be a facet folder entry
- Caused JSON parsing errors but no warnings

**Root Cause:**
- Unknown what caused this entry to be written
- No validation on index.jsonl structure
- No cleanup/recovery mechanism

**Impact:** Could silently corrupt the entire index over time.

---

### 5. ❌ Path Handling Breaks Across bash/Windows

**What Happened:**
```bash
# Windows paths need escaping
"C:\telo\embedding-agent"  # ✓ Works in some contexts
"C:\\telo\\embedding-agent"  # ✓ Works in JSON
C:\telo\embedding-agent  # ✗ Breaks in bash
```

- Different escaping needed for bash vs Python vs JSON
- No normalization utility
- Easy to accidentally break cross-platform users

**Root Cause:**
- No path abstraction layer
- CLI uses raw strings without normalization

**Impact:** Hard to debug path errors, docs have to show multiple formats.

---

### 6. ❌ Silent Validation Failures

**What Happened:**
- Created meta.json file with correct schema
- File existed on disk but index didn't pick it up
- No error message, no warning, no indication of problem

**Root Cause:**
- No pre-indexing validation of meta.json files
- No per-file indexing feedback
- Index runs silently

**Impact:** Users don't know if migration actually worked until they test it.

---

### 7. ❌ Confusing facet migrate Behavior

**What Happened:**
```bash
facet migrate --root "C:\telo" --limit 1 --batch-confirm
# Result: Migrated "bio" folder, not "embedding-agent"
```

- `--limit 1` migrated the *first* folder it found, not the one I wanted
- No way to target a specific folder
- Result was unexpected

**Root Cause:**
- `--limit` is a crude pilot/test feature
- No folder selection mechanism
- Processed in arbitrary order (filesystem iteration order)

**Impact:** Users can't reliably migrate a specific folder.

---

### 8. ❌ Missing Error Context in Failure Messages

**What Happened:**
```
subprocess.CalledProcessError: Command '['facet', 'new', '--path', ...]' 
returned non-zero exit status 2.
```

- Exit code 2 but no message about what failed
- Had to run command manually to see the actual error

**Root Cause:**
- CLI error messages not captured/propagated
- MCP server doesn't add context to errors

**Impact:** Hard to debug, users stuck without clear next steps.

---

## Improvements Needed (By Priority)

### CRITICAL: Fix CLI Interface (P0)

**Problem:** Documentation doesn't match implementation  
**Fix:** Update either:
- Option A: Update SKILL.md to show correct `facet new` syntax with all required arguments
- Option B: Refactor `facet new` to support `--path --title` interface for easier usage

**Recommendation:** **Option B** — The current interface (`facet new project ai active embedding-agent --root ...`) is hard to use. Create an alias or new command:

```bash
# Current (hard to use)
facet new project ai active embedding-agent --root C:\Warp --apply

# Better (what SKILL.md promised)
facet new --path C:\Warp\embedding-agent --title "Embedding Agent" --type project --apply
```

**Implementation Location:** `tools/tools/commands/new.py`

```python
@click.command()
@click.option('--path', required=True, help='Path to folder')
@click.option('--title', required=True, help='Human-readable title')
@click.option('--type', type=click.Choice([...]), required=True)
@click.option('--team', default='ai', help='Team or area')
@click.option('--status', default='active', help='Status')
@click.option('--apply', is_flag=True, help='Actually create (not dry-run)')
def new_friendly(path, title, type, team, status, apply):
    """Create new folder with metadata (user-friendly interface)."""
    # Convert to current internal format
    slug = slugify(title)
    # ... rest of implementation
```

---

### CRITICAL: Add Smart Root Defaults (P0)

**Problem:** Every command requires `--root`, but only one root exists  
**Fix:** Implement root auto-detection:

1. **Check environment:** `FACET_ROOT` env var
2. **Check current directory:** Is `.facets/` in current dir or parent?
3. **Use default:** `C:\telo` (or `E:\` for knowledge root)
4. **Fail with helpful error:** "No facet root found. Set FACET_ROOT or cd into a root directory"

**Implementation Location:** `tools/tools/core/config.py` (new file)

```python
def get_current_root() -> Path:
    """Auto-detect current facet root."""
    # 1. Check env var
    if env_root := os.getenv('FACET_ROOT'):
        return Path(env_root)
    
    # 2. Check if .facets exists in cwd or parents
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / '.facets').exists():
            return parent
    
    # 3. Use default (must be first initialized root)
    default_root = Path('C:\\telo')
    if (default_root / '.facets').exists():
        return default_root
    
    raise click.ClickException(
        "No facet root found.\n"
        "Set FACET_ROOT=/path/to/root or cd into a root directory.\n"
        "Or initialize: facet init /path/to/root"
    )
```

**Update All Commands:**
```python
# Before
@click.command()
@click.option('--root', required=True, type=Path)
def index(root):
    pass

# After
@click.command()
@click.option('--root', type=Path, default=None)
def index(root):
    root = root or get_current_root()
    ...
```

---

### CRITICAL: Validate Before Indexing (P0)

**Problem:** Silent failures when meta.json is created but not indexed  
**Fix:** Add a validation step that:
1. Checks all meta.json files against schema
2. Reports which folders will be indexed
3. Reports any validation errors *before* indexing

**Implementation Location:** `tools/tools/commands/validate.py` (enhance existing)

```python
def validate_and_index(root: Path) -> dict:
    """Validate all meta.json files, then index with feedback."""
    # 1. Validate all meta.json files
    valid_count = 0
    invalid = []
    
    for meta_file in root.rglob('meta.json'):
        try:
            with open(meta_file) as f:
                data = json.load(f)
            schema.validate(data)
            valid_count += 1
            print(f"✓ {meta_file.parent.name}: {data['title']}")
        except (json.JSONDecodeError, ValidationError) as e:
            invalid.append((meta_file, str(e)))
            print(f"✗ {meta_file.parent.name}: {e}")
    
    # 2. Report results
    if invalid:
        raise click.ClickException(
            f"Validation failed: {len(invalid)} files have errors.\n"
            "Fix the errors above, then run `facet index` again."
        )
    
    # 3. Only then index
    print(f"\n✅ All {valid_count} meta.json files are valid.")
    print("Rebuilding index...")
    # ... run index build
    
    return {
        'indexed_count': valid_count,
        'errors': len(invalid),
        'status': 'success' if not invalid else 'failed'
    }
```

---

### HIGH: Improve Error Messages (P1)

**Problem:** Exit code 2 with no context  
**Fix:** Catch exceptions and wrap with helpful context

**Implementation Location:** `tools/tools/mcp_server.py`

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> ToolResult:
    try:
        # ... run command
        result = subprocess.run([...], capture_output=True, text=True, check=True)
        return ToolResult(content=[...], isError=False)
    except subprocess.CalledProcessError as e:
        # Capture the actual error message
        error_msg = e.stderr or e.stdout or f"Exit code {e.returncode}"
        return ToolResult(
            content=[TextContent(
                type="text",
                text=f"❌ {name} failed:\n{error_msg}\n\n"
                     f"Try: {get_help_suggestion(name)}"
            )],
            isError=True
        )
```

---

### HIGH: Add Migration Workflow Guide (P1)

**Problem:** No clear step-by-step guide for "migrate existing project"  
**Fix:** Create a migration helper command and guide

**Implementation Location:** `tools/tools/commands/migrate.py` (enhance)

```python
@click.command()
@click.option('--folder', required=True, help='Folder to migrate')
@click.option('--title', help='Project title (auto-derived if omitted)')
@click.option('--type', default='project')
@click.option('--apply', is_flag=True)
def migrate_single(folder, title, type, apply):
    """Migrate a single existing folder to the index."""
    folder_path = Path(folder).resolve()
    
    if not folder_path.exists():
        raise click.ClickException(f"Folder not found: {folder_path}")
    
    # Auto-derive title from folder name
    title = title or folder_path.name
    
    # Create metadata
    meta = {
        'path': str(folder_path),
        'identifier': generate_id(),
        'title': title,
        'type': type,
        'status': 'active',
        'team': 'general',
        'created': datetime.now().isoformat(),
        'updated': datetime.now().isoformat(),
    }
    
    if not apply:
        click.echo("Dry-run mode. Would create:")
        click.echo(json.dumps(meta, indent=2))
        return
    
    # Create .facets/meta.json
    meta_file = folder_path / '.facets' / 'meta.json'
    meta_file.parent.mkdir(exist_ok=True)
    meta_file.write_text(json.dumps(meta, indent=2))
    
    # Validate and index
    root = get_current_root()
    validate_and_index(root)
    
    click.echo(f"\n✅ Migrated {title} (ID: {meta['identifier']})")
```

---

### MEDIUM: Fix Path Normalization (P2)

**Problem:** Inconsistent path handling  
**Fix:** Create a path utility that normalizes across platforms

**Implementation Location:** `tools/tools/core/paths.py` (new file)

```python
from pathlib import Path
from typing import Union

def normalize_path(path: Union[str, Path]) -> Path:
    """Normalize path for current platform."""
    if isinstance(path, str):
        # Handle Windows UNC paths, env vars, etc.
        path = Path(path).expanduser().resolve()
    return path

def to_absolute(path: Union[str, Path], root: Path = None) -> Path:
    """Convert to absolute path, relative to root if provided."""
    path = normalize_path(path)
    if not path.is_absolute() and root:
        path = root / path
    return path
```

Then use consistently:
```python
# Before
meta_path = folder_path / '.facets' / 'meta.json'

# After
meta_path = normalize_path(folder_path) / '.facets' / 'meta.json'
```

---

### MEDIUM: Add Index Integrity Checks (P2)

**Problem:** Corrupted index.jsonl ({"File-Date": ...} entry)  
**Fix:** Add validation and recovery

**Implementation Location:** `tools/tools/core/index.py` (enhance)

```python
def validate_index(index_file: Path) -> dict:
    """Validate index.jsonl structure."""
    issues = []
    valid_entries = 0
    
    with open(index_file) as f:
        for line_no, line in enumerate(f, 1):
            try:
                entry = json.loads(line)
                # Check required fields
                if 'identifier' not in entry or 'path' not in entry:
                    issues.append(
                        f"Line {line_no}: Missing required field (identifier, path)"
                    )
                else:
                    valid_entries += 1
            except json.JSONDecodeError:
                issues.append(f"Line {line_no}: Invalid JSON")
    
    return {
        'valid_entries': valid_entries,
        'issues': issues,
        'needs_rebuild': len(issues) > 0
    }

def repair_index(root: Path):
    """Rebuild corrupted index."""
    index_file = root / '.facets' / 'index.jsonl'
    
    # Backup original
    import shutil
    backup = index_file.with_suffix('.jsonl.backup')
    shutil.copy(index_file, backup)
    click.echo(f"Backed up to: {backup}")
    
    # Rebuild fresh
    rebuild_index(root)
    click.echo("✅ Index rebuilt from meta.json files")
```

---

### MEDIUM: Add Logging & Verbosity (P2)

**Problem:** Silent operation makes debugging hard  
**Fix:** Add structured logging with --verbose flag

**Implementation Location:** `tools/tools/cli.py`

```python
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--log-file', type=click.Path(), help='Log to file')
def cli(verbose, log_file):
    """Facet CLI."""
    from .core.logging import setup_logging
    setup_logging(verbose=verbose, log_file=log_file)

# Then in commands:
import logging
logger = logging.getLogger(__name__)

@click.command()
def index():
    logger.debug("Starting index rebuild")
    logger.info(f"Found {n} meta.json files")
    logger.debug(f"Processing: {file}")
    logger.info(f"Indexed {count} folders")
```

---

### MEDIUM: Add Testing for Migration Workflow (P2)

**Problem:** No tests for real-world migration scenario  
**Fix:** Add integration tests

**Implementation Location:** `tools/tests/test_migration.py` (new file)

```python
def test_migrate_single_folder(tmp_path):
    """Test migrating an unindexed folder."""
    root = tmp_path / 'root'
    root.mkdir()
    project = root / 'my-project'
    project.mkdir()
    
    # Initialize root
    facet_init(root)
    
    # Verify unindexed
    info = facet_current_info(project)
    assert info['indexed'] is False
    
    # Migrate
    facet_migrate_single(
        project,
        title='My Project',
        apply=True
    )
    
    # Verify indexed
    info = facet_current_info(project)
    assert info['indexed'] is True
    assert info['metadata']['title'] == 'My Project'
    assert (project / '.facets' / 'meta.json').exists()

def test_validate_before_index(tmp_path):
    """Validation should catch bad meta.json."""
    # Create bad meta.json
    meta_file.write_text('{"invalid": }')
    
    # Validation should fail
    result = validate_index(root)
    assert result['status'] == 'failed'
    assert len(result['errors']) > 0

def test_path_normalization():
    """Paths should work consistently."""
    # Windows path
    assert normalize_path('C:\\telo').as_posix() == 'c:\\warp projects'
    
    # Relative path
    assert normalize_path('./folder').is_absolute()
    
    # UNC path
    assert normalize_path('//server/share').is_absolute()
```

---

## Summary of Changes Needed

| Issue | Severity | Fix | File | Effort |
|-------|----------|-----|------|--------|
| CLI interface mismatch | P0 | Refactor `facet new` | `commands/new.py` | 4h |
| Missing --root defaults | P0 | Add auto-detection | `core/config.py` | 2h |
| Silent validation failures | P0 | Pre-index validation | `commands/validate.py` | 3h |
| Bad error messages | P1 | Wrap with context | `mcp_server.py` | 2h |
| No migration guide | P1 | Add helper command | `commands/migrate.py` | 3h |
| Path handling issues | P2 | Normalize paths | `core/paths.py` | 2h |
| Index corruption | P2 | Add integrity checks | `core/index.py` | 2h |
| No logging | P2 | Add structured logging | `cli.py` | 2h |
| No tests | P2 | Integration tests | `tests/test_migration.py` | 4h |

**Total Effort:** ~24 hours (3 days of focused work)

---

## Immediate Actions (Before Next Use)

1. ✅ **Document actual CLI syntax** in SKILL.md
2. ✅ **Add --root defaults** to top 3 commands (index, audit, current-info)
3. ✅ **Add validation before indexing** (catch obvious errors early)
4. ✅ **Update error messages** in MCP server

These 4 changes would have prevented 5 out of 8 errors in this migration test.

---

## Conclusion

The ENERV has solid foundational design but needs:
- **Better ergonomics** (smart defaults, clearer commands)
- **Better feedback** (validation, error messages, logging)
- **Better reliability** (path handling, index integrity, testing)

Investing in these improvements will make the system production-ready and reduce friction for both direct CLI users and skill-based integration (Claude Code).
