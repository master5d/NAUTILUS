import json
import uuid
import click
from pathlib import Path
from datetime import datetime
from core.meta import MetaFile
from core.file_ops import create_directory_hidden
from core.logging import SemanticLogger as OperationsJournal, semantic_command

@click.command()
@click.argument('entity_type', type=click.Choice(['project', 'agent', 'micro', 'sandbox', 'topic', 'vault', 'practice']))
@click.argument('team_or_area')
@click.argument('status')
@click.argument('slug')
@click.option('--root', type=click.Path(exists=True), default=None, help='Root directory (auto-detected if omitted)')
@click.option('--dry-run', 'mode', flag_value='dry-run', default=True, help='Preview without creating (default)')
@click.option('--apply', 'mode', flag_value='apply', help='Actually create')
@click.option('--parent', default=None, help='Parent folder path')
@click.option('--priority', type=int, default=None, help='LLM Context Priority (1-10)')
@semantic_command(name="new")
def new(entity_type, team_or_area, status, slug, root, mode, parent, priority):
    """Create new folder and meta.json."""
    try:
        root_path = Path(root) if root else get_current_root()
    except ValueError as e:
        click.secho(f"❌ {str(e)}", fg="red")
        raise click.Exit(1)

    # If priority not provided, ask for it (unless non-interactive)
    if priority is None:
        try:
            priority = click.prompt("LLM Context Priority (1-10)", type=int, default=5)
        except click.exceptions.Abort:
            priority = 5
        except Exception:
            priority = 5

    # Determine folder name based on type
    if entity_type in ['project', 'agent', 'micro', 'sandbox']:
        folder_name = f"{entity_type}__{team_or_area}__{status}__{slug}"
    else:  # knowledge types
        folder_name = slug  # For knowledge, use free-form name

    folder_path = root_path / folder_name

    # Generate unique identifier
    today = datetime.now().strftime("%Y%m%d")
    uid = uuid.uuid4().hex[:4]
    identifier = f"{entity_type[:3]}-{today}-{uid}"

    # Build meta.json
    meta = {
        "identifier": identifier,
        "title": slug.replace('-', ' ').title(),
        "type": entity_type,
        "status": status,
        "created": datetime.now().strftime("%Y-%m-%d"),
        "updated": datetime.now().strftime("%Y-%m-%d"),
        "llm_context_priority": priority,
        "evolutionary_links": [],
        "dependencies": [],
    }

    if entity_type in ['project', 'agent', 'micro', 'sandbox', 'department', 'portfolio']:
        meta["team"] = team_or_area
    else:
        meta["subject_area"] = team_or_area

    if parent:
        meta["parent"] = parent

    # Output mode (default is dry-run)
    if mode == 'dry-run':
        click.echo(f"\n📋 Would create: {folder_path}")
        click.echo(f"Meta:\n{json.dumps(meta, indent=2)}")
        click.echo("\nUse --apply to actually create")
        return

    # Apply mode
    if mode == 'apply':
        click.echo(f"\n✅ Creating: {folder_path}")

        create_directory_hidden(folder_path)
        MetaFile.write(folder_path / "meta.json", meta)

        # Log to journal
        journal = OperationsJournal(root_path / ".facets" / "operations.log")
        journal.log_create(entity_type, str(folder_path), dry_run=False)

        click.echo(f"✓ Folder created: {folder_path.name}")
        click.echo(f"✓ Meta written to meta.json (hidden)")
