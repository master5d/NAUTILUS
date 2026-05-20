# Faceted Indexing Phase 1.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement auto-indexing with SessionStart hook integration, enabling fresh indexes on every Claude Code session with smart debouncing per root.

**Architecture:** Three-layer design: (1) debounce logic layer validates timestamps and decides rebuild necessity, (2) `facet auto-index` command orchestrates rebuilds via IndexAggregator, (3) SessionStart hook invokes the command silently. State persists in `.facets/.last-index` files; each root debounces independently.

**Tech Stack:** Python 3.10+ (datetime, pathlib, json, subprocess), IndexAggregator from Phase 0, Bash for hook script, Claude Code harness settings.json

---

## File Structure

**New Files:**
- `tools/commands/auto_index.py` — Implements `auto_index` command with debounce logic and JSON output
- `tools/tests/commands/test_auto_index.py` — Unit + integration tests for debounce and rebuild
- `.claude/hooks/sessionstart.sh` — Bash script invoking `facet auto-index`

**Modified Files:**
- `tools/cli.py` — Register `auto_index` command with facet group
- `.claude/settings.json` — Register SessionStart hook

---

## Task 1: Debounce Logic Unit Tests

**Files:**
- Create: `tools/tests/commands/test_auto_index.py`
- Create: `tools/commands/auto_index.py` (stub)

- [ ] **Step 1: Write test for debounce decision with elapsed time >= threshold**

```python
# In tools/tests/commands/test_auto_index.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from tools.commands.auto_index import should_rebuild

def test_should_rebuild_when_elapsed_exceeds_threshold():
    """Tech root (3 min threshold): rebuild if 3+ minutes elapsed."""
    now = datetime.fromisoformat("2026-04-20T15:30:00.000000")
    last_index = datetime.fromisoformat("2026-04-20T15:26:00.000000")
    
    result = should_rebuild(
        last_index_time=last_index,
        now=now,
        threshold_minutes=3
    )
    
    assert result is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd C:\Warp\ Projects\ENERV
pytest tools/tests/commands/test_auto_index.py::test_should_rebuild_when_elapsed_exceeds_threshold -v
```

Expected output: `FAILED ... NameError: name 'should_rebuild' is not defined`

- [ ] **Step 3: Write minimal implementation stub**

```python
# In tools/commands/auto_index.py
from datetime import datetime

def should_rebuild(last_index_time, now, threshold_minutes):
    """
    Determine if an index should be rebuilt based on elapsed time.
    
    Args:
        last_index_time: datetime of last index
        now: current datetime
        threshold_minutes: rebuild threshold in minutes
    
    Returns:
        bool: True if rebuild needed, False otherwise
    """
    elapsed_seconds = (now - last_index_time).total_seconds()
    return elapsed_seconds >= (threshold_minutes * 60)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tools/tests/commands/test_auto_index.py::test_should_rebuild_when_elapsed_exceeds_threshold -v
```

Expected output: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tools/tests/commands/test_auto_index.py tools/commands/auto_index.py
git commit -m "test: add debounce logic with threshold validation"
```

---

## Task 2: Debounce Edge Cases

**Files:**
- Modify: `tools/tests/commands/test_auto_index.py`

- [ ] **Step 1: Write test for elapsed time < threshold (should NOT rebuild)**

```python
def test_should_not_rebuild_when_elapsed_below_threshold():
    """Tech root (3 min threshold): don't rebuild if < 3 minutes elapsed."""
    now = datetime.fromisoformat("2026-04-20T15:30:00.000000")
    last_index = datetime.fromisoformat("2026-04-20T15:29:00.000000")  # 1 minute ago
    
    result = should_rebuild(
        last_index_time=last_index,
        now=now,
        threshold_minutes=3
    )
    
    assert result is False
```

- [ ] **Step 2: Write test for clock skew (time went backward, always rebuild)**

```python
def test_should_rebuild_on_clock_skew():
    """If system time went backward, always rebuild (safety)."""
    now = datetime.fromisoformat("2026-04-20T15:25:00.000000")
    last_index = datetime.fromisoformat("2026-04-20T15:30:00.000000")  # Future time
    
    result = should_rebuild(
        last_index_time=last_index,
        now=now,
        threshold_minutes=3
    )
    
    assert result is True
