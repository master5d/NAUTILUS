import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from core.meta import MetaFile
from core.file_ops import create_file_hidden

class IndexAggregator:
    """Aggregates meta.json files into index.jsonl with incremental + debounce."""

    def __init__(self, root: Path, facets_dir: Path, debounce_minutes: int = 5, max_workers: int = 12):
        self.root = root
        self.facets_dir = facets_dir
        self.debounce_minutes = debounce_minutes
        self.max_workers = max_workers
        self.index_file = facets_dir / "index.jsonl"
        self.last_index_file = facets_dir / ".last-index"

    def should_rebuild(self) -> bool:
        """Check if rebuild is needed based on debounce."""
        if not self.last_index_file.exists():
            return True

        try:
            last_index_time = self.last_index_file.read_text().strip()
            last_time = datetime.fromisoformat(last_index_time)
            now = datetime.now()
            return (now - last_time).total_seconds() >= (self.debounce_minutes * 60)
        except Exception:
            return True

    def rebuild(self, force: bool = False) -> None:
        """Rebuild index from all meta.json files in root using multithreading."""
        if not force and not self.should_rebuild():
            return

        entries = []

        def process_directory(current_path: Path) -> List[Dict[str, Any]]:
            local_entries = []
            try:
                # Optimized walk: manually handle directories and files
                items = list(current_path.iterdir())
                for item in items:
                    if not item.is_dir():
                        if item.name == "meta.json" and item.parent != self.facets_dir:
                            try:
                                meta = MetaFile.read(item)
                                if any(f in meta for f in ["name", "project", "title", "identifier"]):
                                    local_entries.append(meta)
                            except Exception:
                                pass
                        continue
                    
                    # Skip heavy system dirs
                    if item.name in [".git", "node_modules", ".next", ".claude", "venv", ".venv"]:
                        continue
                    
                    # Shallow recursive call for subdirectories
                    local_entries.extend(process_directory(item))
            except OSError:
                pass
            return local_entries

        # Multi-threaded scanning: split by top-level folders
        try:
            top_level_items = list(self.root.iterdir())
            top_folders = [d for d in top_level_items if d.is_dir() and not d.name.startswith('.')]
            root_files = [f for f in top_level_items if not f.is_dir()]
        except OSError:
            top_folders = []
            root_files = []

        if not top_folders:
            entries = process_directory(self.root)
        else:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                results = executor.map(process_directory, top_folders)
                for res in results:
                    entries.extend(res)
            
            # Don't forget meta.json files sitting directly in the root
            for f in root_files:
                if f.name == "meta.json" and f.parent != self.facets_dir:
                    try:
                        meta = MetaFile.read(f)
                        entries.append(meta)
                    except Exception: pass

        # Write index.jsonl
        index_content = "\n".join(json.dumps(e) for e in entries)
        create_file_hidden(self.index_file, index_content)

        # Update .last-index
        self.last_index_file.write_text(datetime.now().isoformat())
