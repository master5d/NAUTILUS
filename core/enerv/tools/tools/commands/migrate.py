import json
import click
from pathlib import Path
from datetime import datetime
from core.meta import MetaFile
from core.file_ops import set_hidden
from core.logging import SemanticLogger as OperationsJournal, semantic_command
from core.index import IndexAggregator
from core.config import get_current_root

@click.command()
@click.option('--root', type=click.Path(exists=True), default=None, help='Tech or knowledge root (auto-detected if omitted)')
@click.option('--batch-confirm', is_flag=True, help='Skip per-folder prompts (use defaults)')
@click.option('--limit', type=int, default=5, help='Limit number of folders to migrate (pilot)')
@semantic_command(name="migrate")
def migrate(root, batch_confirm, limit):
    """Migrate existing folders: create meta.json for unindexed folders."""
    try:
        root_path = Path(root) if root else get_current_root()
    except ValueError as e:
        click.secho(f"❌ {str(e)}", fg="red")
        raise click.Exit(1)
    facets_dir = root_path / ".facets"

    if not facets_dir.exists():
        click.secho("❌ .facets not found. Run 'facet init' first.", fg="red")
        raise click.Exit(1)

    journal = OperationsJournal(facets_dir / "operations.log")

    click.echo(f"\n📋 Analyzing {root_path} for migration")
    click.echo("=" * 60)

    # Find folders without meta.json
    candidates = []
    for folder in root_path.iterdir():
        if folder.is_dir() and not folder.name.startswith('.') and not (folder / "meta.json").exists():
            candidates.append(folder)

    click.echo(f"Found {len(candidates)} folders without meta.json")
    click.echo(f"Limiting to {min(limit, len(candidates))} for pilot migration\n")

    migrated = 0
    for folder in candidates[:limit]:
        click.echo(f"Processing: {folder.name}")

        # Ask for metadata (unless batch mode)
        if not batch_confirm:
            folder_type = click.prompt("  Type (project/agent/micro/sandbox/topic/vault/practice)",
                                      default="project", type=str)
            team_or_area = click.prompt("  Team/Area (personal/ai/infra/wellness)", default="personal")
            status = click.prompt("  Status (active/paused/archive/wip)", default="active")
        else:
            folder_type = "project"
            team_or_area = "personal"
            status = "active"

        # Generate meta
        today = datetime.now().strftime("%Y%m%d")
        meta = {
            "identifier": f"{folder_type[:3]}-{today}-0000",
            "title": folder.name.replace('-', ' ').title(),
            "type": folder_type,
            "status": status,
            "created": datetime.now().strftime("%Y-%m-%d"),
            "updated": datetime.now().strftime("%Y-%m-%d"),
        }

        # Add team or subject_area based on type
        if folder_type in ['project', 'agent', 'micro', 'sandbox', 'department', 'portfolio']:
            meta["team"] = team_or_area
        else:
            meta["subject_area"] = team_or_area

        # Write meta.json
        meta_path = folder / "meta.json"
        MetaFile.write(meta_path, meta)
        journal.log_create(folder_type, str(meta_path), dry_run=False)

        click.secho(f"  ✓ Created meta.json", fg="green")
        migrated += 1

    click.echo("=" * 60)
    click.secho(f"✅ Migrated {migrated} folders", fg="green")

    # Rebuild index
    if migrated > 0:
        click.echo("\n🔄 Rebuilding index...")
        try:
            agg = IndexAggregator(root_path, facets_dir)
            agg.rebuild(force=True)
            click.secho(f"✓ Index rebuilt", fg="green")
        except Exception as e:
            click.secho(f"⚠️  Index rebuild skipped (file locked): {e}", fg="yellow")