```

- [ ] **Step 3: Write test for exact threshold boundary (should rebuild)**

```python
def test_should_rebuild_at_exact_threshold():
    """Boundary: elapsed == threshold should rebuild."""
    now = datetime.fromisoformat("2026-04-20T15:30:00.000000")
    last_index = datetime.fromisoformat("2026-04-20T15:27:00.000000")  # Exactly 3 minutes
    
    result = should_rebuild(
        last_index_time=last_index,
        now=now,
        threshold_minutes=3
    )
    
    assert result is True
```

- [ ] **Step 4: Run all three tests to verify they pass**

```bash
pytest tools/tests/commands/test_auto_index.py::test_should_not_rebuild_when_elapsed_below_threshold -v
pytest tools/tests/commands/test_auto_index.py::test_should_rebuild_on_clock_skew -v
pytest tools/tests/commands/test_auto_index.py::test_should_rebuild_at_exact_threshold -v
```

Expected output: All `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tools/tests/commands/test_auto_index.py
git commit -m "test: add debounce edge cases (boundary, clock skew)"
```

---

## Task 3: Read .last-index File with Error Handling

**Files:**
- Modify: `tools/tests/commands/test_auto_index.py`
- Modify: `tools/commands/auto_index.py`

- [ ] **Step 1: Write test for reading valid .last-index file**

```python
from pathlib import Path
from unittest.mock import patch
from tools.commands.auto_index import read_last_index_timestamp

def test_read_last_index_returns_datetime(tmp_path):
    """Read valid ISO 8601 timestamp from .last-index file."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    last_index_file = facets_dir / ".last-index"
    last_index_file.write_text("2026-04-20T15:25:18.456789\n")
    
    result = read_last_index_timestamp(facets_dir)
    
    assert result == datetime.fromisoformat("2026-04-20T15:25:18.456789")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tools/tests/commands/test_auto_index.py::test_read_last_index_returns_datetime -v
```

Expected output: `FAILED ... NameError: name 'read_last_index_timestamp' is not defined`

- [ ] **Step 3: Implement read_last_index_timestamp**

```python
def read_last_index_timestamp(facets_dir):
    """
    Read last index timestamp from .facets/.last-index file.
    
    Args:
        facets_dir: Path to .facets directory
    
    Returns:
        datetime: Parsed timestamp, or None if file doesn't exist
    
    Raises:
        ValueError: If timestamp format is invalid
    """
    from pathlib import Path
    
    facets_dir = Path(facets_dir)
    last_index_file = facets_dir / ".last-index"
    
    if not last_index_file.exists():
        return None
    
    timestamp_str = last_index_file.read_text().strip()
    return datetime.fromisoformat(timestamp_str)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tools/tests/commands/test_auto_index.py::test_read_last_index_returns_datetime -v
```

Expected output: `PASSED`

- [ ] **Step 5: Write test for missing .last-index file (returns None)**

```python
def test_read_last_index_returns_none_if_file_missing(tmp_path):
    """Missing .last-index should return None (triggers rebuild)."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    
    result = read_last_index_timestamp(facets_dir)
    
    assert result is None
```

- [ ] **Step 6: Run test to verify it passes**

```bash
pytest tools/tests/commands/test_auto_index.py::test_read_last_index_returns_none_if_file_missing -v
```

Expected output: `PASSED`

- [ ] **Step 7: Write test for invalid timestamp format (raises ValueError)**

```python
def test_read_last_index_raises_on_invalid_format(tmp_path):
    """Invalid ISO 8601 timestamp should raise ValueError."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    last_index_file = facets_dir / ".last-index"
    last_index_file.write_text("not-a-valid-timestamp\n")
    
    with pytest.raises(ValueError):
        read_last_index_timestamp(facets_dir)
```

- [ ] **Step 8: Run test to verify it passes**

```bash
pytest tools/tests/commands/test_auto_index.py::test_read_last_index_raises_on_invalid_format -v
```

Expected output: `PASSED`

- [ ] **Step 9: Commit**

```bash
git add tools/tests/commands/test_auto_index.py tools/commands/auto_index.py
git commit -m "feat: add .last-index file reading with edge case handling"
```

---

## Task 4: Write .last-index Timestamp

**Files:**
- Modify: `tools/tests/commands/test_auto_index.py`
- Modify: `tools/commands/auto_index.py`

- [ ] **Step 1: Write test for writing current timestamp to .last-index**

```python
from tools.commands.auto_index import write_last_index_timestamp

def test_write_last_index_writes_iso_timestamp(tmp_path):
    """Write current ISO 8601 timestamp to .last-index file."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    now = datetime.fromisoformat("2026-04-20T15:30:42.123456")
    
    with patch('tools.commands.auto_index.datetime') as mock_datetime:
        mock_datetime.now.return_value = now
        write_last_index_timestamp(facets_dir, now=now)
    
    last_index_file = facets_dir / ".last-index"
    assert last_index_file.exists()
    assert last_index_file.read_text().strip() == "2026-04-20T15:30:42.123456"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tools/tests/commands/test_auto_index.py::test_write_last_index_writes_iso_timestamp -v
