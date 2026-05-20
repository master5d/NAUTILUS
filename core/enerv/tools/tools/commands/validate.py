import json
import click
from pathlib import Path
from jsonschema import validate as json_validate, ValidationError
from core.config import get_current_root
from core.logging import semantic_command

@click.command()
@click.option('--root', type=click.Path(exists=True), default=None, help='Root directory (auto-detected if omitted)')
@semantic_command(name="validate")
def validate(root):
    """Validate all meta.json files against schema."""
    try:
        root_path = Path(root) if root else get_current_root()
    except ValueError as e:
        click.secho(f"❌ {str(e)}", fg="red")
        raise click.Exit(1)

    # Load appropriate schema based on root path
    if root_path.name == "telo" or "tech" in str(root_path).lower():
        schema_file = Path(__file__).parent.parent.parent / "schemas" / "tech.schema.json"
    else:
        schema_file = Path(__file__).parent.parent.parent / "schemas" / "knowledge.schema.json"

    with open(schema_file) as f:
        schema = json.load(f)

    valid_count = 0
    invalid_count = 0
    errors = []

    click.echo(f"\n🔍 Validating meta.json in {root_path}")
    click.echo("=" * 60)

    for meta_file in root_path.rglob("meta.json"):
        # Skip meta files in .facets directory
        if ".facets" in meta_file.parts:
            continue

        try:
            meta = json.loads(meta_file.read_text())
            json_validate(meta, schema)
            valid_count += 1
            click.echo(f"  ✓ {meta_file.relative_to(root_path)}")
        except ValidationError as e:
            invalid_count += 1
            errors.append((meta_file, e.message))
            click.echo(f"  ✗ {meta_file.relative_to(root_path)}: {e.message}")
        except json.JSONDecodeError as e:
            invalid_count += 1
            errors.append((meta_file, f"Invalid JSON: {e.msg}"))
            click.echo(f"  ✗ {meta_file.relative_to(root_path)}: Invalid JSON: {e.msg}")

    click.echo("=" * 60)
    click.echo(f"Valid: {valid_count}, Invalid: {invalid_count}")

    if invalid_count > 0:
        click.secho("\n❌ Validation failed", fg="red")
        raise click.Exit(1)
    else:
        click.secho("\n✅ All valid", fg="green")
