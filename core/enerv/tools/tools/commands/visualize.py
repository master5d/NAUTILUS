import click
import webbrowser
import os

@click.command()
@click.argument('path', default='.')
def visualize(path):
    """Open 3D Knowledge Graph for the specified path."""
    abs_path = os.path.abspath(path)
    click.echo(f"🚀 Visualizing knowledge graph for: {abs_path}")
    
    # Base URL for the embedding-agent (apps/knowledge-graph)
    # Default shifted to 3001 to avoid conflict with LangGraph
    base_url = "http://localhost:3001"
    
    # In the future, we can add ?path=... query parameter if we implement 
    # filtering in the frontend.
    target_url = base_url
    
    webbrowser.open(target_url)
    click.echo(f"Opened {target_url} in your browser.")
