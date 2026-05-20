import json
import os
from pathlib import Path
from typing import List, Dict, Any


def get_current_root() -> Path:
    """Auto-detect current facet root from environment or filesystem."""
    # 1. Check environment variable
    if env_root := os.getenv('FACET_ROOT'):
        root = Path(env_root).resolve()
        if (root / '.facets').exists():
            return root
        raise ValueError(f"FACET_ROOT={env_root} exists but has no .facets directory")

    # 2. Check if current directory or parents contain .facets
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / '.facets').exists():
            return parent

    # 3. Check default roots
    defaults = [
        Path('C:\\telo'),
        Path('C:/telo'),
        Path('E:\\'),
        Path('E:/'),
    ]

    for default_root in defaults:
        root = default_root.resolve()
        if (root / '.facets').exists():
            return root

    # 4. Fail with helpful message
    raise ValueError(
        "No facet root found.\n\n"
        "To fix this:\n"
        "  1. Set FACET_ROOT=/path/to/root environment variable, OR\n"
        "  2. cd into a directory with .facets, OR\n"
        "  3. Make sure C:\\telo or E:\\ has .facets (initialize with 'facet init')"
    )


class ScopeConfig:
    """Parses scope.json to determine what the system indexes."""

    def __init__(self, root: str, whitelisted: List[Dict[str, Any]], ignored_patterns: List[str]):
        self.root = root
        self.whitelisted = whitelisted
        self.ignored_patterns = ignored_patterns

    @classmethod
    def load(cls, path: Path) -> "ScopeConfig":
        """Load scope.json from disk."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(
            root=data.get("root"),
            whitelisted=data.get("whitelisted", []),
            ignored_patterns=data.get("ignored_patterns", [])
        )

    def should_index(self, folder_name: str) -> bool:
        """Check if folder is whitelisted."""
        whitelisted_names = [w["name"] for w in self.whitelisted]
        return folder_name in whitelisted_names

    def get_default_confidentiality(self, folder_name: str) -> str:
        """Get default confidentiality for a whitelisted folder."""
        for w in self.whitelisted:
            if w["name"] == folder_name:
                return w.get("default_confidentiality", "personal")
        return "personal"
