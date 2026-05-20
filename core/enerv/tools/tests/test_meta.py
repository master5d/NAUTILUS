import json
import pytest
from pathlib import Path
from tools.core.meta import MetaFile

def test_meta_write_read(tmp_path):
    """Test writing and reading meta.json."""
    meta_path = tmp_path / "meta.json"

    meta_data = {
        "identifier": "proj-20260420-3f9a",
        "title": "Test Project",
        "type": "project",
        "status": "active",
        "created": "2026-04-20",
        "updated": "2026-04-20",
        "team": "ai"
    }

    MetaFile.write(meta_path, meta_data)

    assert meta_path.exists()
    loaded = MetaFile.read(meta_path)
    assert loaded["title"] == "Test Project"
    assert loaded["team"] == "ai"

def test_meta_write_sets_hidden(tmp_path):
    """Test that write() sets hidden attribute."""
    meta_path = tmp_path / "meta.json"
    meta_data = {"identifier": "test-20260420-0000", "title": "Test", "type": "topic"}

    MetaFile.write(meta_path, meta_data)

    import os
    if os.name == 'nt':
        import ctypes
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(meta_path))
        assert attrs & 0x02
