"""
Automatic indexing command with hybrid debounce strategy.

This module implements the `facet auto-index` CLI command, which rebuilds
tech and knowledge root indexes based on independent debounce thresholds:

- Tech root (C:\\telo): rebuild if >= 3 minutes since last index
- Knowledge root (E:\\): rebuild if >= 60 minutes since last index

State is persisted in .facets/.last-index files (ISO 8601 timestamps).
Edge cases (missing files, clock skew) are handled safely.
"""

from datetime import datetime
from pathlib import Path
import json
import click
import sys
from core.logging import semantic_command

# Import for testing/mocking purposes (will be imported dynamically in rebuild_index_for_root)
try:
    from tools.core.index import IndexAggregator
except ImportError:
    IndexAggregator = None

def read_last_index_timestamp(facets_dir):
    """
    Read last index timestamp from .facets/.last-index file.
    """
    facets_dir = Path(facets_dir)
    last_index_file = facets_dir / ".last-index"

    if not last_index_file.exists():
        return None

    timestamp_str = last_index_file.read_text().strip()
    return datetime.fromisoformat(timestamp_str)


def should_rebuild(last_index_time, now, threshold_minutes):
    """
    Determine if an index should be rebuilt based on elapsed time.
    """
    elapsed_seconds = (now - last_index_time).total_seconds()

    # Clock skew detection: if time went backward, always rebuild (safety)
    if elapsed_seconds < 0:
        return True

    return elapsed_seconds >= (threshold_minutes * 60)


def write_last_index_timestamp(facets_dir, now=None):
    """
    Write current timestamp to .facets/.last-index file.
    """
    if now is None:
        now = datetime.now()

    facets_dir = Path(facets_dir)
    facets_dir.mkdir(parents=True, exist_ok=True)

    last_index_file = facets_dir / ".last-index"
    last_index_file.write_text(now.isoformat() + "\n")


def check_root_rebuild_needed(root_path, root_name, now=None):
    """
    Check if a root needs index rebuild based on debounce threshold.
    """
    if now is None:
        now = datetime.now()

    thresholds = {"tech": 3, "knowledge": 60}
    threshold_minutes = thresholds.get(root_name, 60)

    facets_dir = Path(root_path) / ".facets"

    # If .facets doesn't exist, skip this root
    if not facets_dir.exists():
        return False, f".facets directory not initialized"

    last_index_time = read_last_index_timestamp(facets_dir)

    # If .last-index missing, always rebuild (first run or corrupted)
    if last_index_time is None:
        return True, f"No .last-index found (first run or corrupted)"

    if should_rebuild(last_index_time, now, threshold_minutes):
        elapsed_minutes = (now - last_index_time).total_seconds() / 60
        return True, f"{elapsed_minutes:.1f} minutes elapsed"
    else:
        elapsed_minutes = (now - last_index_time).total_seconds() / 60
        return False, f"{elapsed_minutes:.1f} minutes elapsed ({threshold_minutes} min threshold)"


def build_summary(tech_indexed, tech_reason, tech_entry_count,
                  knowledge_indexed, knowledge_reason, knowledge_entry_count,
                  timestamp):
    """
    Build JSON summary of auto-index operation.
    """
    return json.dumps({
        "tech": {
            "indexed": tech_indexed,
            "reason": tech_reason,
            "entry_count": tech_entry_count
        },
        "knowledge": {
            "indexed": knowledge_indexed,
            "reason": knowledge_reason,
            "entry_count": knowledge_entry_count
        },
        "timestamp": timestamp.isoformat()
    }, indent=2)


def rebuild_index_for_root(root_path):
    """
    Rebuild index for a root using IndexAggregator.
    """
    from tools.core.index import IndexAggregator

    root_path = Path(root_path)
    facets_dir = root_path / ".facets"

    aggregator = IndexAggregator(root_path, facets_dir, debounce_minutes=0)
    aggregator.rebuild(force=True)  # Force rebuild, bypass debouncing

    # Count entries in index.jsonl
    index_file = facets_dir / "index.jsonl"
    if not index_file.exists():
        return 0

    entries = index_file.read_text().strip().split("\n")
    return len([e for e in entries if e])  # Count non-empty lines


def auto_index_command(tech_root, knowledge_root, now=None):
    """
    Auto-index command: check debounce for both roots, rebuild if needed.
    """
    if now is None:
        now = datetime.now()

    # Check if tech needs rebuild
    tech_needed, tech_reason = check_root_rebuild_needed(
        root_path=tech_root,
        root_name="tech",
        now=now
    )

    # Check if knowledge needs rebuild
    knowledge_needed, knowledge_reason = check_root_rebuild_needed(
        root_path=knowledge_root,
        root_name="knowledge",
        now=now
    )

    tech_entry_count = 0
    knowledge_entry_count = 0

    # Rebuild tech if needed
    if tech_needed:
        tech_entry_count = rebuild_index_for_root(tech_root)
        write_last_index_timestamp(Path(tech_root) / ".facets", now=now)

    # Rebuild knowledge if needed
    if knowledge_needed:
        knowledge_entry_count = rebuild_index_for_root(knowledge_root)
        write_last_index_timestamp(Path(knowledge_root) / ".facets", now=now)

    return build_summary(
        tech_indexed=tech_needed,
        tech_reason=tech_reason,
        tech_entry_count=tech_entry_count,
        knowledge_indexed=knowledge_needed,
        knowledge_reason=knowledge_reason,
        knowledge_entry_count=knowledge_entry_count,
        timestamp=now
    )


@click.command("auto-index")
@click.option(
    "--tech-root",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default="C:\\telo",
    help="Tech root directory"
)
@click.option(
    "--knowledge-root",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default="E:\\",
    help="Knowledge root directory"
)
@click.option(
    "--silent",
    is_flag=True,
    help="Log errors to journal but do not exit with non-zero code"
)
@semantic_command(name="auto-index")
def auto_index_cli(tech_root, knowledge_root, silent):
    """Rebuild indexes for tech and knowledge roots using hybrid debounce."""
    try:
        result = auto_index_command(
            tech_root=tech_root,
            knowledge_root=knowledge_root,
            now=datetime.now()
        )
        click.echo(result)
    except Exception as e:
        if silent:
            # Errors are already logged by the @semantic_command decorator
            click.echo(json.dumps({"error": str(e)}))
            sys.exit(0)  # Forced success
        else:
            raise e
