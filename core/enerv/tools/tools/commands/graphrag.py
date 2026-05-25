import click
import os
import requests
import json
from neo4j import GraphDatabase
from .ingest import load_nautilus_env, get_embedding, get_litellm_url

def fetch_subgraph_context(session, anchor_ids):
    """Retrieve 1-2 hop subgraph around anchor document nodes."""
    if not anchor_ids:
        return "No relevant nodes found in knowledge base."
        
    cypher = """
    MATCH (anchor:Document)
    WHERE anchor.id IN $ids
    OPTIONAL MATCH (anchor)-[r:SIMILAR_TO|BELONGS_TO|TAGGED]-(neighbor)
    RETURN anchor.id AS anchorId, anchor.title AS anchorTitle,
           anchor.content AS anchorContent,
           type(r) AS relType,
           CASE WHEN neighbor IS NOT NULL THEN neighbor.title ELSE null END AS neighborTitle,
           CASE WHEN neighbor IS NOT NULL THEN neighbor.id ELSE null END AS neighborId
    LIMIT 30
    """
    
    res = session.run(cypher, {"ids": anchor_ids})
    records = list(res)
    
    if not records:
        return "No context found for this query."
        
    lines = []
    seen = set()
    
    for r in records:
        anchor_title = r["anchorTitle"]
        anchor_content = r["anchorContent"]
        rel_type = r["relType"]
        neighbor_title = r["neighborTitle"]
        
        if anchor_title not in seen:
            seen.add(anchor_title)
            lines.append(f"📄 {anchor_title}")
            if anchor_content:
                lines.append(f"   {anchor_content.strip()[:300]}...")
                
        if rel_type and neighbor_title:
            lines.append(f"   → [{rel_type}] {neighbor_title}")
            
    return "\n".join(lines)

def ask_llm(prompt, env):
    """Ask LiteLLM gateway or fall back to direct Gemini API to stream/generate answer."""
    # Attempt 1: LiteLLM proxy
    try:
        litellm_url = get_litellm_url()
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "fast-pool",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        res = requests.post(f"{litellm_url}/v1/chat/completions", json=payload, headers=headers, timeout=30)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
    except Exception:
        pass

    # Attempt 2: Direct Google Gemini API
    api_key = env.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment. Start LiteLLM proxy or set key.")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    res = requests.post(url, json=payload, timeout=30)
    res.raise_for_status()
    return res.json()["candidates"][0]["content"]["parts"][0]["text"]

@click.command()
@click.argument('question')
@click.option('--top-k', default=5, type=int, help='Number of anchors to fetch')
def graphrag(question, top_k):
    """Perform GraphRAG to synthesize an answer to your question using the Knowledge Graph context."""
    if not question.strip():
        click.secho("❌ Error: Question cannot be empty.", fg="red")
        return

    click.secho(f"🤖 Processing GraphRAG reasoning for: '{question}'...", fg="cyan")

    # 1. Load Environment Variables
    env = load_nautilus_env()
    neo4j_uri = env.get("NEO4J_URI") or "neo4j+s://localhost:7687"
    neo4j_user = env.get("NEO4J_USERNAME") or "neo4j"
    neo4j_pass = env.get("NEO4J_PASSWORD")
    neo4j_db = env.get("NEO4J_DATABASE") or "neo4j"

    if not neo4j_pass:
        click.secho("❌ Error: NEO4J_PASSWORD not found in .env file.", fg="red")
        return

    # 2. Embed the question
    try:
        click.echo("  [~] Embedding question...")
        question_embedding = get_embedding(question, env)
    except Exception as e:
        click.secho(f"❌ Error generating embedding: {e}", fg="red")
        return

    # 3. Query database for anchors and subgraph context
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
        with driver.session(database=neo4j_db) as session:
            click.echo("  [~] Performing semantic search for anchor nodes...")
            
            cypher = """
            CALL db.index.vector.queryNodes('document_embeddings', $top_k, $embedding)
            YIELD node, score
            WHERE score >= 0.5
            RETURN node.id AS id
            """
            
            res = session.run(cypher, {"top_k": top_k, "embedding": question_embedding})
            anchor_ids = [r["id"] for r in res]
            
            click.echo(f"  [~] Expanding subgraph around {len(anchor_ids)} anchor(s)...")
            subgraph_ctx = fetch_subgraph_context(session, anchor_ids)
            
    except Exception as e:
        click.secho(f"❌ Database error: {e}", fg="red")
        return

    # 4. Formulate Prompt and Ask LLM
    prompt = f"""You are a knowledge assistant helping the user explore their personal knowledge base.

Answer the question thoughtfully using the graph context below. Your answer should:
- Synthesize ideas across multiple nodes when relevant
- Explain the *meaning* of connections, not just name them
- Reference specific documents and relationships to support your reasoning
- Be 2-4 paragraphs — substantive but focused

Format graph citations inline like: (📄 Document Title → [RELATION] → Document Title)

## Knowledge Graph Context:
{subgraph_ctx}

## Question:
{question}"""

    try:
        click.echo("  [~] Querying AI reasoning engine...")
        answer = ask_llm(prompt, env)
        click.secho("\n🧠 Synthesized Answer:\n", fg="green", bold=True)
        click.echo(answer)
    except Exception as e:
        click.secho(f"❌ LLM error: {e}", fg="red")
