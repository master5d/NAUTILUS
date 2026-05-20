import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from core.meta import MetaFile
from core.file_ops import create_file_hidden

class IndexAggregator:
    """Aggregates meta.json files into index.jsonl with incremental + debounce."""

    def __init__(self, root: Path, facets_dir: Path, debounce_minutes: int = 5):
        self.root = root
        self.facets_dir = facets_dir
        self.debounce_minutes = debounce_minutes
        self.index_file = facets_dir / "index.jsonl"
        self.last_index_file = facets_dir / ".last-index"

    def should_rebuild(self) -> bool:
        """Check if rebuild is needed based on debounce."""
        if not self.last_index_file.exists():
            return True

        last_index_time = self.last_index_file.read_text().strip()
        last_time = datetime.fromisoformat(last_index_time)
        now = datetime.now()

        return (now - last_time).total_seconds() >= (self.debounce_minutes * 60)

    def rebuild(self, force: bool = False) -> None:
        """Rebuild index from all meta.json files in root."""
        if not force and not self.should_rebuild():
            return  # Skip, debounced

        entries = []

        # Optimizing walk: avoid heavy directories
        # We manually walk to have better control over errors and skipped dirs
        def safe_walk(current_path: Path):
            try:
                for item in current_path.iterdir():
                    if not item.is_dir():
                        if item.name == "meta.json" and item.parent != self.facets_dir:
                            try:
                                meta = MetaFile.read(item)
                                if any(f in meta for f in ["name", "project", "title", "identifier"]):
                                    entries.append(meta)
                            except Exception:
                                pass
                        continue
                    
                    # Skip noise and system dirs
                    if item.name in [".git", "node_modules", ".next", ".claude", "venv", ".venv"]:
                        continue
                        
                    yield from safe_walk(item)
            except OSError:
                pass # Access Denied or other system error

        # Start recursive safe walk
        list(safe_walk(self.root))

        # Write index.jsonl
        index_content = "\n".join(json.dumps(e) for e in entries)
        create_file_hidden(self.index_file, index_content)

        # Update .last-index
        self.last_index_file.write_text(datetime.now().isoformat())
