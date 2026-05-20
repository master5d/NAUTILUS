# Getting Started with Embedding Agent

Your personal AI knowledge graph. Ingest anything → it becomes a node → connections emerge automatically.

---

## Core Concepts

### Node
A **node** is a single piece of knowledge stored in the graph. Every time you ingest content, it becomes a node.

Types of nodes:
| Type | What it is | Example |
|------|-----------|---------|
| **Document** | An article, note, PDF chunk, or URL | "How to build a second brain" |
| **Cluster** | A folder or topic grouping | "productivity", "ai-research" |
| **Tag** | A keyword attached to documents | "zettelkasten" |
| **Highlight** | A saved quote or excerpt | Coming in Sprint 2 |

### Edge
An **edge** is a connection between two nodes. Edges are created automatically — you never draw them manually.

Types of edges:
| Edge | Meaning | How it's created |
|------|---------|-----------------|
| `SIMILAR_TO` | Two docs share similar ideas | Cosine similarity > 0.82 on embeddings |
| `BELONGS_TO` | Document belongs to a cluster | Set via `cluster` field on ingest |
| `TAGGED` | Document has a keyword | Set via `tags` field on ingest |

### Embedding
Before storing a node, the app converts its text into a **vector** — a list of 3072 numbers that represent the *meaning* of the content. Documents with similar meanings end up with similar vectors. This is how `SIMILAR_TO` edges are discovered automatically.

---

## Quick Start

### 1. Ingest your first document

Open the side panel → **Ingest** tab → paste any text or URL:

```
Source type:  text
Title:        My First Note
Content:      [paste your note here]
Cluster:      personal  (optional — groups related docs)
Tags:         ideas, thinking  (optional — comma separated)
```

Click **Ingest**. The app will:
1. Normalize and chunk your text
2. Generate a 3072-dimensional embedding via Gemini
3. Store it as a Document node in Neo4j
4. Search for similar existing documents → draw `SIMILAR_TO` edges automatically
5. Create a Cluster node if the cluster name is new

### 2. Explore the graph

The 3D graph loads automatically. Each node is a document. Each line is a connection.

- **Rotate**: click + drag
- **Zoom**: scroll
- **Click a node**: opens the content viewer on the right
- **Particle animations on edges**: show direction of similarity relationships
- **Node color**: corresponds to cluster (same cluster = same color)
- **↺ refresh**: reload the graph after ingesting new content

### 3. Search

**Search tab** → type a question or keyword → returns the most semantically similar nodes, not just keyword matches.

Example: searching "focus and productivity" will surface documents about deep work, distraction, flow state — even if they never use those exact words.

### 4. Ask the graph (GraphRAG)

**GraphRAG tab** → ask a question in natural language.

The system will:
1. Find the most relevant anchor nodes via vector search
2. Expand 1-2 hops through the graph (follow edges to neighbors)
3. Feed that subgraph context to Gemini
4. Stream back a synthesized answer with document citations

Example: *"What do I know about building habits?"* → the AI will synthesize ideas across all relevant notes and explain how they connect.

---

## Data Model

```
(:Document {id, title, content, url, source, cluster, embedding[]})
(:Cluster  {id, name})
(:Tag      {name})

(:Document)-[:SIMILAR_TO {score: 0.0–1.0}]->(:Document)
(:Document)-[:BELONGS_TO]->(:Cluster)
(:Document)-[:TAGGED]->(:Tag)
```

Everything lives in **Neo4j AuraDB** (free tier — 200k nodes, 400k edges).

---

## Tips

- **Same cluster = same color** in the graph. Use consistent cluster names to see topic islands emerge.
- **Short, focused notes work better than long documents** — they produce tighter embeddings and more precise similarity edges.
- **Ingest related content together** — if two docs share ideas, they'll automatically connect. If nothing connects, the graph is too sparse.
- **GraphRAG improves as you add more** — with 3 nodes it's a lookup; with 300 nodes it finds connections you forgot you made.
- The graph is **append-only by design** — re-ingesting the same URL/title updates the node in place (MERGE), it doesn't duplicate it.

---

## What's Next (Sprint 2)

- Readwise highlights import
- Browser web clipper
- Image + video embeddings
- Auto-Brainwriting per cluster
- Dynamic cluster emergence (Louvain algorithm)
