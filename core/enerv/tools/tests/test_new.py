import json
import pytest
from pathlib import Path
from click.testing import CliRunner
from tools.tools.cli import facet

def test_new_project_dry_run(tmp_path):
    """Test facet new with --dry-run (no actual creation)."""
    runner = CliRunner()

    root = tmp_path / "tech"
    root.mkdir()

    result = runner.invoke(facet, [
        'new',
        'project',
        'ai',
        'active',
        'test-project',
        '--root', str(root),
        '--dry-run'
    ])

    assert result.exit_code == 0
    assert "Would create" in result.output

    # Verify folder NOT actually created
    assert not (root / "project__ai__active__test-project").exists()

def test_new_project_apply(tmp_path):
    """Test facet new with --apply (actually creates)."""
    runner = CliRunner()

    root = tmp_path / "tech"
    root.mkdir()
    (root / ".facets").mkdir()

    result = runner.invoke(facet, [
        'new',
        'project',
        'ai',
        'active',
        'test-project',
        '--root', str(root),
        '--apply'
    ])

    assert result.exit_code == 0
    assert "Creating" in result.output

    # Verify folder created
    folder = root / "project__ai__active__test-project"
    assert folder.exists()
    assert (folder / "meta.json").exists()

    # Verify meta.json is valid
    meta = json.loads((folder / "meta.json").read_text())
    assert meta["title"] == "Test Project"
    assert meta["type"] == "project"
    assert meta["status"] == "active"
    assert meta["team"] == "ai"
    assert meta["llm_context_priority"] == 5
    assert meta["evolutionary_links"] == []
    assert meta["dependencies"] == []

def test_new_knowledge_topic_apply(tmp_path):
    """Test facet new with knowledge type."""
    runner = CliRunner()

    root = tmp_path / "knowledge"
    root.mkdir()
    (root / ".facets").mkdir()

    result = runner.invoke(facet, [
        'new',
        'topic',
        'ai-safety',
        'active',
        'alignment-research',
        '--root', str(root),
        '--apply'
    ])

    assert result.exit_code == 0

    # Verify folder created with slug name (no prefix for knowledge types)
    folder = root / "alignment-research"
    assert folder.exists()
    assert (folder / "meta.json").exists()

    meta = json.loads((folder / "meta.json").read_text())
    assert meta["type"] == "topic"
    assert meta["subject_area"] == "ai-safety"
    assert meta["llm_context_priority"] == 5

def test_new_default_is_dry_run(tmp_path):
    """Test that default behavior is dry-run."""
    runner = CliRunner()

    root = tmp_path / "tech"
    root.mkdir()

    result = runner.invoke(facet, [
        'new',
        'project',
        'ai',
        'active',
        'test-project',
        '--root', str(root)
    ])

    assert result.exit_code == 0
    assert "Would create" in result.output
    assert not (root / "project__ai__active__test-project").exists()

def test_new_with_parent(tmp_path):
    """Test facet new with parent parameter."""
    runner = CliRunner()

    root = tmp_path / "tech"
    root.mkdir()
    (root / ".facets").mkdir()

    result = runner.invoke(facet, [
        'new',
        'micro',
        'ai',
        'active',
        'test-micro',
        '--root', str(root),
        '--parent', '/some/parent/path',
        '--apply'
    ])

    assert result.exit_code == 0

    folder = root / "micro__ai__active__test-micro"
    meta = json.loads((folder / "meta.json").read_text())
    assert meta["parent"] == "/some/parent/path"

def test_new_with_priority(tmp_path):
    """Test facet new with explicit priority."""
    runner = CliRunner()

    root = tmp_path / "tech"
    root.mkdir()
    (root / ".facets").mkdir()

    result = runner.invoke(facet, [
        'new',
        'project',
        'ai',
        'active',
        'test-priority',
        '--root', str(root),
        '--priority', '8',
        '--apply'
    ])

    assert result.exit_code == 0
    folder = root / "project__ai__active__test-priority"
    meta = json.loads((folder / "meta.json").read_text())
    assert meta["llm_context_priority"] == 8
