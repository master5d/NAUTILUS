import json
from pathlib import Path
from click.testing import CliRunner
from tools.tools.cli import facet

def test_migrate_with_batch_confirm(tmp_path):
    """Test migration of sample folders with batch mode."""
    runner = CliRunner()

    # Create root with .facets
    root = tmp_path / "tech"
    root.mkdir()
    facets_dir = root / ".facets"
    facets_dir.mkdir()
    (facets_dir / "operations.log").touch()
    (facets_dir / "index.jsonl").touch()

    # Create 3 sample folders without meta.json
    for i in range(3):
        proj = root / f"sample-project-{i}"
        proj.mkdir()
        (proj / "README.md").write_text("Sample content")

    result = runner.invoke(facet, ['migrate', '--root', str(root), '--batch-confirm', '--limit', '3'])

    assert result.exit_code == 0
    assert "Migrated 3 folders" in result.output
    assert "Index rebuilt" in result.output

    # Verify meta.json files were created
    for i in range(3):
        meta_file = root / f"sample-project-{i}" / "meta.json"
        assert meta_file.exists()

        meta = json.loads(meta_file.read_text())
        assert meta["type"] == "project"
        assert meta["team"] == "personal"
        assert meta["status"] == "active"
        assert meta["identifier"].startswith("pro-")

def test_migrate_no_facets_dir(tmp_path):
    """Test migration fails when .facets doesn't exist."""
    runner = CliRunner()
    root = tmp_path / "tech"
    root.mkdir()

    result = runner.invoke(facet, ['migrate', '--root', str(root)])

    assert result.exit_code == 1
    assert ".facets not found" in result.output

def test_migrate_skip_existing_meta(tmp_path):
    """Test that folders with meta.json are skipped."""
    runner = CliRunner()

    # Create root with .facets
    root = tmp_path / "tech"
    root.mkdir()
    facets_dir = root / ".facets"
    facets_dir.mkdir()
    (facets_dir / "operations.log").touch()
    (facets_dir / "index.jsonl").touch()

    # Create folder with meta.json (should be skipped)
    existing = root / "existing-project"
    existing.mkdir()
    existing_meta = {
        "identifier": "pro-20260420-0001",
        "title": "Existing Project",
        "type": "project",
        "status": "active",
        "created": "2026-04-20",
        "updated": "2026-04-20",
        "team": "ai"
    }
    (existing / "meta.json").write_text(json.dumps(existing_meta))

    # Create folder without meta.json (should be migrated)
    new_proj = root / "new-project"
    new_proj.mkdir()

    result = runner.invoke(facet, ['migrate', '--root', str(root), '--batch-confirm', '--limit', '5'])

    assert result.exit_code == 0
    assert "Migrated 1 folders" in result.output
    assert (new_proj / "meta.json").exists()

def test_migrate_knowledge_type(tmp_path):
    """Test migration with knowledge types (vault, topic, practice)."""
    runner = CliRunner()

    # Create root with .facets
    root = tmp_path / "knowledge"
    root.mkdir()
    facets_dir = root / ".facets"
    facets_dir.mkdir()
    (facets_dir / "operations.log").touch()
    (facets_dir / "index.jsonl").touch()

    # Create folder
    vault = root / "wellness-vault"
    vault.mkdir()

    # Simulate user input
    result = runner.invoke(facet, [
        'migrate',
        '--root', str(root),
        '--limit', '1'
    ], input='vault\nwellness\nactive\n')

    assert result.exit_code == 0
    assert "Migrated 1 folders" in result.output

    meta_file = vault / "meta.json"
    assert meta_file.exists()

    meta = json.loads(meta_file.read_text())
    assert meta["type"] == "vault"
    assert meta["subject_area"] == "wellness"

def test_migrate_limit_pilot(tmp_path):
    """Test that --limit restricts migration to pilot set."""
    runner = CliRunner()

    # Create root with .facets
    root = tmp_path / "tech"
    root.mkdir()
    facets_dir = root / ".facets"
    facets_dir.mkdir()
    (facets_dir / "operations.log").touch()
    (facets_dir / "index.jsonl").touch()

    # Create 10 sample folders
    for i in range(10):
        proj = root / f"project-{i:02d}"
        proj.mkdir()
        (proj / "README.md").write_text(f"Project {i}")

    result = runner.invoke(facet, [
        'migrate',
        '--root', str(root),
        '--batch-confirm',
        '--limit', '5'
    ])

    assert result.exit_code == 0
    assert "Migrated 5 folders" in result.output

    # Verify only 5 have meta.json
    count = 0
    for proj in root.iterdir():
        if proj.is_dir() and not proj.name.startswith('.'):
            if (proj / "meta.json").exists():
                count += 1

    assert count == 5
