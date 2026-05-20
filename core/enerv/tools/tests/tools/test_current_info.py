import pytest
import json
from pathlib import Path
from tools.commands.current_info import validate_folder_path, detect_root, lookup_metadata_in_index, calculate_folder_stats


def test_validate_folder_path_exists():
    """Existing folder passes validation."""
    tmp_path = Path(__file__).parent
    result = validate_folder_path(str(tmp_path))
    assert result == tmp_path


def test_validate_folder_path_missing():
    """Non-existent folder raises ValueError."""
    with pytest.raises(ValueError, match="Folder not found"):
        validate_folder_path("/nonexistent/path/xyz")


def test_detect_root_tech():
    """Folders under C:\\telo\\ resolve to tech root."""
    path = Path("C:/telo/some-project/src")
    root, root_name = detect_root(path)

    assert root == Path("C:/telo").resolve()
    assert root_name == "tech"


def test_detect_root_knowledge():
    """Folders under E:\\ resolve to knowledge root."""
    path = Path("E:/my-knowledge/topic")
    root, root_name = detect_root(path)

    assert root == Path("E:/").resolve()
    assert root_name == "knowledge"


def test_detect_root_unknown():
    """Folder outside known roots raises ValueError."""
    with pytest.raises(ValueError, match="not under a known root"):
        detect_root(Path("/usr/local"))


def test_lookup_indexed_folder(tmp_path):
    """Find folder metadata in index.jsonl."""
    # Create mock index.jsonl
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    index_file = facets_dir / "index.jsonl"

    folder_path = tmp_path / "my-project"
    folder_path.mkdir()

    # Write index entry
    entry = {
        "path": str(folder_path),
        "identifier": "proj-20260420-1234",
        "title": "My Project",
        "type": "project",
        "status": "active",
        "team": "ai",
        "created": "2026-04-20",
        "updated": "2026-04-20"
    }
    index_file.write_text(json.dumps(entry) + "\n")

    # Lookup
    result = lookup_metadata_in_index(folder_path, facets_dir)

    assert result is not None
    assert result["title"] == "My Project"
    assert result["identifier"] == "proj-20260420-1234"


