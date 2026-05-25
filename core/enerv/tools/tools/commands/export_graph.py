import os
import sys
import json
import re
import click
from pathlib import Path

# Theme standard HSL mapping colors
CLUSTER_COLORS = {
    'file': '#4f46e5',
    'url': '#059669',
    'readwise': '#d97706',
    'highlight': '#dc2626',
    'calendar': '#0ea5e9',
    'default': '#6b7280',
}

def cluster_color(cluster: str) -> str:
    if not cluster:
        return CLUSTER_COLORS['default']
    
    cluster_lower = cluster.lower()
    for key, color in CLUSTER_COLORS.items():
        if key in cluster_lower:
            return color
            
    # Generate deterministic color from cluster name
    hash_val = 0
    for char in cluster:
        char_code = ord(char)
        hash_val = char_code + ((hash_val << 5) - hash_val)
        # Handle 32-bit signed int overflow
        hash_val = (hash_val + 2**31) % 2**32 - 2**31
        
    hue = abs(hash_val) % 360
    return f"hsl({hue}, 65%, 55%)"

def load_nautilus_env():
    """Dynamically load monorepo environment variables by traversing up."""
    env = {}
    current_dir = os.getcwd()
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

def get_vault_path(env):
    """Resolve active Obsidian vault path with standard fallbacks."""
    vault = env.get("OBSIDIAN_VAULT_PATH")
    if not vault or not os.path.exists(vault):
        options = [
            r"C:\Users\sasha\Downloads\Notes_ACE",
            r"C:\Users\sasha\life",
        ]
        for opt in options:
            if os.path.exists(opt):
                return opt
    return vault or r"C:\Users\sasha\Downloads\Notes_ACE"

def parse_frontmatter(raw: str):
    if not raw.startswith('---'):
        return {}, raw

    end = raw.find('\n---', 3)
    if end == -1:
        return {}, raw

    yaml_block = raw[4:end]
    body = raw[end + 4:].lstrip()

    meta = {}
    lines = yaml_block.split('\n')
    for line in lines:
        if ':' not in line:
            continue
        key, val = line.split(':', 1)
        key = key.strip()
        val = val.strip()
        if not key:
            continue

        if val.startswith('[') and val.endswith(']'):
            items = [item.strip().strip("'").strip('"') for item in val[1:-1].split(',')]
            meta[key] = [item for item in items if item]
        elif val:
            meta[key] = val.strip("'").strip('"')

    block_list_pattern = re.compile(r'^([\w-]+):\s*\n((?:\s+-\s+.+\n?)+)', re.MULTILINE)
    for match in block_list_pattern.finditer(yaml_block):
        key = match.group(1)
        items_raw = match.group(2)
        items = []
        for line in items_raw.split('\n'):
            line_stripped = line.strip()
            if line_stripped.startswith('-'):
                item_val = line_stripped[1:].strip().strip("'").strip('"')
                if item_val:
                    items.append(item_val)
        if items:
            meta[key] = items

    return meta, body

def extract_tags(meta, body):
    tags = []
    for key in ['tags', 'tag']:
        v = meta.get(key)
        if isinstance(v, list):
            tags.extend([str(item) for item in v])
        elif isinstance(v, str) and v:
            split_tags = re.split(r'[,\s]+', v)
            tags.extend([t for t in split_tags if t])

    inline_matches = re.finditer(r'(?:^|\s)#([\w/-]+)', body)
    for match in inline_matches:
        tags.append(match.group(1))

    cleaned_tags = []
    seen = set()
    for t in tags:
        t_clean = t.lower().lstrip('#')
        if t_clean and t_clean not in seen:
            seen.add(t_clean)
            cleaned_tags.append(t_clean)
    return cleaned_tags

def strip_obsidian_syntax(text, note_dir=None, vault_path=None):
    result = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
    result = re.sub(r'\[\[([^\]]+)\]\]', r'\1', result)
    result = re.sub(r'!\[\[[^\]]*\]\]', '', result)

    if note_dir and vault_path:
        abs_vault = os.path.abspath(vault_path)
        
        def replace_img(match):
            alt = match.group(1)
            img_path = match.group(2)
            if img_path.startswith('http'):
                return match.group(0)
            
            try:
                abs_img_path = os.path.abspath(os.path.join(note_dir, img_path))
                rel_path = os.path.relpath(abs_img_path, abs_vault)
                if '..' in rel_path:
                    return ''
                url_path = rel_path.replace('\\', '/')
                return f'![{alt}](/api/vault-image/{url_path})'
            except Exception:
                return ''
                
        result = re.sub(r'!\[([^\]]*)\]\((?!https?://)?([^)]+)\)', replace_img, result)
    else:
        result = re.sub(r'!\[([^\]]*)\]\((?!https?://)[^)]*\)', '', result)

    result = re.sub(r'==([^=]+)==', r'\1', result)
    result = re.sub(r'%%[\s\S]*?%%', '', result)
    result = re.sub(r'<!--[\s\S]*?-->', '', result)
    result = re.sub(r'```dataview[\s\S]*?```', '', result)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()

def normalize_id(file_path: str, vault_path: str) -> str:
    normalized_file = file_path.replace('\\', '/')
    normalized_vault = vault_path.replace('\\', '/')
    
    if normalized_file.startswith(normalized_vault):
        relative = normalized_file[len(normalized_vault):]
    else:
        relative = normalized_file
        
    relative = relative.lstrip('/')
    relative = re.sub(r'\.md$', '', relative)
    
    full_id = 'obsidian/' + relative
    full_id = full_id.lower()
    full_id = re.sub(r'\s+', '-', full_id)
    full_id = re.sub(r'[^a-z0-9\-/]', '', full_id)
    return full_id[:100]

