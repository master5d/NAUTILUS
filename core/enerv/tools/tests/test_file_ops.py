import os
import pytest
from pathlib import Path
from tools.core.file_ops import create_file_hidden, set_hidden

def test_create_file_hidden(tmp_path):
    """Test creating a file with hidden attribute on Windows."""
    file_path = tmp_path / "test.txt"

    create_file_hidden(file_path, content="test content")

    assert file_path.exists()
    assert file_path.read_text() == "test content"
    # On Windows, check hidden attribute; on Unix, no-op
    if os.name == 'nt':
        import ctypes
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
        assert attrs & 0x02  # FILE_ATTRIBUTE_HIDDEN

def test_set_hidden_existing_file(tmp_path):
    """Test setting hidden on existing file."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")

    set_hidden(file_path)

    assert file_path.exists()
    if os.name == 'nt':
        import ctypes
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
        assert attrs & 0x02
