import os
from pathlib import Path
from typing import Optional

FILE_ATTRIBUTE_HIDDEN = 0x02

def set_hidden(path: Path) -> None:
    """Set Windows hidden attribute on a file or directory.

    On non-Windows systems, this is a no-op.
    """
    if os.name == 'nt':
        import ctypes
        ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_HIDDEN)

def create_file_hidden(path: Path, content: str = "") -> None:
    """Create a file with hidden attribute (Windows) or leading dot (Unix convention).

    On Windows, sets hidden attribute after write.
    On Unix, renames to dotfile (not applicable here; we keep original names).
    """
    # If file exists and is hidden, temporarily unhide it to write
    if path.exists() and os.name == 'nt':
        import ctypes
        try:
            ctypes.windll.kernel32.SetFileAttributesW(str(path), 0x80)  # FILE_ATTRIBUTE_NORMAL
        except Exception:
            pass

    path.write_text(content)
    set_hidden(path)

def create_directory_hidden(path: Path) -> None:
    """Create a directory with hidden attribute."""
    path.mkdir(parents=True, exist_ok=True)
    set_hidden(path)