@click.command(name="export-graph")
@click.option('--vault', type=click.Path(exists=True), help='Path to active Obsidian vault')
@click.option('--output', type=click.Path(), help='Filepath to write compiled JSON result to')
def export_graph(vault, output):
    """Compile and export offline-first Obsidian vault graph coordinates & links."""
    click.echo("🟣 Compiling offline 3D Knowledge Graph from vault...", err=True)
    
    env = load_nautilus_env()
    if not vault:
        vault = get_vault_path(env)
        
    if not os.path.exists(vault):
        click.secho(f"❌ Error: Vault path not found: {vault}", fg="red", err=True)
        sys.exit(1)
        
    abs_vault = os.path.abspath(vault)
    click.echo(f"📂 Scanning vault: {abs_vault}", err=True)
    
    skip_dirs = {".obsidian", ".trash", "_templates", "templates", "Template", "Templates"}
    skip_files = {"README.md", "CHANGELOG.md"}
    
    notes = []
    
    for root, dirs, files in os.walk(abs_vault):
        # Filter directories to skip hidden or template directories
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        
        # Calculate cluster name
        if root == abs_vault:
            cluster = "vault-root"
        else:
            rel_to_vault = os.path.relpath(root, abs_vault)
            parts = rel_to_vault.split(os.sep)
            cluster = parts[0] if parts else "vault-root"
            
        for f in files:
            if f.endswith('.md') and f not in skip_files:
                file_path = os.path.join(root, f)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as fh:
                        raw_content = fh.read()
                        
                    meta, body = parse_frontmatter(raw_content)
                    note_dir = os.path.dirname(file_path)
                    content = strip_obsidian_syntax(body, note_dir, abs_vault)
                    
                    if len(content) < 30:
                        continue
                        
                    title = meta.get('title') or f[:-3]
                    tags = extract_tags(meta, body)
                    
                    # Wiki links mentions
                    mentions = []
                    inline_matches = re.finditer(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', body)
                    for m in inline_matches:
                        mentions.append(m.group(1).strip())
                    unique_mentions = list(dict.fromkeys(mentions))
                    
                    notes.append({
                        'filePath': file_path,
                        'title': title,
                        'content': content,
                        'cluster': cluster,
                        'tags': tags,
                        'mentions': unique_mentions
                    })
                except Exception as e:
                    click.echo(f"⚠️ Warning: failed to parse note {file_path}: {e}", err=True)

    nodes = []
    links = []
    cluster_ids = set()
    title_to_id = {}
    
    # 1. Map document nodes
    for note in notes:
        doc_id = normalize_id(note['filePath'], abs_vault)
        title_to_id[note['title'].lower()] = doc_id
        
        nodes.append({
            'id': doc_id,
            'title': note['title'],
            'source': 'obsidian',
            'type': 'Document',
            'content': note['content'][:1000],
            'cluster': note['cluster'],
            'color': cluster_color(note['cluster']),
            'url': note['filePath'], # Critical absolute path for 'Open in Obsidian'
            'tags': note['tags']
        })
        
        if note['cluster'] and note['cluster'] != 'vault-root':
            cluster_ids.add(note['cluster'])
            
    # 2. Add Cluster nodes
    for cluster in cluster_ids:
        cluster_id = f"cluster:{cluster.lower().replace(' ', '-')}"
        nodes.append({
            'id': cluster_id,
            'title': cluster,
            'source': 'file',
            'type': 'Cluster',
            'cluster': cluster,
            'color': cluster_color(cluster)
        })
        
    # 3. Create BELONGS_TO and SIMILAR_TO (Mentions) links
    for note in notes:
        doc_id = normalize_id(note['filePath'], abs_vault)
        
        # Cluster link
        if note['cluster'] and note['cluster'] != 'vault-root':
            cluster_id = f"cluster:{note['cluster'].lower().replace(' ', '-')}"
            links.append({
                'source': doc_id,
                'target': cluster_id,
                'type': 'BELONGS_TO',
                'score': 0.5
            })
            
        # Mention reference links
        if note['mentions']:
            for mention in note['mentions']:
                # Clean mention like in TS (path slash split, pop, etc)
                clean_mention = mention.replace('\\', '/').split('/')[-1]
                if clean_mention.endswith('.md'):
                    clean_mention = clean_mention[:-3]
                
                target_id = title_to_id.get(clean_mention.lower())
                if target_id and target_id != doc_id:
                    links.append({
                        'source': doc_id,
                        'target': target_id,
                        'type': 'SIMILAR_TO',
                        'score': 0.8
                    })
                    
    graph_data = {
        'nodes': nodes,
        'links': links
    }
    
    output_json = json.dumps(graph_data, indent=2)
    
    if output:
        try:
            with open(output, 'w', encoding='utf-8') as out_f:
                out_f.write(output_json)
            click.secho(f"✔ Successfully exported graph data to: {output}", fg="green", err=True)
        except Exception as e:
            click.secho(f"❌ Error writing output file: {e}", fg="red", err=True)
            sys.exit(1)
    else:
        # Output clean JSON to stdout for Next.js to parse
        sys.stdout.write(output_json)
        sys.stdout.flush()

if __name__ == "__main__":
    export_graph()
