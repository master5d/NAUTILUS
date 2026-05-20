"""Migrate a single existing folder to the Facet index with user-friendly interface."""

import json
import sys
import uuid
import click
from pathlib import Path
from datetime import datetime
from core.meta import MetaFile
from core.file_ops import create_directory_hidden
from core.logging import SemanticLogger as OperationsJournal, semantic_command
from core.index import IndexAggregator
from core.config import get_current_root
from jsonschema import validate as json_validate, ValidationError


@click.command('migrate-folder')
@click.argument('folder_path', type=click.Path(exists=True))
@click.option('--title', default=None, help='Project title (auto-derived from folder name if omitted)')
@click.option('--type', 'entity_type', type=click.Choice(['project', 'agent', 'micro', 'sandbox', 'topic', 'vault', 'practice']),
              default='project', help='Folder type')
@click.option('--team', default='ai', help='Team or area assignment')
@click.option('--status', default='active', help='Status (active/paused/archive/wip)')
@click.option('--description', default=None, help='Optional folder description')
@click.option('--dry-run', is_flag=True, default=False, help='Preview without creating (default is to create)')
@semantic_command(name="migrate-folder")
def migrate_folder(folder_path, title, entity_type, team, status, description, dry_run):
    """Migrate a single existing folder to the Facet index.

    This command makes it easy to index an existing folder:

        facet migrate-folder C:/my/folder --title "My Project"

    Or let it auto-derive the title from folder name:

        facet migrate-folder C:/my-folder
    """
    folder_path = Path(folder_path).resolve()

    if not folder_path.exists():
        click.secho(f"❌ Folder not found: {folder_path}", fg="red")
        sys.exit(1)

    if not folder_path.is_dir():
        click.secho(f"❌ Not a directory: {folder_path}", fg="red")
        sys.exit(1)

    # Check if already indexed
    if (folder_path / '.facets' / 'meta.json').exists():
        click.secho(f"⚠️  Already indexed: {folder_path.name}", fg="yellow")
        sys.exit(0)

    # Auto-derive title if not provided
    if not title:
        title = folder_path.name.replace('-', ' ').replace('_', ' ').title()

    # Get the root this folder belongs to
    try:
        root_path = get_current_root()
    except ValueError as e:
        click.secho(f"❌ {str(e)}", fg="red")
        sys.exit(1)

    # Generate unique identifier matching schema: ^[a-z]+-[0-9]{8}-[0-9a-f]{4}$
    today = datetime.now().strftime("%Y%m%d")
    uid = uuid.uuid4().hex[:4]  # 4 hex chars
    identifier = f"{entity_type[:3]}-{today}-{uid}"

    # Build metadata
    meta = {
        "path": str(folder_path),
        "identifier": identifier,
        "title": title,
        "type": entity_type,
        "status": status,
        "team": team,
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
    }

    if description:
        meta["description"] = description

    # Validate metadata against schema
    try:
        schema_file = Path(__file__).parent.parent.parent / "schemas" / "tech.schema.json"
        with open(schema_file) as f:
            schema = json.load(f)
        json_validate(meta, schema)
    except ValidationError as e:
        click.secho(f"❌ Metadata validation failed: {e.message}", fg="red")
        sys.exit(1)
    except Exception as e:
        click.secho(f"⚠️  Could not validate schema: {e}", fg="yellow")

    # Dry-run mode: show what would happen
    if dry_run:
        click.echo("\n📋 DRY-RUN: Would create metadata:")
        click.echo(f"  Folder: {folder_path}")
        click.echo(f"  Title: {title}")
        click.echo(f"  Type: {entity_type}")
        click.echo(f"  Team: {team}")
        click.echo(f"  Status: {status}")
        click.echo(f"  Identifier: {identifier}")
        if description:
            click.echo(f"  Description: {description}")
        click.echo("\nRun without --dry-run to actually migrate")
        return

    # Create metadata
    click.echo(f"\n📝 Migrating: {folder_path.name}")
    try:
        # Create .facets directory
        facets_dir = folder_path / '.facets'
        facets_dir.mkdir(exist_ok=True)

        # Write meta.json
        meta_file = facets_dir / 'meta.json'
        MetaFile.write(meta_file, meta)
        click.secho(f"  ✓ Created .facets/meta.json", fg="green")

        # Log to journal
        journal = OperationsJournal(root_path / ".facets" / "operations.log")
        journal.log_create(entity_type, str(folder_path), dry_run=False)

    except Exception as e:
        click.secho(f"❌ Failed to create metadata: {e}", fg="red")
        sys.exit(1)

    # Rebuild index
    click.echo("🔄 Rebuilding index...")
    try:
        agg = IndexAggregator(root_path, root_path / ".facets")
        agg.rebuild(force=True)
        click.secho(f"  ✓ Index rebuilt", fg="green")
    except Exception as e:
        click.secho(f"⚠️  Index rebuild failed: {e}", fg="yellow")
        click.echo("     (metadata was created but index may not reflect changes yet)")

    # Verify it was indexed
    click.echo("✅ Verifying indexing...")
    index_file = root_path / ".facets" / "index.jsonl"
    found = False
    if index_file.exists():
        for line in index_file.read_text().strip().split('\n'):
            if line:
                try:
                    entry = json.loads(line)
                    if entry.get('path') == str(folder_path):
                        found = True
                        click.secho(f"  ✓ {title} is now indexed (ID: {identifier})", fg="green")
                        break
                except json.JSONDecodeError:
                    pass

    if not found:
        click.secho(f"⚠️  Folder created but not yet in index", fg="yellow")
        click.echo(f"     Run: facet index (to force rebuild)")

    click.echo()
