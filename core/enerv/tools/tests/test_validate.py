import json
from pathlib import Path
from click.testing import CliRunner
from tools.tools.cli import facet


def test_validate_valid_tech_meta(tmp_path):
    """Test validate on valid tech meta.json."""
    runner = CliRunner()

    root = tmp_path / "tech"
    root.mkdir()
    (root / ".facets").mkdir()

    proj = root / "project__ai__active__test"
    proj.mkdir()
    (proj / "meta.json").write_text(json.dumps({
        "identifier": "proj-20260420-0000",
        "title": "Test",
        "type": "project",
        "status": "active",
        "created": "2026-04-20",
        "updated": "2026-04-20",
        "team": "ai"
    }))

    result = runner.invoke(facet, ['validate', '--root', str(root)])
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_validate_invalid_tech_meta(tmp_path):
    """Test validate on invalid tech meta.json."""
    runner = CliRunner()

    root = tmp_path / "tech"
    root.mkdir()
    (root / ".facets").mkdir()

    proj = root / "project__ai__active__test"
    proj.mkdir()
    # Missing required fields
    (proj / "meta.json").write_text(json.dumps({
        "identifier": "proj-20260420-0000",
        "title": "Test"
    }))

    result = runner.invoke(facet, ['validate', '--root', str(root)])
    assert result.exit_code == 1
    assert "failed" in result.output.lower()


def test_validate_valid_knowledge_meta(tmp_path):
    """Test validate on valid knowledge meta.json."""
    runner = CliRunner()

    root = tmp_path / "knowledge"
    root.mkdir()
    (root / ".facets").mkdir()

    vault = root / "vault__wellness__active__test"
    vault.mkdir()
    (vault / "meta.json").write_text(json.dumps({
        "identifier": "vault-20260420-0000",
        "title": "Test Vault",
        "type": "vault",
        "status": "active",
        "created": "2026-04-20",
        "updated": "2026-04-20",
        "subject_area": "wellness"
    }))

    result = runner.invoke(facet, ['validate', '--root', str(root)])
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_validate_multiple_files(tmp_path):
    """Test validate with multiple meta.json files."""
    runner = CliRunner()

    root = tmp_path / "tech"
    root.mkdir()
    (root / ".facets").mkdir()

    # Valid file
    proj1 = root / "project__ai__active__test1"
    proj1.mkdir()
    (proj1 / "meta.json").write_text(json.dumps({
        "identifier": "proj-20260420-0001",
        "title": "Test 1",
        "type": "project",
        "status": "active",
        "created": "2026-04-20",
        "updated": "2026-04-20"
    }))

    # Another valid file
    proj2 = root / "project__ai__active__test2"
    proj2.mkdir()
    (proj2 / "meta.json").write_text(json.dumps({
        "identifier": "proj-20260420-0002",
        "title": "Test 2",
        "type": "project",
        "status": "paused",
        "created": "2026-04-20",
        "updated": "2026-04-20"
    }))

    result = runner.invoke(facet, ['validate', '--root', str(root)])
    assert result.exit_code == 0
    assert "Valid: 2" in result.output


def test_validate_skips_facets_dir(tmp_path):
    """Test that validate skips .facets directory."""
    runner = CliRunner()

    root = tmp_path / "tech"
    root.mkdir()
    facets_dir = root / ".facets"
    facets_dir.mkdir()

    # Create invalid meta.json in .facets (should be skipped)
    (facets_dir / "meta.json").write_text(json.dumps({"invalid": "data"}))

    # Create valid meta.json in main root
    proj = root / "project__ai__active__test"
    proj.mkdir()
    (proj / "meta.json").write_text(json.dumps({
        "identifier": "proj-20260420-0000",
        "title": "Test",
        "type": "project",
        "status": "active",
        "created": "2026-04-20",
        "updated": "2026-04-20"
    }))

    result = runner.invoke(facet, ['validate', '--root', str(root)])
    assert result.exit_code == 0
    assert "Valid: 1" in result.output


def test_validate_invalid_json(tmp_path):
    """Test validate on malformed JSON."""
    runner = CliRunner()

    root = tmp_path / "tech"
    root.mkdir()
    (root / ".facets").mkdir()

    proj = root / "project__ai__active__test"
    proj.mkdir()
    (proj / "meta.json").write_text("{invalid json}")

    result = runner.invoke(facet, ['validate', '--root', str(root)])
    assert result.exit_code == 1
    assert "Invalid JSON" in result.output
