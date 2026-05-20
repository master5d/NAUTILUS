import click
from pathlib import Path
from core.index import IndexAggregator
from core.config import get_current_root
from core.logging import semantic_command

@click.command()
@click.option('--root', type=click.Path(exists=True), default=None, help='Root directory (auto-detected if omitted)')
@click.option('--force', is_flag=True, help='Force full rebuild (skip debounce)')
@semantic_command(name="index")
def index(root, force):
    """Rebuild aggregated index (with debounce, unless --force)."""
    try:
        root_path = Path(root) if root else get_current_root()
    except ValueError as e:
        click.secho(f"❌ {str(e)}", fg="red")
        raise click.Exit(1)
    facets_dir = root_path / ".facets"

    if not facets_dir.exists():
        click.secho(f"❌ .facets directory not found in {root_path}", fg="red")
        raise click.Exit(1)

    click.echo(f"\n🔨 Rebuilding index for {root_path}")

    agg = IndexAggregator(root_path, facets_dir)
    agg.rebuild(force=force)

    index_file = facets_dir / "index.jsonl"
    if index_file.exists():
        lines = [l for l in index_file.read_text().strip().split('\n') if l]
        count = len(lines)
    else:
        count = 0

    click.secho(f"✅ Indexed {count} entries", fg="green")
