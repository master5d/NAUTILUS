import json
import click
from pathlib import Path
from core.file_ops import create_directory_hidden, create_file_hidden
from core.config import get_current_root
from core.logging import semantic_command

FACETS_TECH = """# FACETS Glossary — Tech Root

## Closed Vocabulary (Enum Values)

### type
- project, agent, micro, sandbox, department, portfolio

### team
- ai, infra, research, wellness, personal, client-work, meta

### status
- active, paused, archive, sandbox, wip

### priority
- P0, P1, P2, P3, P4

### confidentiality
- public, personal, internal, sensitive

## Open Vocabulary (Arrays)

### domain
Examples: fintech, personal-finance, healthcare, devtools, pkm, voice, mobile, web

### tech
Examples: nextjs, react, nodejs, python, dotnet, ai-sdk, vercel, neo4j, serilog
"""

FACETS_KNOWLEDGE = """# FACETS Glossary — Knowledge Root

## Closed Vocabulary

### type
- vault, topic, practice

### status
- active, exploring, dormant, archive

### subject_area
- wellness, biohacking, esoteric, metaphysics, psychology, psychotherapy, spirituality,
  personal-development, history, science, art, language

### maturity
- exploring, learning, practicing, integrating, teaching

## Open Vocabulary

### source_type (array)
Examples: book, course, summit, method, practice, lecture, podcast, video, article

### modality (array)
Examples: text, audio, video, experiential, ritual, meditation, bodywork
"""

FACETSIGNORE = """# Patterns to ignore during indexing
$RECYCLE.BIN
System Volume Information
~*
Thumbs.db
.DS_Store
"""

@click.command()
@click.option('--root', type=click.Path(exists=True), default=None, help='Root directory (auto-detected if omitted)')
@click.option('--type', type=click.Choice(['tech', 'knowledge']), required=True, help='Root type')
@semantic_command(name="init")
def init(root, type):
    """Initialize .facets directory for a root."""
    if not root:
        try:
            root = str(get_current_root())
        except ValueError as e:
            click.secho(f"❌ {str(e)}", fg="red")
            import sys
            sys.exit(1)

    root_path = Path(root)
    facets_dir = root_path / ".facets"

    if facets_dir.exists():
        click.secho(f"⚠️  .facets already exists in {root_path}", fg="yellow")
        return

    click.echo(f"\n🚀 Initializing .facets for {type} root: {root_path}")

    # Create .facets directory (hidden)
    create_directory_hidden(facets_dir)

    # Copy schema
    schema_src = Path(__file__).parent.parent.parent / "schemas" / f"{type}.schema.json"
    schema_dst = facets_dir / "schema.json"
    if schema_src.exists():
        schema_dst.write_text(schema_src.read_text())
    else:
        click.secho(f"⚠️  Schema file not found: {schema_src}", fg="yellow")

    # Write FACETS.md
    facets_content = FACETS_TECH if type == 'tech' else FACETS_KNOWLEDGE
    create_file_hidden(facets_dir / "FACETS.md", facets_content)

    # Write .facetsignore
    create_file_hidden(facets_dir / ".facetsignore", FACETSIGNORE)

    # Create empty index.jsonl
    create_file_hidden(facets_dir / "index.jsonl", "")

    click.secho(f"✅ Initialized .facets in {root_path}", fg="green")
    click.echo(f"   schema.json, FACETS.md, .facetsignore, index.jsonl (empty)")
