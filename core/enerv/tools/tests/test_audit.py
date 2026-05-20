import json
from pathlib import Path
from click.testing import CliRunner
from tools.tools.cli import facet

def test_audit_tech_root(tmp_path):
    """Test facet audit on tech root."""
    runner = CliRunner()

    # Create mock tech root
    root = tmp_path / "tech"
    root.mkdir()
    (root / ".facets").mkdir()

    # Create sample project folder
    proj = root / "project__ai__active__test"
    proj.mkdir()
    (proj / "meta.json").write_text(json.dumps({
        "identifier": "proj-1",
        "title": "Test",
        "type": "project"
    }))

    result = runner.invoke(facet, ['audit', '--root', str(root)])

    assert result.exit_code == 0
    assert "Audit Report" in result.output