def test_lookup_unindexed_folder(tmp_path):
    """Return None for folder not in index."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    index_file = facets_dir / "index.jsonl"

    # Empty index
    index_file.write_text("")

    folder_path = tmp_path / "unindexed"
    folder_path.mkdir()

    result = lookup_metadata_in_index(folder_path, facets_dir)
    assert result is None


def test_calculate_folder_stats(tmp_path):
    """Calculate file count, folder count, size, last-modified."""
    # Create test structure
    folder = tmp_path / "test-folder"
    folder.mkdir()
    (folder / "file1.txt").write_text("content")
    (folder / "file2.py").write_text("more content")
    subfolder = folder / "subfolder"
    subfolder.mkdir()
    (subfolder / "nested.md").write_text("nested")

    stats = calculate_folder_stats(folder)

    assert stats["file_count"] == 2  # immediate children files
    assert stats["folder_count"] == 1  # immediate children folders
    assert stats["total_size_bytes"] > 0
    assert "last_modified" in stats
    assert "T" in stats["last_modified"]  # ISO format has T


def test_calculate_folder_stats_empty(tmp_path):
    """Empty folder returns zero counts."""
    empty = tmp_path / "empty"
    empty.mkdir()

    stats = calculate_folder_stats(empty)

    assert stats["file_count"] == 0
    assert stats["folder_count"] == 0
    assert stats["total_size_bytes"] == 0


def test_enumerate_children_with_index_status(tmp_path):
    """List children and mark which are indexed."""
    from tools.commands.current_info import enumerate_children

    # Setup structure
    folder = tmp_path / "parent"
    folder.mkdir()
    (folder / "indexed-file.txt").write_text("content")
    indexed_subfolder = folder / "indexed-subfolder"
    indexed_subfolder.mkdir()
    unindexed_subfolder = folder / "unindexed"
    unindexed_subfolder.mkdir()

    # Create index
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    index_file = facets_dir / "index.jsonl"
    indexed_entry = {
        "path": str(indexed_subfolder.resolve()),
        "identifier": "sub-1234",
        "title": "Indexed Subfolder",
        "type": "topic"
    }
    index_file.write_text(json.dumps(indexed_entry) + "\n")

    # Enumerate
    children = enumerate_children(folder, facets_dir)

    assert len(children) == 3
    indexed_child = [c for c in children if c["name"] == "indexed-subfolder"][0]
    assert indexed_child["indexed"] is True
    unindexed_child = [c for c in children if c["name"] == "unindexed"][0]
    assert unindexed_child["indexed"] is False
    file_child = [c for c in children if c["name"] == "indexed-file.txt"][0]
    assert file_child["type"] == "file"


def test_build_output_indexed(tmp_path):
    """Build output with indexed metadata."""
    from tools.commands.current_info import build_output

    # Setup structure
    folder = tmp_path / "indexed-folder"
    folder.mkdir()
    (folder / "file.txt").write_text("content")

    # Create index
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    index_file = facets_dir / "index.jsonl"
    metadata = {
        "path": str(folder.resolve()),
        "identifier": "proj-1234",
        "title": "My Project",
        "type": "project"
    }
    index_file.write_text(json.dumps(metadata) + "\n")

    # Build output
    output = build_output(folder, facets_dir, metadata)

    assert output["path"] == str(folder.resolve())
    assert output["indexed"] is True
    assert output["metadata"] is not None
    assert output["metadata"]["title"] == "My Project"
    assert "stats" in output
    assert "children" in output
    assert isinstance(output["children"], list)


def test_build_output_unindexed(tmp_path):
    """Build output without metadata."""
    from tools.commands.current_info import build_output

    # Setup structure
    folder = tmp_path / "unindexed-folder"
    folder.mkdir()

    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()

    # Build output with no metadata
    output = build_output(folder, facets_dir, metadata=None)

    assert output["path"] == str(folder.resolve())
    assert output["indexed"] is False
    assert output["metadata"] is None
    assert "stats" in output
    assert "children" in output


def test_current_info_cli_command_success(tmp_path, monkeypatch):
    """CLI command succeeds with valid folder."""
    from click.testing import CliRunner
    from tools.commands.current_info import current_info_cli

    # Setup structure under tmp_path
    folder = tmp_path / "test-folder"
    folder.mkdir()
    (folder / "file.txt").write_text("content")

    # Create index with metadata
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    index_file = facets_dir / "index.jsonl"
    metadata = {
        "path": str(folder.resolve()),
        "identifier": "proj-1234",
        "title": "Test Project",
        "type": "project"
    }
    index_file.write_text(json.dumps(metadata) + "\n")

    # Mock detect_root to return tmp_path as root
    from tools.commands import current_info
    original_detect_root = current_info.detect_root
    monkeypatch.setattr(current_info, "detect_root", lambda p: (tmp_path, "tech"))

    try:
        # Run CLI
        runner = CliRunner()
        result = runner.invoke(current_info_cli, [str(folder)])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        output_json = json.loads(result.output)
        assert output_json["indexed"] is True
        assert output_json["path"] == str(folder.resolve())
    finally:
        monkeypatch.setattr(current_info, "detect_root", original_detect_root)


def test_current_info_cli_command_missing_folder():
    """CLI command fails for missing folder."""
    from click.testing import CliRunner
    from tools.commands.current_info import current_info_cli

    runner = CliRunner()
    result = runner.invoke(current_info_cli, ["/nonexistent/path"])

    # Click validation exits with code 2
    assert result.exit_code != 0
    assert "does not exist" in result.output or "error" in result.output


def test_enumerate_children_with_corrupted_index(tmp_path):
    """Gracefully handle corrupted index.jsonl."""
    from tools.commands.current_info import enumerate_children

    # Setup structure
    folder = tmp_path / "parent"
    folder.mkdir()
    (folder / "file.txt").write_text("content")

    # Create corrupted index
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    index_file = facets_dir / "index.jsonl"
    index_file.write_text("{invalid json}\n")

    # Enumerate should not crash
    children = enumerate_children(folder, facets_dir)

    assert len(children) == 1
    assert children[0]["name"] == "file.txt"
    assert children[0]["indexed"] is False


def test_enumerate_children_missing_facets_dir(tmp_path):
    """Gracefully handle missing .facets directory."""
    from tools.commands.current_info import enumerate_children

    # Setup structure
    folder = tmp_path / "parent"
    folder.mkdir()
    (folder / "file.txt").write_text("content")

    facets_dir = tmp_path / ".facets"
    # Don't create facets_dir

    # Enumerate should not crash
    children = enumerate_children(folder, facets_dir)

    assert len(children) == 1
    assert children[0]["name"] == "file.txt"
    assert children[0]["indexed"] is False


def test_enumerate_children_special_characters(tmp_path):
    """Handle children with special characters in names."""
    from tools.commands.current_info import enumerate_children

    # Setup structure with special characters
    folder = tmp_path / "parent"
    folder.mkdir()
    (folder / "file with spaces.txt").write_text("content")
    (folder / "file-with-dashes.py").write_text("code")
    (folder / "file_with_underscores.md").write_text("markdown")

    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    index_file = facets_dir / "index.jsonl"
    index_file.write_text("")

    # Enumerate should handle all names
    children = enumerate_children(folder, facets_dir)

    assert len(children) == 3
    names = [c["name"] for c in children]
    assert "file with spaces.txt" in names
    assert "file-with-dashes.py" in names
    assert "file_with_underscores.md" in names
