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

        # Walk root, find all meta.json
        for folder in self.root.rglob("meta.json"):
            # Skip root .facets/meta.json (system config)
            if folder.parent == self.facets_dir:
                continue

            # Skip node_modules (npm package metadata, not facet metadata)
            if "node_modules" in folder.parts:
                continue

            try:
                meta = MetaFile.read(folder)
                
                # Check for existence of any naming field to consider it a valid facet
                naming_fields = ["name", "project", "title", "identifier"]
                has_identity = any(field in meta for field in naming_fields)

                if has_identity:
                    # Normalization for the index (optional, but good for aggregate)
                    # We keep original meta but ensure it's indexed
                    entries.append(meta)
            except Exception:
                pass  # Skip invalid meta.json

        # Write index.jsonl
        index_content = "\n".join(json.dumps(e) for e in entries)
        create_file_hidden(self.index_file, index_content)

        # Update .last-index
        self.last_index_file.write_text(datetime.now().isoformat())
