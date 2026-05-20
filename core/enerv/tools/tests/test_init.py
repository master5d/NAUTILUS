import json
import pytest
from pathlib import Path
from click.testing import CliRunner
from tools.tools.cli import facet

def test_init_tech_root(tmp_path):
    """Test facet init on tech root."""
    runner = CliRunner()
    root = tmp_path / "tech"
    root.mkdir()

    result = runner.invoke(facet, ['init', '--root', str(root), '--type', 'tech'])

    assert result.exit_code == 0
    assert "Initialized" in result.output

    # Check files created
    facets = root / ".facets"
    assert facets.exists()
    assert (facets / "schema.json").exists()
    assert (facets / "FACETS.md").exists()
    assert (facets / ".facetsignore").exists()
    assert (facets / "index.jsonl").exists()

    # Verify schema is correct
    schema = json.loads((facets / "schema.json").read_text())
    assert schema["title"] == "Tech Meta Schema"

    # Verify FACETS.md content
    facets_md = (facets / "FACETS.md").read_text()
    assert "FACETS Glossary — Tech Root" in facets_md
    assert "type" in facets_md
    assert "project, agent, micro, sandbox" in facets_md

    # Verify .facetsignore
    facetsignore = (facets / ".facetsignore").read_text()
    assert "$RECYCLE.BIN" in facetsignore

    # Verify index.jsonl is empty
    index_content = (facets / "index.jsonl").read_text()
    assert index_content == ""

def test_init_knowledge_root(tmp_path):
    """Test facet init on knowledge root."""
    runner = CliRunner()
    root = tmp_path / "knowledge"
    root.mkdir()

    result = runner.invoke(facet, ['init', '--root', str(root), '--type', 'knowledge'])

    assert result.exit_code == 0
    assert "Initialized" in result.output

    # Check files created
    facets = root / ".facets"
    assert facets.exists()
    assert (facets / "schema.json").exists()
    assert (facets / "FACETS.md").exists()
    assert (facets / ".facetsignore").exists()
    assert (facets / "index.jsonl").exists()

    # Verify schema is correct
    schema = json.loads((facets / "schema.json").read_text())
    assert schema["title"] == "Knowledge Meta Schema"

    # Verify FACETS.md content
    facets_md = (facets / "FACETS.md").read_text()
    assert "FACETS Glossary — Knowledge Root" in facets_md
    assert "vault, topic, practice" in facets_md

def test_init_already_exists(tmp_path):
    """Test facet init when .facets already exists."""
    runner = CliRunner()
    root = tmp_path / "tech"
    root.mkdir()
    (root / ".facets").mkdir()

    result = runner.invoke(facet, ['init', '--root', str(root), '--type', 'tech'])

    assert result.exit_code == 0
    assert ".facets already exists" in result.output
    assert "yellow" in result.output or "⚠️" in result.output

def test_init_without_root_option(tmp_path):
    """Test facet init without required --root option."""
    runner = CliRunner()

    result = runner.invoke(facet, ['init', '--type', 'tech'])

    # Should fail due to missing --root
    assert result.exit_code != 0
    assert "Missing option" in result.output or "requires an argument" in result.output.lower()

def test_init_with_invalid_type(tmp_path):
    """Test facet init with invalid root type."""
    runner = CliRunner()
    root = tmp_path / "tech"
    root.mkdir()

    result = runner.invoke(facet, ['init', '--root', str(root), '--type', 'invalid'])

    # Should fail due to invalid choice
    assert result.exit_code != 0
    assert "Invalid value for" in result.output or "invalid" in result.output.lower()
