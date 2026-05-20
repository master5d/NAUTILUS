import click
import json
from pathlib import Path
from core.config import ScopeConfig, get_current_root
from core.meta import MetaFile
from core.logging import semantic_command

@click.command()
@click.option('--root', type=click.Path(exists=True), default=None, help='Root directory to audit (auto-detected if omitted)')
@semantic_command(name="audit")
def audit(root):
    """Audit current state without making changes (always safe)."""
    try:
        root_path = Path(root) if root else get_current_root()
    except ValueError as e:
        click.secho(f"❌ {str(e)}", fg="red")
        raise click.Exit(1)
    facets_dir = root_path / ".facets"

    click.echo(f"\n📋 Audit Report for {root_path}")
    click.echo("=" * 60)

    # Count meta.json files safely with multithreading
    meta_count = 0
    click.echo("🔍 Scanning for metadata...")
    try:
        from concurrent.futures import ThreadPoolExecutor
        
        def count_meta_in_dir(path: Path):
            count = 0
            try:
                for item in path.iterdir():
                    if item.is_dir():
                        if item.name not in [".git", "node_modules", ".next", ".claude", "venv", ".venv"]:
                            count += count_meta_in_dir(item)
                    elif item.name == "meta.json":
                        count += 1
            except OSError: pass
            return count

        top_dirs = [d for d in root_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        with ThreadPoolExecutor(max_workers=12) as executor:
            meta_count = sum(executor.map(count_meta_in_dir, top_dirs))
        
        # Check root itself
        for f in root_path.iterdir():
            if not f.is_dir() and f.name == "meta.json":
                meta_count += 1
                
    except OSError as e:
        click.secho(f"⚠️ Warning: Permissions issue: {e}", fg="yellow")
    
    click.echo(f"Folders with meta.json: {meta_count}")

    # List top-level folders safely
    top_level = []
    try:
        top_level = [d for d in root_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    except OSError as e:
        click.secho(f"⚠️ Warning: Could not list all top-level folders: {e}", fg="yellow")
    
    click.echo(f"Top-level folders: {len(top_level)}")
    for folder in sorted(top_level)[:10]:
        try:
            has_meta = (folder / "meta.json").exists()
            click.echo(f"  {'✓' if has_meta else ' '} {folder.name}")
        except OSError:
            click.echo(f"  ? {folder.name} (Access Denied)")

    # Check .facets status
    if facets_dir.exists():
        click.echo(f".facets directory: exists")
        if (facets_dir / "index.jsonl").exists():
            lines = (facets_dir / "index.jsonl").read_text().strip().split('\n')
            click.echo(f"  index.jsonl: {len(lines)} entries")
    else:
        click.echo(".facets directory: NOT FOUND")

    # Journal Audit
    journal_file = facets_dir / "journal.jsonl"
    if journal_file.exists():
        click.echo("\n📜 Recent Operations (Journal):")
        lines = [l for l in journal_file.read_text().strip().split('\n') if l]
        last_5 = lines[-5:]
        for line in last_5:
            try:
                entry = json.loads(line)
                ts = entry.get('timestamp', '').split('T')[0]
                op = entry.get('operation', 'unknown')
                status = entry.get('status', 'success')
                target = Path(entry.get('target', '')).name
                color = "green" if status == "success" else "red"
                click.echo(f"  {ts} | {click.style(op, bold=True)} | {click.style(status, fg=color)} | {target}")
            except Exception:
                continue
    else:
        # Fallback to old operations.log
        legacy_journal = facets_dir / "operations.log"
        if legacy_journal.exists():
             click.echo("\n📜 Recent Operations (Legacy Journal):")
             lines = [l for l in legacy_journal.read_text().strip().split('\n') if l]
             last_5 = lines[-5:]
             for line in last_5:
                 try:
                     entry = json.loads(line)
                     ts = entry.get('timestamp', '').split('T')[0]
                     op = entry.get('operation', 'unknown')
                     click.echo(f"  {ts} | {op} | {Path(entry.get('target', '')).name}")
                 except Exception:
                     continue

    click.echo("=" * 60)
    click.echo("\n✅ Audit complete. No changes made.")
