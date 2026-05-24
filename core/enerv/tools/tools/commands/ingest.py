import click
import os
import json
import hashlib
import re
import uuid
import requests
from pathlib import Path
from neo4j import GraphDatabase

REGISTRY_PATH = r"C:\telo\Efforts\Ongoing\NAUTILUS\config\services.json"

def load_nautilus_env():
    """Dynamically find and parse the .env file by walking up parent directories."""
    env = {}
    current_dir = os.getcwd()
    # Walk up to 6 levels to find the monorepo root
    for _ in range(6):
        env_path = os.path.join(current_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    if "=" in line and not line.strip().startswith("#"):
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip().strip('"').strip("'")
            break
        parent = os.path.dirname(current_dir)
        if parent == current_dir:
            break
        current_dir = parent
    return env

def get_litellm_url():
    """Retrieve LiteLLM dynamic URL from the Port Broker registry or fall back to 4000."""
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                if "litellm" in data:
                    return data["litellm"]["url"]
        except Exception:
            pass
    return "http://localhost:4000"

def get_embedding(text, env):
    """Generate 768-dim embeddings via LiteLLM proxy, falling back to direct Gemini API if offline."""
    normalized = re.sub(r"\s+", " ", text).strip()
    
    # Attempt 1: LiteLLM
    try:
        litellm_url = get_litellm_url()
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "gemini-embedding-001",
            "input": [normalized]
        }
        res = requests.post(f"{litellm_url}/v1/embeddings", json=payload, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()["data"][0]["embedding"]
    except Exception:
        pass

    # Attempt 2: Direct Google Gemini API
    api_key = env.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment. Start LiteLLM proxy or set key.")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
    payload = {
        "content": {
            "parts": [{"text": normalized}]
        }
    }
    res = requests.post(url, json=payload, timeout=10)
    res.raise_for_status()
    return res.json()["embedding"]["values"]

def chunk_text(text, max_words=400, overlap_words=50):
    """Chunk text into overlapping segments."""
    words = text.split()
    if len(words) <= max_words:
        return [text]
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+max_words])
        chunks.append(chunk)
        i += max_words - overlap_words
    return chunks

