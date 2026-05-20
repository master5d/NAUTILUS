import json
from pathlib import Path
from click.testing import CliRunner
from tools.tools.cli import facet

def test_index_rebuild(tmp_path):
    """Test facet index --force rebuild."""
    runner = CliRunner()

    root = tmp_path / "tech"
    root.mkdir()
    (root / ".facets").mkdir()

    # Create sample project
    proj = root / "project__ai__active__test"
    proj.mkdir()
    (proj / "meta.json").write_text(json.dumps({
        "identifier": "proj-1",
        "title": "Test",
        "type": "project"
    }))

    result = runner.invoke(facet, ['index', '--root', str(root), '--force'])

    assert result.exit_code == 0
    assert "indexed" in result.output.lower()

    # Verify index.jsonl created
    index_file = root / ".facets" / "index.jsonl"
    assert index_file.exists()
    lines = [l for l in index_file.read_text().strip().split('\n') if l]
    assert len(lines) == 1

def test_index_no_facets_dir(tmp_path):
    """Test index fails gracefully without .facets."""
    runner = CliRunner()

    root = tmp_path / "tech"
    root.mkdir()

    result = runner.invoke(facet, ['index', '--root', str(root)])

    assert result.exit_code == 1
    assert ".facets directory not found" in result.output