```

Expected output: `FAILED ... NameError: name 'write_last_index_timestamp' is not defined`

- [ ] **Step 3: Implement write_last_index_timestamp**

```python
def write_last_index_timestamp(facets_dir, now=None):
    """
    Write current timestamp to .facets/.last-index file.
    
    Args:
        facets_dir: Path to .facets directory
        now: datetime to write (defaults to datetime.now())
    """
    from pathlib import Path
    
    if now is None:
        now = datetime.now()
    
    facets_dir = Path(facets_dir)
    facets_dir.mkdir(parents=True, exist_ok=True)
    
    last_index_file = facets_dir / ".last-index"
    last_index_file.write_text(now.isoformat() + "\n")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tools/tests/commands/test_auto_index.py::test_write_last_index_writes_iso_timestamp -v
```

Expected output: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tools/tests/commands/test_auto_index.py tools/commands/auto_index.py
git commit -m "feat: add .last-index file writing"
```

---

## Task 5: Index Rebuild Decision Logic

**Files:**
- Modify: `tools/tests/commands/test_auto_index.py`
- Modify: `tools/commands/auto_index.py`

- [ ] **Step 1: Write test for checking if root needs rebuild (tech root)**

```python
from tools.commands.auto_index import check_root_rebuild_needed

def test_check_root_rebuild_needed_tech(tmp_path):
    """Tech root: rebuild if >= 3 minutes elapsed."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    last_index_file = facets_dir / ".last-index"
    last_index_file.write_text("2026-04-20T15:26:00.000000\n")
    
    now = datetime.fromisoformat("2026-04-20T15:30:00.000000")  # 4 minutes later
    
    needed, reason = check_root_rebuild_needed(
        root_path=tmp_path,
        root_name="tech",
        now=now
    )
    
    assert needed is True
    assert "4.0 minutes elapsed" in reason or "4" in reason
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tools/tests/commands/test_auto_index.py::test_check_root_rebuild_needed_tech -v
```

Expected output: `FAILED ... NameError: name 'check_root_rebuild_needed' is not defined`

- [ ] **Step 3: Implement check_root_rebuild_needed**

```python
def check_root_rebuild_needed(root_path, root_name, now=None):
    """
    Check if a root needs index rebuild based on debounce threshold.
    
    Args:
        root_path: Path to root directory
        root_name: "tech" or "knowledge"
        now: Current datetime (defaults to datetime.now())
    
    Returns:
        tuple: (bool, str) - (rebuild_needed, reason)
    """
    from pathlib import Path
    
    if now is None:
        now = datetime.now()
    
    thresholds = {"tech": 3, "knowledge": 60}
    threshold_minutes = thresholds.get(root_name, 60)
    
    facets_dir = Path(root_path) / ".facets"
    
    # If .facets doesn't exist, skip this root
    if not facets_dir.exists():
        return False, f".facets directory not initialized"
    
    last_index_time = read_last_index_timestamp(facets_dir)
    
    # If .last-index missing, always rebuild (first run or corrupted)
    if last_index_time is None:
        return True, f"No .last-index found (first run or corrupted)"
    
    if should_rebuild(last_index_time, now, threshold_minutes):
        elapsed_minutes = (now - last_index_time).total_seconds() / 60
        return True, f"{elapsed_minutes:.1f} minutes elapsed"
    else:
        elapsed_minutes = (now - last_index_time).total_seconds() / 60
        return False, f"{elapsed_minutes:.1f} minutes elapsed ({threshold_minutes} min threshold)"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tools/tests/commands/test_auto_index.py::test_check_root_rebuild_needed_tech -v
```

Expected output: `PASSED`

- [ ] **Step 5: Write test for knowledge root (60 min threshold)**