def hash_content(text):
    """Generate SHA-256 hash of content for deduplication."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def normalize_id(title, url=None):
    """Generate a stable, unique ID based on URL or slugified title."""
    if url:
        return re.sub(r"[^a-z0-9]/gi", "-", url.replace("https://", "").replace("http://", "")).lower()[:80]
    slug = re.sub(r"[^\w-]", "", title.lower().replace(" ", "-"))[:60]
    return f"{slug}-{str(uuid.uuid4())[:8]}"

@click.command()
@click.argument('path')
@click.option('--force', is_flag=True, help='Force re-ingest even if content hash matches')
def ingest(path, force):
    """Ingest a file into the 3D Knowledge Graph with ENERV metadata sync."""
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        click.secho(f"❌ Error: File not found: {abs_path}", fg="red")
        return

    if os.path.isdir(abs_path):
        click.secho("❌ Error: Directory ingestion is deprecated. Please specify a single Markdown/file path.", fg="red")
        return

    click.secho(f"📄 Local Ingest starting for: {abs_path}", fg="cyan")

    # 1. Parse Enerv meta.json
    meta_data = {}
    current_dir = os.path.dirname(abs_path)
    while current_dir and current_dir != os.path.dirname(current_dir):
        meta_path = os.path.join(current_dir, ".facets", "meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                click.secho(f"  [+] Loaded ENERV metadata: '{meta_data.get('title', 'Untitled')}'", fg="green")
                break
            except Exception as e:
                click.secho(f"  [!] Warning reading meta.json: {e}", fg="yellow")
        current_dir = os.path.dirname(current_dir)

    # 2. Load Environment Variables
    env = load_nautilus_env()
    neo4j_uri = env.get("NEO4J_URI") or "neo4j+s://localhost:7687"
    neo4j_user = env.get("NEO4J_USERNAME") or "neo4j"
    neo4j_pass = env.get("NEO4J_PASSWORD")
    neo4j_db = env.get("NEO4J_DATABASE") or "neo4j"

    if not neo4j_pass:
        click.secho("❌ Error: NEO4J_PASSWORD not found in .env file.", fg="red")
        return

    try:
        content = Path(abs_path).read_text(encoding='utf-8')
        title = os.path.basename(abs_path)
        content_hash = hash_content(content)
        doc_id = normalize_id(title, abs_path)

        # 3. Establish Neo4j connection
        click.echo("  [~] Connecting to Neo4j database...")
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
        
        with driver.session(database=neo4j_db) as session:
            # 4. Check if document exists and matches hash
            if not force:
                res = session.run("MATCH (d:Document {id: $id}) RETURN d.contentHash as existingHash", {"id": doc_id})
                record = res.single()
                if record and record["existingHash"] == content_hash:
                    click.secho("✓ Content hash matches existing node. Skipping re-sync (use --force to override).", fg="green")
                    return

            # 5. Chunk and embed
            click.echo("  [~] Chunking content and generating vector embeddings...")
            chunks = chunk_text(content)
            
            # Embed first chunk
            first_embedding = get_embedding(chunks[0], env)
            
            # Merge Main Document Node
            session.run("""
                MERGE (d:Document {id: $id})
                ON CREATE SET d.createdAt = datetime()
                SET d.title = $title,
                    d.content = $content,
                    d.url = $url,
                    d.source = 'enerv',
                    d.cluster = $cluster,
                    d.embedding = $embedding,
                    d.contentHash = $contentHash,
                    d.updatedAt = datetime()
            """, {
                "id": doc_id,
                "title": title,
                "content": content[:2000],
                "url": abs_path,
                "cluster": meta_data.get("team") or meta_data.get("type") or "General",
                "embedding": first_embedding,
                "contentHash": content_hash
            })

            # Merge Cluster belongs relationship
            cluster = meta_data.get("team") or meta_data.get("type") or "General"
            cluster_id = cluster.lower().replace(" ", "-")
            session.run("""
                MERGE (c:Cluster {id: $clusterId})
                ON CREATE SET c.name = $clusterName, c.createdAt = datetime()
                WITH c
                MATCH (d:Document {id: $docId})
                MERGE (d)-[:BELONGS_TO]->(c)
            """, {
                "clusterId": cluster_id,
                "clusterName": cluster,
                "docId": doc_id
            })

            # Merge Tags
            tags = meta_data.get("tags") or []
            for tag in tags:
                session.run("""
                    MERGE (t:Tag {name: $tag})
                    WITH t
                    MATCH (d:Document {id: $docId})
                    MERGE (d)-[:TAGGED]->(t)
                """, {"tag": tag, "docId": doc_id})

            # Store remaining chunks
            for i in range(1, len(chunks)):
                chunk_id = f"{doc_id}--chunk-{i}"
                chunk_embedding = get_embedding(chunks[i], env)
                session.run("""
                    MERGE (d:Document {id: $id})
                    ON CREATE SET d.createdAt = datetime()
                    SET d.title = $title,
                        d.content = $content,
                        d.url = $url,
                        d.source = 'enerv',
                        d.cluster = $cluster,
                        d.embedding = $embedding,
                        d.contentHash = $contentHash,
                        d.updatedAt = datetime()
                """, {
                    "id": chunk_id,
                    "title": f"{title} (part {i + 1})",
                    "content": chunks[i],
                    "url": abs_path,
                    "cluster": cluster,
                    "embedding": chunk_embedding,
                    "contentHash": content_hash
                })

            # 6. Build relations (similarity edges & cross-root wiki-links)
            click.echo("  [~] Building semantic connections and cross-root wiki-links...")
            
            # Similarity edges
            similar_res = session.run("""
                CALL db.index.vector.queryNodes('document_embeddings', 5, $embedding)
                YIELD node, score
                WHERE score >= 0.75
                RETURN node.id AS id, score
            """, {"embedding": first_embedding})
            
            edges_created = 0
            for record in similar_res:
                target_id = record["id"]
                score = record["score"]
                if target_id == doc_id:
                    continue
                session.run("""
                    MATCH (a:Document {id: $a}), (b:Document {id: $b})
                    MERGE (a)-[r:SIMILAR_TO]-(b)
                    SET r.score = $score
                """, {"a": doc_id, "b": target_id, "score": score})
                edges_created += 1

            # Cross-root wiki-links
            matches = re.findall(r"\[\[(tech|knowledge):([^\]]+)\]\]", content)
            links_created = 0
            for root_type, target_name in matches:
                target_name = target_name.strip()
                session.run("""
                    MATCH (a:Document {id: $a})
                    MATCH (b:Document)
                    WHERE (b.title CONTAINS $target OR b.cluster CONTAINS $target)
                      AND b.source CONTAINS $rootType
                    MERGE (a)-[r:REFERENCES {type: 'cross-root'}]->(b)
                """, {"a": doc_id, "target": target_name, "rootType": root_type})
                links_created += 1

            click.secho(f"\n🎉 Successfully Ingested locally!", fg="green", bold=True)
            click.echo(f"  -> Node ID: {doc_id}")
            click.echo(f"  -> Chunks Created: {len(chunks)}")
            click.echo(f"  -> Similarity Connections Linked: {edges_created}")
            click.echo(f"  -> Wiki-links resolved: {links_created}\n")
            
        driver.close()
    except Exception as e:
        click.secho(f"❌ Error during ingestion: {e}", fg="red")


