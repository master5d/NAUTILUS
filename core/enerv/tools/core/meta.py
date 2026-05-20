import json
from pathlib import Path
from typing import Dict, Any
from core.file_ops import set_hidden

class MetaFile:
    """Read/write meta.json files with hidden attribute."""

    @staticmethod
    def write(path: Path, data: Dict[str, Any]) -> None:
        """Write meta.json to disk and set hidden attribute."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        set_hidden(path)

    @staticmethod
    def read(path: Path) -> Dict[str, Any]:
        """Read meta.json from disk."""
        with open(path, 'r') as f:
            return json.load(f)

    @staticmethod
    def exists(path: Path) -> bool:
        """Check if meta.json exists."""
        return path.exists()
