import glob
import os
import json
import argparse
import logging
from pathlib import Path
from urllib.parse import quote
import requests
import fitz  # PyMuPDF
import docx

LITELLM_URL = "http://localhost:11434/v1/chat/completions"
MODEL_NAME = "hermes3:8b" 
MAX_CHARS = 24000   # Большой контекст для глубокого анализа
OBSIDIAN_DIR = Path("/mnt/c/Obsidian/life/Atlas/Notes/Deep_Refs")

logging.basicConfig(level=logging.INFO, format="%(message)s")

def extract_pdf_deep(path: Path) -> str:
    text = ""
    try:
        with fitz.open(path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
    except Exception as e:
        logging.error(f"Error reading PDF {path}: {e}")
    return text

def extract_docx_deep(path: Path) -> str:
    text = ""
    try:
        doc = docx.Document(path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        logging.error(f"Error DOCX {path}: {e}")
    return text

def to_windows_uri(wsl_path: Path) -> str:
    parts = wsl_path.parts
    if len(parts) >= 3 and parts[1] == 'mnt':
        return f"file:///{parts[2].upper()}:/{quote('/'.join(parts[3:]))}"
    return f"file://{wsl_path}"

def get_deep_shadow(filename: str, text: str) -> dict:
    # Обрезаем до лимита контекста 
    content = text[:MAX_CHARS]
    
    prompt = f"""You are the ENERV Deep Knowledge Extractor.
Extract extremely detailed context from this project reference document to help an AI agent write a complete PRD (Product Requirements Document/Architecture).

Filename: {filename}

Document Content:
{content}

Respond only with a JSON object containing:
- identity: Short title (no extension)
- intent: 'project_reference'
- context: 'Atlas/Notes/Projects'
- tags: [5-10 strict semantic tags]
- deep_summary: A 100-200 word summary of the methodology, framework, or content.
- key_principles: Array of 3-7 core principles, rules, or formulas found in the text.
- actionable_insights: Array of 3-7 specific steps or ideas that can be applied to a new project.
"""
    try:
        resp = requests.post(
            LITELLM_URL,
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            },
            timeout=120
        )
        return json.loads(resp.json()['choices'][0]['message']['content'])
    except Exception as e:
        logging.error(f"LLM Error: {e}")
        return {"identity": filename.split('.')[0], "deep_summary": "Error parsing."}

def process_file(file_path: Path):
    # Skip if already exists
    safe_name = file_path.stem[:30].replace(" ", "_")
    existing = glob.glob(f"{OBSIDIAN_DIR}/*_DEEP_{safe_name}*.md")
    if existing:
        logging.info(f"Skipping (already deep ingested): {file_path.name}")
        return

    ext = file_path.suffix.lower()
    if ext not in ['.pdf', '.docx', '.epub', '.md', '.txt']: return
    
    logging.info(f"Deep Processing: {file_path.name}")
    
    if ext == '.pdf': text = extract_pdf_deep(file_path)
    elif ext in ['.doc', '.docx']: text = extract_docx_deep(file_path)
    else: text = open(file_path, 'r', encoding='utf-8', errors='ignore').read()
        
    ai_data = get_deep_shadow(file_path.name, text)
    
    file_id = time.strftime("%Y%m%d%H%M%S", time.gmtime())
    tags = ", ".join(ai_data.get('tags', []))
    loc = to_windows_uri(file_path)
    
    principles = "\n".join([f"- {p}" for p in (ai_data.get('key_principles') or [])])
    insights = "\n".join([f"- {i}" for i in (ai_data.get('actionable_insights') or [])])
    
    md_content = f"""---
id: {file_id}
facets:
  identity: {ai_data.get('identity', 'Unknown')}
  intent: {ai_data.get('intent', 'project_reference')}
  context: {ai_data.get('context', 'Atlas/Notes/Projects')}
source: deep_ingest
tags: [{tags}]
---
# {ai_data.get('identity')}

**Source:** [🔗 Open Original]({loc})

### 📖 Deep Summary
{ai_data.get('deep_summary', '')}

### ⚖️ Key Principles / Rules
{principles}

### 🚀 Actionable Insights for PRD/Project
{insights}

---
*Deep Extraction via ENERV*"""
    
    out = OBSIDIAN_DIR / f"{file_id}_DEEP_{ai_data.get('identity', 'Unknown')[:30].replace(' ', '_')}.md"
    OBSIDIAN_DIR.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(md_content)
    logging.info(f"Saved: {out.name}")

if __name__ == "__main__":
    import sys, time
    d = Path(sys.argv[1])
    for root, _, files in os.walk(d):
        for f in files:
            process_file(Path(root) / f)