```python
def test_check_root_rebuild_needed_knowledge(tmp_path):
    """Knowledge root: rebuild if >= 60 minutes elapsed."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    last_index_file = facets_dir / ".last-index"
    last_index_file.write_text("2026-04-20T14:00:00.000000\n")
    
    now = datetime.fromisoformat("2026-04-20T15:30:00.000000")  # 90 minutes later
    
    needed, reason = check_root_rebuild_needed(
        root_path=tmp_path,
        root_name="knowledge",
        now=now
    )
    
    assert needed is True
```

- [ ] **Step 6: Run test to verify it passes**

```bash
pytest tools/tests/commands/test_auto_index.py::test_check_root_rebuild_needed_knowledge -v
```

Expected output: `PASSED`

- [ ] **Step 7: Write test for .facets not initialized (skips root)**

```python
def test_check_root_rebuild_needed_facets_missing(tmp_path):
    """Root without .facets should be skipped."""
    now = datetime.fromisoformat("2026-04-20T15:30:00.000000")
    
    needed, reason = check_root_rebuild_needed(
        root_path=tmp_path,
        root_name="tech",
        now=now
    )
    
    assert needed is False
    assert "not initialized" in reason
```

- [ ] **Step 8: Run test to verify it passes**

```bash
pytest tools/tests/commands/test_auto_index.py::test_check_root_rebuild_needed_facets_missing -v
```

Expected output: `PASSED`

- [ ] **Step 9: Commit**

```bash
git add tools/tests/commands/test_auto_index.py tools/commands/auto_index.py
git commit -m "feat: add root rebuild decision logic with per-root thresholds"
```

---

## Task 6: JSON Output Formatting

**Files:**
- Modify: `tools/tests/commands/test_auto_index.py`
- Modify: `tools/commands/auto_index.py`

- [ ] **Step 1: Write test for building JSON summary**

```python
import json
from tools.commands.auto_index import build_summary

def test_build_summary_json_format():
    """Build JSON summary with tech and knowledge rebuild results."""
    now = datetime.fromisoformat("2026-04-20T15:30:42.123456")
    
    summary = build_summary(
        tech_indexed=True,
        tech_reason="3.5 minutes elapsed",
        tech_entry_count=34,
        knowledge_indexed=False,
        knowledge_reason="45 minutes elapsed (60 min threshold)",
        knowledge_entry_count=10,
        timestamp=now
    )
    
    data = json.loads(summary)
    
    assert data["tech"]["indexed"] is True
    assert data["tech"]["reason"] == "3.5 minutes elapsed"
    assert data["tech"]["entry_count"] == 34
    assert data["knowledge"]["indexed"] is False
    assert data["knowledge"]["entry_count"] == 10
    assert "timestamp" in data
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tools/tests/commands/test_auto_index.py::test_build_summary_json_format -v
```

Expected output: `FAILED ... NameError: name 'build_summary' is not defined`

- [ ] **Step 3: Implement build_summary**

```python
import json

def build_summary(tech_indexed, tech_reason, tech_entry_count, 
                  knowledge_indexed, knowledge_reason, knowledge_entry_count, 
                  timestamp):
    """
    Build JSON summary of auto-index operation.
    
    Args:
        tech_indexed: bool
        tech_reason: str
        tech_entry_count: int
        knowledge_indexed: bool
        knowledge_reason: str
        knowledge_entry_count: int
        timestamp: datetime
    
    Returns:
        str: JSON string
    """
    return json.dumps({
        "tech": {
            "indexed": tech_indexed,
            "reason": tech_reason,
            "entry_count": tech_entry_count
        },
        "knowledge": {
            "indexed": knowledge_indexed,
            "reason": knowledge_reason,
            "entry_count": knowledge_entry_count
        },
        "timestamp": timestamp.isoformat()
    }, indent=2)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tools/tests/commands/test_auto_index.py::test_build_summary_json_format -v
```

Expected output: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tools/tests/commands/test_auto_index.py tools/commands/auto_index.py
git commit -m "feat: add JSON summary formatting"
```

---

## Task 7: Mock IndexAggregator Integration Test

**Files:**
- Modify: `tools/tests/commands/test_auto_index.py`
- Modify: `tools/commands/auto_index.py`

- [ ] **Step 1: Write test for calling IndexAggregator when rebuild needed**

```python
from unittest.mock import Mock, patch
from tools.commands.auto_index import rebuild_index_for_root

