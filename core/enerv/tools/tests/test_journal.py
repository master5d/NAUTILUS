import json
import pytest
from pathlib import Path
from tools.core.logging import SemanticLogger as OperationsJournal

def test_journal_append_operation(tmp_path):
    """Test appending operation to journal."""
    journal_file = tmp_path / "operations.log"

    journal = OperationsJournal(journal_file)
    journal.log_create("folder", str(tmp_path / "test_folder"), dry_run=False)

    assert journal_file.exists()
    lines = journal_file.read_text().strip().split('\n')
    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["operation"] == "create"
    assert entry["target"] == str(tmp_path / "test_folder")
    assert entry["dry_run"] == False
    assert "timestamp" in entry
