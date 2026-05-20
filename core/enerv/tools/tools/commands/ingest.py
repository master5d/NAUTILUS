import click
import requests
import os
import json
from pathlib import Path

@click.command()
@click.argument('path')
@click.option('--api-url', default='http://localhost:3010/api/ingest', help='API URL for ingestion')
def ingest(path, api_url):
    """Ingest a file or folder into the 3D Knowledge Graph with ENERV metadata sync."""
    if os.path.isdir(path):
        click.echo(f"📁 Ingesting directory: {path}")
        # Bulk ingestion could be implemented here
        click.echo("Error: Directory ingestion not yet implemented. Please specify a file.")
        return

    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        click.echo(f"❌ Error: File not found: {abs_path}")
        return

    click.echo(f"📄 Ingesting file: {abs_path}")
    
    # Try to find meta.json in the current or parent directory
    meta_data = {}
    current_dir = os.path.dirname(abs_path)
    while current_dir and current_dir != os.path.dirname(current_dir):
        meta_path = os.path.join(current_dir, ".facets", "meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                click.echo(f"✅ Found ENERV metadata: {meta_data.get('title', 'Unknown')}")
                break
            except Exception as e:
                click.echo(f"⚠️ Warning: Could not read meta.json: {e}")
        current_dir = os.path.dirname(current_dir)

    try:
        content = Path(abs_path).read_text(encoding='utf-8')
        title = os.path.basename(abs_path)
        
        payload = {
            "source": "enerv",
            "content": content,
            "title": title,
            "url": abs_path,
            "tags": meta_data.get("tags", []),
            "cluster": meta_data.get("team") or meta_data.get("type") or "general",
            "metadata": meta_data # Custom field for Metadata Sync
        }

        response = requests.post(api_url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            click.echo(f"🎉 Successfully ingested! Node ID: {result.get('nodeId')}")
            click.echo(f"📊 Created {result.get('chunksCreated')} chunks and {result.get('edgesCreated')} similarity edges.")
        else:
            click.echo(f"❌ Ingestion failed (Status {response.status_code}): {response.text}")

    except Exception as e:
        click.echo(f"❌ Error during ingestion: {e}")