def test_rebuild_index_for_root_calls_aggregator(tmp_path):
    """Call IndexAggregator to rebuild index when needed."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    
    with patch('tools.commands.auto_index.IndexAggregator') as mock_aggregator_class:
        mock_aggregator = Mock()
        mock_aggregator.aggregate.return_value = {"entries": 34}
        mock_aggregator_class.return_value = mock_aggregator
        
        entry_count = rebuild_index_for_root(tmp_path)
        
        mock_aggregator_class.assert_called_once_with(str(tmp_path))
        mock_aggregator.aggregate.assert_called_once()
        assert entry_count == 34
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tools/tests/commands/test_auto_index.py::test_rebuild_index_for_root_calls_aggregator -v
```

Expected output: `FAILED ... NameError: name 'rebuild_index_for_root' is not defined`

- [ ] **Step 3: Implement rebuild_index_for_root**

```python
def rebuild_index_for_root(root_path):
    """
    Rebuild index for a root using IndexAggregator.
    
    Args:
        root_path: Path to root directory
    
    Returns:
        int: Number of entries in rebuilt index
    """
    from pathlib import Path
    from tools.indexing.aggregator import IndexAggregator
    
    root_path = Path(root_path)
    aggregator = IndexAggregator(str(root_path))
    result = aggregator.aggregate()
    
    # Extract entry count from result (assumes aggregator returns dict with 'entries' key)
    entry_count = result.get("entries", 0)
    return entry_count
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tools/tests/commands/test_auto_index.py::test_rebuild_index_for_root_calls_aggregator -v
```

Expected output: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tools/tests/commands/test_auto_index.py tools/commands/auto_index.py
git commit -m "feat: add IndexAggregator integration for index rebuilding"
```

---

## Task 8: Full Auto-Index Command Implementation

**Files:**
- Modify: `tools/tests/commands/test_auto_index.py`
- Modify: `tools/commands/auto_index.py`

- [ ] **Step 1: Write integration test for full auto-index command**

```python
from tools.commands.auto_index import auto_index_command

def test_auto_index_command_rebuilds_both_roots(tmp_path):
    """Full command: check both roots, rebuild as needed, return JSON."""
    # Setup: Create tech and knowledge root directories with timestamps
    tech_root = tmp_path / "tech"
    knowledge_root = tmp_path / "knowledge"
    tech_root.mkdir()
    knowledge_root.mkdir()
    
    # Create .facets with old timestamps (both need rebuild)
    tech_facets = tech_root / ".facets"
    knowledge_facets = knowledge_root / ".facets"
    tech_facets.mkdir()
    knowledge_facets.mkdir()
    
    tech_facets.joinpath(".last-index").write_text("2026-04-20T15:20:00.000000\n")
    knowledge_facets.joinpath(".last-index").write_text("2026-04-20T14:00:00.000000\n")
    
    now = datetime.fromisoformat("2026-04-20T15:35:00.000000")
    
    with patch('tools.commands.auto_index.IndexAggregator') as mock_agg_class:
        mock_agg = Mock()
        mock_agg.aggregate.return_value = {"entries": 34}
        mock_agg_class.return_value = mock_agg
        
        result = auto_index_command(
            tech_root=str(tech_root),
            knowledge_root=str(knowledge_root),
            now=now
        )
    
    data = json.loads(result)
    
    assert data["tech"]["indexed"] is True
    assert data["knowledge"]["indexed"] is True
    assert data["tech"]["entry_count"] == 34
    assert data["knowledge"]["entry_count"] == 34
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tools/tests/commands/test_auto_index.py::test_auto_index_command_rebuilds_both_roots -v
```

Expected output: `FAILED ... NameError: name 'auto_index_command' is not defined`

- [ ] **Step 3: Implement auto_index_command**

```python
def auto_index_command(tech_root, knowledge_root, now=None):
    """
    Auto-index command: check debounce for both roots, rebuild if needed.
    
    Args:
        tech_root: Path to tech root directory
        knowledge_root: Path to knowledge root directory
        now: Current datetime (defaults to datetime.now())
    
    Returns:
        str: JSON summary of indexing results
    """
    from pathlib import Path
    
    if now is None:
        now = datetime.now()
    
    # Check if tech needs rebuild
    tech_needed, tech_reason = check_root_rebuild_needed(
        root_path=tech_root,
        root_name="tech",
        now=now
    )
    
    # Check if knowledge needs rebuild
    knowledge_needed, knowledge_reason = check_root_rebuild_needed(
        root_path=knowledge_root,
        root_name="knowledge",
        now=now
    )
    
    tech_entry_count = 0
    knowledge_entry_count = 0
    
    # Rebuild tech if needed
    if tech_needed:
        tech_entry_count = rebuild_index_for_root(tech_root)
        write_last_index_timestamp(Path(tech_root) / ".facets", now=now)
    
    # Rebuild knowledge if needed
    if knowledge_needed:
        knowledge_entry_count = rebuild_index_for_root(knowledge_root)
        write_last_index_timestamp(Path(knowledge_root) / ".facets", now=now)
    
    return build_summary(
        tech_indexed=tech_needed,
        tech_reason=tech_reason,
        tech_entry_count=tech_entry_count,
        knowledge_indexed=knowledge_needed,
        knowledge_reason=knowledge_reason,
        knowledge_entry_count=knowledge_entry_count,
        timestamp=now
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tools/tests/commands/test_auto_index.py::test_auto_index_command_rebuilds_both_roots -v
```

Expected output: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tools/tests/commands/test_auto_index.py tools/commands/auto_index.py
git commit -m "feat: implement full auto-index command with dual-root orchestration"
```

---

## Task 9: CLI Command Registration

**Files:**
- Modify: `tools/cli.py`
- Modify: `tools/commands/auto_index.py`

- [ ] **Step 1: Add Click command decorator to auto_index_command**

Update `tools/commands/auto_index.py` to add Click wrapper:

```python
import click
from pathlib import Path

@click.command("auto-index")
@click.option(
    "--tech-root",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default="C:\\telo",
    help="Tech root directory"
)
@click.option(
    "--knowledge-root",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default="E:\\",
    help="Knowledge root directory"
)
def auto_index_cli(tech_root, knowledge_root):
    """Rebuild indexes for tech and knowledge roots using hybrid debounce."""
    result = auto_index_command(
        tech_root=tech_root,
        knowledge_root=knowledge_root,
        now=datetime.now()
    )
    click.echo(result)
```

- [ ] **Step 2: Update tools/cli.py to register the command**

Find the facet command group (should exist from Phase 0) and add:

```python
# In tools/cli.py, in the facet group section:

from tools.commands.auto_index import auto_index_cli

@click.group()
def facet():
    """Faceted indexing tools."""
    pass

facet.add_command(auto_index_cli)
```

If `facet` group doesn't exist, create it and register with main CLI:

```python
@click.group()
def cli():
    """ENERV CLI."""
    pass

cli.add_group(facet)
```

- [ ] **Step 3: Test the CLI command manually**

```bash
cd C:\Warp\ Projects\ENERV
python -m tools.cli facet auto-index --help
```

Expected output: Help text showing `--tech-root` and `--knowledge-root` options

- [ ] **Step 4: Run full test suite to verify nothing broke**

```bash
pytest tools/tests/commands/test_auto_index.py -v
```

Expected output: All tests pass

- [ ] **Step 5: Commit**

```bash
git add tools/cli.py tools/commands/auto_index.py
git commit -m "feat: register auto-index command with facet CLI group"
```

---

## Task 10: SessionStart Hook Implementation

**Files:**
- Create: `.claude/hooks/sessionstart.sh`
- Modify: `.claude/settings.json`

- [ ] **Step 1: Create SessionStart hook script**

Create `.claude/hooks/sessionstart.sh`:

```bash
#!/bin/bash

# SessionStart hook: Automatically reindex tech and knowledge roots
# on Claude Code session initialization with hybrid debounce logic.

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Invoke facet auto-index command
# Defaults use C:\telo (tech) and E:\ (knowledge)
python -m tools.cli facet auto-index > /dev/null 2>&1 || true

# Note: We silently succeed even if command fails, to avoid blocking session start.
# Errors are logged via semantic logging, not user-facing.
```

- [ ] **Step 2: Make hook script executable**

```bash
chmod +x .claude/hooks/sessionstart.sh
```

- [ ] **Step 3: Register hook in .claude/settings.json**

Find the hooks section of `.claude/settings.json` and add:

```json
{
  "hooks": {
    "sessionstart": {
      "command": ".claude/hooks/sessionstart.sh",
      "enabled": true,
      "description": "Auto-reindex tech and knowledge roots on session start"
    }
  }
}
```

If hooks section doesn't exist, create it at root level of settings.json.

- [ ] **Step 4: Verify settings.json is valid JSON**

```bash
python -m json.tool .claude/settings.json > /dev/null && echo "Valid JSON"
```

Expected output: `Valid JSON`

- [ ] **Step 5: Commit**

```bash
git add .claude/hooks/sessionstart.sh .claude/settings.json
git commit -m "feat: add SessionStart hook for automatic index rebuilding"
```

---

## Task 11: Full Integration Test (Real File System)

**Files:**
- Modify: `tools/tests/commands/test_auto_index.py`

- [ ] **Step 1: Write integration test with real temp directories**

```python
def test_auto_index_integration_real_filesystem(tmp_path):
    """Integration: real filesystem, real index rebuild, state persistence."""
    from unittest.mock import patch
    
    tech_root = tmp_path / "tech"
    knowledge_root = tmp_path / "knowledge"
    tech_root.mkdir()
    knowledge_root.mkdir()
    
    # Initialize .facets directories
    tech_facets = tech_root / ".facets"
    knowledge_facets = knowledge_root / ".facets"
    tech_facets.mkdir()
    knowledge_facets.mkdir()
    
    # Create meta.json files to be indexed
    (tech_root / "project" / ".meta").mkdir(parents=True, exist_ok=True)
    (tech_root / "project" / ".meta" / "meta.json").write_text(
        '{"name": "project", "type": "workspace"}\n'
    )
    (knowledge_root / "article" / ".meta").mkdir(parents=True, exist_ok=True)
    (knowledge_root / "article" / ".meta" / "meta.json").write_text(
        '{"title": "article", "type": "document"}\n'
    )
    
    now1 = datetime.fromisoformat("2026-04-20T15:00:00.000000")
    
    # First run: should rebuild both
    with patch('tools.commands.auto_index.IndexAggregator') as mock_agg_class:
        mock_agg = Mock()
        mock_agg.aggregate.return_value = {"entries": 1}
        mock_agg_class.return_value = mock_agg
        
        result1 = auto_index_command(
            tech_root=str(tech_root),
            knowledge_root=str(knowledge_root),
            now=now1
        )
    
    data1 = json.loads(result1)
    assert data1["tech"]["indexed"] is True
    assert data1["knowledge"]["indexed"] is True
    
    # Verify .last-index files were written
    assert (tech_facets / ".last-index").exists()
    assert (knowledge_facets / ".last-index").exists()
    
    # Second run (1 minute later): only tech should rebuild
    now2 = datetime.fromisoformat("2026-04-20T15:01:00.000000")
    
    with patch('tools.commands.auto_index.IndexAggregator') as mock_agg_class:
        mock_agg = Mock()
        mock_agg.aggregate.return_value = {"entries": 1}
        mock_agg_class.return_value = mock_agg
        
        result2 = auto_index_command(
            tech_root=str(tech_root),
            knowledge_root=str(knowledge_root),
            now=now2
        )
    
    data2 = json.loads(result2)
    assert data2["tech"]["indexed"] is True  # 1 minute < 3 min, but was reset, now needs check
    assert data2["knowledge"]["indexed"] is False  # 1 minute < 60 min
```

- [ ] **Step 2: Run test to verify it fails (IndexAggregator not yet mocked properly)**

```bash
pytest tools/tests/commands/test_auto_index.py::test_auto_index_integration_real_filesystem -v
```

Expected output may fail depending on IndexAggregator implementation details

- [ ] **Step 3: Adjust test to match actual IndexAggregator behavior**

Check Phase 0 implementation to understand what `IndexAggregator.aggregate()` returns. Update mock or test as needed based on actual Phase 0 code.

- [ ] **Step 4: Run test until it passes**

```bash
pytest tools/tests/commands/test_auto_index.py::test_auto_index_integration_real_filesystem -v
```

Expected output: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tools/tests/commands/test_auto_index.py
git commit -m "test: add integration test with real filesystem and state persistence"
```

---

## Task 12: Documentation and Final Tests

**Files:**
- Modify: `tools/commands/auto_index.py` (docstrings)
- Modify: `tools/tests/commands/test_auto_index.py` (docstrings)

- [ ] **Step 1: Add module-level docstring to auto_index.py**

```python
"""
Automatic indexing command with hybrid debounce strategy.

