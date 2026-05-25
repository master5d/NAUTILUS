import click
import os
from neo4j import GraphDatabase
from .ingest import load_nautilus_env, get_embedding

@click.command()
@click.argument('query')
@click.option('--top-k', default=5, type=int, help='Number of top results to return')
@click.option('--min-score', default=0.6, type=float, help='Minimum similarity score threshold')
def search(query, top_k, min_score):
    """Perform a semantic vector similarity search against the Nautilus Knowledge Graph."""
    if not query.strip():
        click.secho("❌ Error: Query cannot be empty.", fg="red")
        return

    click.secho(f"🔎 Searching semantically for: '{query}'...", fg="cyan")

    # 1. Load Environment Variables
    env = load_nautilus_env()
    neo4j_uri = env.get("NEO4J_URI") or "neo4j+s://localhost:7687"
    neo4j_user = env.get("NEO4J_USERNAME") or "neo4j"
    neo4j_pass = env.get("NEO4J_PASSWORD")
    neo4j_db = env.get("NEO4J_DATABASE") or "neo4j"

    if not neo4j_pass:
        click.secho("❌ Error: NEO4J_PASSWORD not found in .env file.", fg="red")
        return

    # 2. Generate Embedding for the query
    try:
        click.echo("  [~] Generating embedding vector...")
        embedding = get_embedding(query, env)
    except Exception as e:
        click.secho(f"❌ Error generating embedding: {e}", fg="red")
        return

    # 3. Query Neo4j
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
        with driver.session(database=neo4j_db) as session:
            click.echo("  [~] Querying Neo4j vector index...")
            
            cypher = """
            CALL db.index.vector.queryNodes('document_embeddings', $top_k, $embedding)
            YIELD node, score
            WHERE score >= $min_score
            RETURN node.id AS id, node.title AS title, node.content AS content,
                   node.url AS url, node.source AS source, node.cluster AS cluster,
                   score
            ORDER BY score DESC
            """
            
            res = session.run(cypher, {"top_k": top_k, "embedding": embedding, "min_score": min_score})
            records = list(res)
            
            if not records:
                click.secho("💡 No matching nodes found above the similarity threshold.", fg="yellow")
                return

            click.secho(f"\n🎯 Found {len(records)} matching nodes:", fg="green", bold=True)
            for idx, r in enumerate(records, 1):
                title = r["title"]
                score = r["score"]
                content = r["content"]
                filepath = r["url"]  # Stored as file path under url
                source = r["source"]
                
                click.secho(f"\n[{idx}] {title} (Similarity: {score:.4f})", fg="cyan", bold=True)
                if filepath:
                    click.secho(f"    Path: {filepath}", fg="zinc" if hasattr(click, "zinc") else "white")
                if content:
                    snippet = content.replace("\n", " ").strip()[:200]
                    click.echo(f"    Snippet: {snippet}...")
                click.echo(f"    Source: {source}")
                
    except Exception as e:
        click.secho(f"❌ Database error: {e}", fg="red")
