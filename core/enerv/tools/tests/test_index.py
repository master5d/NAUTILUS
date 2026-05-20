import json
import time
import pytest
from pathlib import Path
from tools.core.index import IndexAggregator

def test_index_full_rebuild(tmp_path):
    """Test full index rebuild from folders."""
    root = tmp_path / "test_root"
    root.mkdir()

    # Create two folders with meta.json
    proj1 = root / "project__ai__active__test1"
    proj1.mkdir()
    (proj1 / "meta.json").write_text(json.dumps({
        "identifier": "proj-1", "title": "Test 1", "type": "project"
    }))

    proj2 = root / "project__ai__active__test2"
    proj2.mkdir()
    (proj2 / "meta.json").write_text(json.dumps({
        "identifier": "proj-2", "title": "Test 2", "type": "project"
    }))

    facets_dir = root / ".facets"
    facets_dir.mkdir()

    agg = IndexAggregator(root, facets_dir)
    agg.rebuild()

    index_file = facets_dir / "index.jsonl"
    assert index_file.exists()

    lines = index_file.read_text().strip().split('\n')
    assert len(lines) == 2

    entries = [json.loads(line) for line in lines]
    identifiers = {e["identifier"] for e in entries}
    assert identifiers == {"proj-1", "proj-2"}

def test_index_debounce(tmp_path):
    """Test that debounce skips rebuild if < 5 min."""
    root = tmp_path / "test_root"
    root.mkdir()
    facets_dir = root / ".facets"
    facets_dir.mkdir()

    agg = IndexAggregator(root, facets_dir, debounce_minutes=5)

    # First rebuild
    agg.rebuild()
    assert (facets_dir / ".last-index").exists()

    # Second rebuild immediately — should skip
    start_mtime = (facets_dir / "index.jsonl").stat().st_mtime
    time.sleep(0.1)  # brief wait
    agg.rebuild()
    end_mtime = (facets_dir / "index.jsonl").stat().st_mtime

    assert start_mtime == end_mtime  # not updated