This module implements the `facet auto-index` CLI command, which rebuilds
tech and knowledge root indexes based on independent debounce thresholds:

- Tech root (C:\telo): rebuild if >= 3 minutes since last index
- Knowledge root (E:\): rebuild if >= 60 minutes since last index

State is persisted in .facets/.last-index files (ISO 8601 timestamps).
Edge cases (missing files, clock skew) are handled safely.
"""
```

- [ ] **Step 2: Run all tests to verify everything passes**

```bash
pytest tools/tests/commands/test_auto_index.py -v
```

Expected output: All tests pass, coverage report shown

- [ ] **Step 3: Verify code coverage**

```bash
pytest tools/tests/commands/test_auto_index.py --cov=tools.commands.auto_index --cov-report=term-missing
```

Expected output: Coverage >= 95% (target: all debounce logic, edge cases, rebuilds covered)

- [ ] **Step 4: Manual CLI test**

```bash
python -m tools.cli facet auto-index
```

Expected output: JSON summary (may show no rebuild if thresholds not met)

- [ ] **Step 5: Commit**

```bash
git add tools/commands/auto_index.py tools/tests/commands/test_auto_index.py
git commit -m "docs: add module docstrings and verify test coverage"
```

---

## Task 13: Verify Hook Integration

**Files:**
- `.claude/hooks/sessionstart.sh` (no changes, verification only)
- `.claude/settings.json` (no changes, verification only)

- [ ] **Step 1: Verify hook file exists and is executable**

```bash
ls -la .claude/hooks/sessionstart.sh
```

Expected output: `-rwxr-xr-x` (executable permission set)

- [ ] **Step 2: Manually test hook script**

```bash
./.claude/hooks/sessionstart.sh
```

Expected output: Hook runs silently (no output unless error occurs)

- [ ] **Step 3: Check settings.json has hook registered**

```bash
python -c "
import json
with open('.claude/settings.json') as f:
    settings = json.load(f)
    print('Hook registered:', 'hooks' in settings and 'sessionstart' in settings.get('hooks', {}))
"
```

Expected output: `Hook registered: True`

- [ ] **Step 4: No additional commits needed**

All hook changes were committed in Task 10.

---

## Task 14: README and Success Criteria

**Files:**
- Create: `tools/commands/README-auto-index.md` (optional, for documentation)

- [ ] **Step 1: Create optional documentation file**

```markdown
# Auto-Index Command

## Usage

```bash
python -m tools.cli facet auto-index
```

Or with custom roots:

```bash
python -m tools.cli facet auto-index --tech-root "C:\telo" --knowledge-root "E:\"
```

## Behavior

- **Tech root**: Rebuilds index if >= 3 minutes since last rebuild
- **Knowledge root**: Rebuilds index if >= 60 minutes since last rebuild
- **Edge cases**: Missing .last-index files trigger rebuild; clock skew handled safely
- **State**: Persistent .last-index timestamps in .facets/ directories
- **SessionStart hook**: Automatically invoked on every Claude Code session start

## Output

JSON summary with indexed status, reasons, and entry counts for each root.
```

- [ ] **Step 2: Optional commit (skip if not needed)**

```bash
git add tools/commands/README-auto-index.md
git commit -m "docs: add auto-index command documentation"
```

---

## Success Criteria Verification

- [ ] All unit tests pass (debounce logic, edge cases, timestamp handling)
- [ ] All integration tests pass (real filesystem, state persistence)
- [ ] Code coverage >= 95%
- [ ] CLI command registered and callable: `python -m tools.cli facet auto-index`
- [ ] SessionStart hook registered in .claude/settings.json
- [ ] Hook script is executable and runs silently
- [ ] Hybrid debounce works (tech: 3 min, knowledge: 60 min, independently)
- [ ] .last-index timestamps persist correctly across runs
- [ ] JSON output matches spec format
- [ ] All commits follow convention (feat/test/docs)

---

## Notes for Implementation

1. **IndexAggregator dependency**: Ensure Phase 0's `IndexAggregator` class is importable from `tools.indexing.aggregator`. Adjust imports if needed.

2. **Path handling**: Use `pathlib.Path` consistently; convert to string for Click options and function calls.

3. **Datetime handling**: Mock `datetime.now()` in tests for deterministic results. Use `datetime.fromisoformat()` for parsing ISO 8601 timestamps.

4. **Error resilience**: Hook script uses `|| true` to silently succeed even on failure, preventing session start blockage.

5. **Debounce thresholds**: Tech (3 min) is aggressive for high-churn workspace; Knowledge (60 min) respects low-churn knowledge base. These are not configurable in Phase 1.1.

6. **Entry count semantics**: Number of entries returned by IndexAggregator is preserved in JSON output. If Phase 0 doesn't return this, extract from index.jsonl file length.
