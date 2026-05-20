import json
from pathlib import Path
from datetime import datetime
import click


def validate_folder_path(path_str):
    """
    Validate that folder exists and return absolute Path.

    Args:
        path_str: folder path as string

    Returns:
        Path: absolute path object

    Raises:
        ValueError: if folder doesn't exist
    """
    path = Path(path_str).resolve()
    if not path.is_dir():
        raise ValueError(f"Folder not found: {path}")
    return path


def detect_root(folder_path):
    """
    Determine which root a folder belongs to.

    Args:
        folder_path: Path object (absolute)

    Returns:
        tuple: (root_path, root_name) where root_name is "tech" or "knowledge"

    Raises:
        ValueError: if folder is not under a known root
    """
    folder_path = Path(folder_path).resolve()

    # Define roots
    tech_root = Path("C:/telo").resolve()
    knowledge_root = Path("E:/").resolve()

    # Check which root contains this folder
    if str(folder_path).startswith(str(tech_root)):
        return tech_root, "tech"
    elif str(folder_path).startswith(str(knowledge_root)):
        return knowledge_root, "knowledge"
    else:
        raise ValueError(f"Folder {folder_path} is not under a known root")


def lookup_metadata_in_index(folder_path, facets_dir):
    """
    Search index.jsonl for metadata matching folder_path.

    Args:
        folder_path: Path object (absolute)
        facets_dir: Path to .facets directory

    Returns:
        dict: metadata entry, or None if not found
    """
    folder_path_str = str(Path(folder_path).resolve())
    index_file = Path(facets_dir) / "index.jsonl"

    if not index_file.exists():
        return None

    try:
        for line in index_file.read_text().strip().split("\n"):
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("path") == folder_path_str:
                return entry
    except (json.JSONDecodeError, IOError):
        return None

    return None


def calculate_folder_stats(folder_path):
    """
    Calculate folder statistics.

    Args:
        folder_path: Path object

    Returns:
        dict: {file_count, folder_count, total_size_bytes, last_modified}
    """
    folder_path = Path(folder_path)

    file_count = 0
    folder_count = 0
    total_size = 0

    for item in folder_path.iterdir():
        if item.is_file():
            file_count += 1
            total_size += item.stat().st_size
        elif item.is_dir():
            folder_count += 1

    # Get folder's last-modified time
    mtime = folder_path.stat().st_mtime
    last_modified = datetime.fromtimestamp(mtime).isoformat()

    return {
        "file_count": file_count,
        "folder_count": folder_count,
        "total_size_bytes": total_size,
        "last_modified": last_modified
    }


def enumerate_children(folder_path, facets_dir):
    """
    List immediate children with indexed status.

    Args:
        folder_path: Path to parent folder
        facets_dir: Path to .facets directory

    Returns:
        list: Children dicts sorted (indexed first, then by name)
    """
    folder_path = Path(folder_path)
    children = []

    # Build set of indexed paths
    indexed_paths = set()
    index_file = Path(facets_dir) / "index.jsonl"
    if index_file.exists():
        try:
            for line in index_file.read_text().strip().split("\n"):
                if line:
                    entry = json.loads(line)
                    indexed_paths.add(entry.get("path"))
        except (json.JSONDecodeError, IOError):
            pass

    # Enumerate children
    for item in folder_path.iterdir():
        child_path = item.resolve()
        is_indexed = str(child_path) in indexed_paths

        if item.is_file():
            children.append({
                "name": item.name,
                "type": "file",
                "indexed": is_indexed,
                "size_bytes": item.stat().st_size,
                "last_modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            })
        elif item.is_dir():
            file_count = sum(1 for _ in item.glob("*") if _.is_file())
            children.append({
                "name": item.name,
                "type": "folder",
                "indexed": is_indexed,
                "file_count": file_count,
                "last_modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            })

    # Sort: indexed first, then by name
    children.sort(key=lambda x: (not x["indexed"], x["name"]))

    return children


def build_output(folder_path, facets_dir, metadata=None):
    """
    Build complete JSON output object.

    Args:
        folder_path: Path to folder
        facets_dir: Path to .facets directory
        metadata: dict from index, or None if not indexed

    Returns:
        dict: Complete output structure
    """
    folder_path = Path(folder_path).resolve()

    return {
        "path": str(folder_path),
        "indexed": metadata is not None,
        "metadata": metadata,
        "stats": calculate_folder_stats(folder_path),
        "children": enumerate_children(folder_path, facets_dir)
    }


@click.command("current-info")
@click.argument("path", type=click.Path(exists=True))
def current_info_cli(path):
    """Show metadata and children for a folder."""
    try:
        folder_path = validate_folder_path(path)
        root, root_name = detect_root(folder_path)
        facets_dir = root / ".facets"

        metadata = lookup_metadata_in_index(folder_path, facets_dir)
        output = build_output(folder_path, facets_dir, metadata)

        click.echo(json.dumps(output))
    except ValueError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(json.dumps({"error": f"Unexpected error: {str(e)}"}), err=True)
        raise SystemExit(2)
