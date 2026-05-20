import os
import json
import time
import argparse
import logging
from pathlib import Path
from urllib.parse import quote
import requests
import fitz  # PyMuPDF
import docx
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ================= Configuration =================
LITELLM_URL = "http://localhost:11434/v1/chat/completions"
OBSIDIAN_DIR = Path("/mnt/c/Obsidian/life/Atlas/Notes/Library")
STATE_FILE = Path("/mnt/c/Warp Projects/Efforts/Ongoing/SOVRN/config/shadow_ingest_state.json")
MODEL_NAME = "hermes3:8b" 
MAX_CHARS = 6000 # Влезает до 2 000 токенов контекста. Идеально для Qwen/DeepSeek

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# ================= Helper Functions =================

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_state(processed_files):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(processed_files, f, ensure_ascii=False, indent=2)

def to_windows_uri(wsl_path: Path) -> str:
    parts = wsl_path.parts
    if len(parts) >= 3 and parts[1] == 'mnt':
        drive = parts[2].upper()
        rest = "/".join(parts[3:])
        return f"file:///{drive}:/{quote(rest)}"
    return f"file://{wsl_path}"

# ================= Semantic Skeleton Extraction =================

def extract_pdf_skeleton(path: Path) -> str:
    skeleton = []
    try:
        with fitz.open(path) as doc:
            # 1. Извлечение Метаданных (Автор, Название, Ключевики)
            meta = doc.metadata
            if meta:
                title = meta.get('title', '')
                author = meta.get('author', '')
                if title or author:
                    skeleton.append(f"--- METADATA ---\nTitle: {title}\nAuthor: {author}\n")
            
            # 2. Извлечение Оглавления (ToC / Bookmarks)
            toc = doc.get_toc()
            if toc:
                skeleton.append("--- TABLE OF CONTENTS ---")
                # Берем только первые 40 Глав/Разделов, чтобы не забить весь контекст
                for lvl, title, page in toc[:40]:
                    indent = "  " * (lvl - 1)
                    skeleton.append(f"{indent}- {title}")
                skeleton.append("\n")

            # 3. Smart Text Sampling (Введение и Выводы)
            skeleton.append("--- CONTENT SAMPLE ---")
            total_pages = len(doc)
            
            intro_text = ""
            # Берем первые 5 страниц (Аннотация/Предисловие)
            for i in range(1, min(6, total_pages)):
                intro_text += doc[i].get_text() + " "
                
            outro_text = ""
            # Если книга длинная (например 100 страниц), берем последние 2 (Выводы)
            if total_pages > 8:
                for i in range(total_pages - 2, total_pages):
                    outro_text += doc[i].get_text() + " "
                    
            if outro_text:
                combined = intro_text[:(MAX_CHARS//2)] + "\n\n... [СЕРЕДИНА КНИГИ ПРОПУЩЕНА ИИ-ПАРСЕРОМ] ...\n\n" + outro_text[-(MAX_CHARS//2):]
            else:
                combined = intro_text[:MAX_CHARS]
                
            skeleton.append(combined)

    except Exception as e:
        logging.error(f"Error reading PDF {path}: {e}")
        
    return "\n".join(skeleton)[:MAX_CHARS]

def extract_docx_skeleton(path: Path) -> str:
    try:
        doc = docx.Document(path)
        all_paras = [p.text for p in doc.paragraphs if p.text.strip()]
        if not all_paras: return ""
        
        # Берем 30 абзацев из начала и 15 из Конца
        head = "\n".join(all_paras[:30])
        tail = "\n".join(all_paras[-15:]) if len(all_paras) > 40 else ""
        
        text = "--- BEGINNING ---\n" + head
        if tail:
            text += "\n\n--- ENDING ---\n" + tail
        return text[:MAX_CHARS]
    except Exception as e:
        logging.error(f"Error reading DOCX {path}: {e}")
        return ""

def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == '.pdf':
        return extract_pdf_skeleton(path)
    elif ext in ['.doc', '.docx']:
        return extract_docx_skeleton(path)
    elif ext in ['.md', '.txt']:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                return (content[:MAX_CHARS//2] + "\n...[SKIP]...\n" + content[-MAX_CHARS//2:]) if len(content) > MAX_CHARS else content
        except:
            return ""
    return ""

# ================= AI Processing =================

def get_semantic_shadow(filename: str, text_sample: str) -> dict:
    if len(text_sample.strip()) < 50:
        text_sample = "Нет текста для анализа. Только название."

    prompt = f"""You are the ENERV Edge Ingest AI.
Analyze this book/document's Semantic Skeleton (Metadata, ToC, and Intro/Outro) and return ONLY a valid JSON object.
Filename: {filename}

Document Skeleton:
{text_sample}

Required JSON fields:
- identity: Short title of the document (3-7 words, NO extensions)
- intent: 'knowledge_ingest'
- context: 'Atlas/Notes/Library'
- signal: low | medium | high (based on usefulness)
- tags: [3-5 related lowercase tags based strictly on the ToC and content]
- summary: A 2-sentence summary of what this document is about.
"""
    try:
        resp = requests.post(
            LITELLM_URL,
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            },
            timeout=30
        )
        if resp.status_code == 200:
            content = resp.json()['choices'][0]['message']['content']
            return json.loads(content)
        else:
            logging.error(f"LLM API Error: {resp.text}")
    except Exception as e:
        logging.error(f"Failed to reach LLM: {e}")
    
    # Fallback
    return {
        "identity": filename.split('.')[0],
        "intent": "knowledge_ingest",
        "context": "Atlas/Notes/Library",
        "signal": "medium",
        "tags": ["untagged"],
        "summary": "Автоматически заархивировано без ИИ."
    }

# ================= ACE Builder & Watchdog =================

def create_markdown(file_path: Path, ai_data: dict):
    now = time.gmtime()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", now)
    file_id = time.strftime("%Y%m%d%H%M%S", now)
    
    tags_str = ", ".join(ai_data.get('tags', []))
    loc_uri = to_windows_uri(file_path)
    
    md_content = f"""---
id: {file_id}
timestamp: {timestamp}
facets:
  identity: {ai_data.get('identity', 'Unknown')}
  intent: {ai_data.get('intent')}
  context: {ai_data.get('context')}
  signal: {ai_data.get('signal')}
source: edge_node
tags: [{tags_str}]
---
# {ai_data.get('identity')}

**Источник:** [🔗 Открыть оригинальный файл]({loc_uri})
**Оригинальное имя:** `{file_path.name}`

> {ai_data.get('summary', '')}

---
*Generated by ENERV Local Edge Ingest*
"""
    safe_name = ai_data.get('identity', 'Unknown').replace(" ", "_").replace("/", "").replace("\\", "")
    out_file = OBSIDIAN_DIR / f"{file_id}_{safe_name[:40]}.md"
    
    OBSIDIAN_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    logging.info(f"Created shadow: {out_file.name}")

processed = load_state()

def process_file(file_path: Path):
    if str(file_path) in processed:
        return
    
    ext = file_path.suffix.lower()
    if ext not in ['.pdf', '.docx', '.epub', '.md', '.txt']:
        return
    
    logging.info(f"Processing (Skeleton Mode): {file_path.name}...")
    
    text_sample = extract_text(file_path)
    ai_data = get_semantic_shadow(file_path.name, text_sample)
    create_markdown(file_path, ai_data)
    
    processed.append(str(file_path))
    save_state(processed)

def batch_scan(directory: Path):
    for root, _, files in os.walk(directory):
        for file in files:
            process_file(Path(root) / file)

class EdgeFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            time.sleep(2)
            process_file(Path(event.src_path))

def start_watchdog(directory: Path):
    event_handler = EdgeFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(directory), recursive=True)
    observer.start()
    logging.info(f"Watchdog started monitoring: {directory}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ENERV Edge Semantic Ingest")
    parser.add_argument("--scan", type=str, help="Directory to scan in batch mode")
    parser.add_argument("--watch", type=str, help="Directory to watch in daemon mode")
    args = parser.parse_args()

    if args.scan:
        logging.info(f"Starting BATCH scan on {args.scan}")
        batch_scan(Path(args.scan))
    elif args.watch:
        start_watchdog(Path(args.watch))
    else:
        parser.print_help()