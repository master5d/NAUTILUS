import os
import sys
import time
import json
import subprocess
from pathlib import Path

# Paths
REGISTRY_PATH = r"C:\telo\Efforts\Ongoing\NAUTILUS\config\services.json"
STATE_DIR = r"C:\telo\Efforts\Ongoing\NAUTILUS\.hermes"
STATE_FILE = os.path.join(STATE_DIR, "watcher_state.json")

def load_nautilus_env():
    """Dynamically load monorepo environment variables."""
    env = {}
    current_dir = os.path.abspath(os.path.dirname(__file__))
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
    """Resolve active Obsidian vault path."""
    vault = env.get("OBSIDIAN_VAULT_PATH")
    if not vault or not os.path.exists(vault):
        # Fallbacks
        options = [
            r"C:\Users\sasha\Downloads\Notes_ACE",
            r"C:\Users\sasha\life",
            r"C:\Users\sasha\Downloads\Notes_ACE"
        ]
        for opt in options:
            if os.path.exists(opt):
                return opt
    return vault or r"C:\Users\sasha\Downloads\Notes_ACE"

def load_state():
    """Load previously recorded file modification timestamps."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return {}

def save_state(state):
    """Save file modification timestamps."""
    os.makedirs(STATE_DIR, exist_ok=True)
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
    except Exception as e:
        print(f"Error saving state: {e}", file=sys.stderr)

def main():
    print("🟣 Nautilus Obsidian Vault Watcher bootstrap starting...", flush=True)
    env = load_nautilus_env()
    vault = get_vault_path(env)
    
    if not os.path.exists(vault):
        print(f"❌ Error: Vault path not found: {vault}", file=sys.stderr, flush=True)
        sys.exit(1)
        
    print(f"📂 Actively watching vault: {vault}", flush=True)
    
    # Load past timestamps state
    state = load_state()
    first_run = not bool(state)
    
    if first_run:
        print("  [~] First run: indexing initial files to prevent API rate-limiting storms...", flush=True)
        
    # Python path setup for executing CLI commands
    cli_env = os.environ.copy()
    cli_env["PYTHONPATH"] = r"C:\telo\Efforts\Ongoing\NAUTILUS\core\enerv\tools"
    
    # Skips
    skip_dirs = {".obsidian", ".trash", "_templates", "templates", "Template", "Templates"}
    
    while True:
        try:
            current_files = {}
            for root, dirs, files in os.walk(vault):
                # Filter skip directories
                dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
                
                for f in files:
                    if f.endswith(".md") and f not in {"README.md", "CHANGELOG.md"}:
                        path = os.path.join(root, f)
                        try:
                            mtime = os.path.getmtime(path)
                            current_files[path] = mtime
                        except Exception:
                            pass
            
            # Detect changes
            changes_detected = False
            for path, mtime in current_files.items():
                prev_mtime = state.get(path)
                
                if prev_mtime is None:
                    # New file
                    state[path] = mtime
                    changes_detected = True
                    if not first_run:
                        print(f"🆕 New note detected: {path}. Ingesting...", flush=True)
                        subprocess.run(["facet", "ingest", path], env=cli_env, shell=True)
                elif mtime > prev_mtime:
                    # Modified file
                    state[path] = mtime
                    changes_detected = True
                    if not first_run:
                        print(f"📝 Modified note detected: {path}. Re-ingesting...", flush=True)
                        subprocess.run(["facet", "ingest", path], env=cli_env, shell=True)
            
            # Clean up deleted files from state
            deleted_paths = [p for p in state if p not in current_files]
            if deleted_paths:
                for p in deleted_paths:
                    del state[p]
                changes_detected = True
                print(f"🗑 Removed {len(deleted_paths)} deleted note(s) from watcher state.", flush=True)
                
            if changes_detected:
                save_state(state)
                
            if first_run:
                print(f"✓ Watcher state initialized with {len(state)} files. Watching dynamically...", flush=True)
                first_run = False
                
            # Sleep to prevent high CPU utilization
            time.sleep(2.5)
            
        except KeyboardInterrupt:
            print("\nShutting down Nautilus Vault Watcher...", flush=True)
            break
        except Exception as e:
            print(f"⚠️ Watcher loop error: {e}", file=sys.stderr, flush=True)
            time.sleep(5)

if __name__ == "__main__":
    main()
