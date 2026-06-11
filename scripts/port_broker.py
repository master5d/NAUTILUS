# scripts/port_broker.py
# Nautilus Dynamic Port Broker & Service Registry
# Phase 1, P4 — Agentic AI v3.4 (Nautilus Rebrand)
# Automatically checks for free ports and keeps all system environment files in perfect sync.

import socket
import json
import os
import sys
import re

REGISTRY_PATH = r"C:\telo\Efforts\Ongoing\NAUTILUS\config\services.json"
ROOT_ENV_PATH = r"C:\telo\Efforts\Ongoing\NAUTILUS\.env"
APP_ENV_PATH = r"C:\telo\Efforts\Ongoing\NAUTILUS\apps\knowledge-graph\.env.local"
HERMES_CONFIG_PATH = os.path.expandvars(r"%USERPROFILE%\.hermes\config.yaml")

def get_free_port(start_port):
    """Scan for a free TCP port starting from start_port."""
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                # NO SO_REUSEADDR: on Windows it lets bind() succeed on a port
                # that is already LISTENing — the probe would report busy ports
                # as free (root cause of duplicate service instances).
                s.bind(("127.0.0.1", port))
                return port
            except socket.error:
                port += 1
    raise IOError("No free ports available.")

def register_service(name, port):
    """Save the active port allocation to the central services registry JSON."""
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    data = {}
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            pass
            
    data[name] = {
        "port": port,
        "url": f"http://localhost:{port}"
    }
    
    with open(REGISTRY_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    print(f"✓ Service '{name}' registered in services.json on port {port}", file=sys.stderr)

def update_env_file(file_path, key, value):
    """Safely update or insert an environment variable in an env file."""
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(f"{key}={value}\n")
        print(f"  [+] Created {os.path.basename(file_path)} with {key}={value}", file=sys.stderr)
        return
        
    with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
        lines = fh.readlines()
        
    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(line)
            
    if not updated:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"
        new_lines.append(f"{key}={value}\n")
        
    with open(file_path, "w", encoding="utf-8") as fh:
        fh.writelines(new_lines)
    print(f"  [~] Updated {os.path.basename(file_path)}: {key}={value}", file=sys.stderr)

def update_hermes_yaml(file_path, base_url):
    """Safely update the base_url inside Hermes config.yaml using regex."""
    if not os.path.exists(file_path):
        print(f"  [-] Skipped Hermes sync: config file not found at {file_path}", file=sys.stderr)
        return
        
    with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
        content = fh.read()
        
    # Match "base_url: <anything>"
    pattern = r"^(\s*base_url\s*:\s*)(.*)$"
    updated, count = re.subn(pattern, rf"\g<1>\"{base_url}\"", content, flags=re.MULTILINE)
    
    if count > 0:
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(updated)
        print(f"  [~] Dynamic port synchronized to Hermes config: {base_url}", file=sys.stderr)
    else:
        # If the key base_url isn't in config.yaml, let's append it inside the models section or end
        with open(file_path, "a", encoding="utf-8") as fh:
            fh.write(f"\nbase_url: \"{base_url}\"\n")
        print(f"  [+] Appended base_url to Hermes config: {base_url}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python port_broker.py <service_name> <default_port>", file=sys.stderr)
        sys.exit(1)
        
    service_name = sys.argv[1].lower()
    default_port = int(sys.argv[2])
    
    # 1. Detect dynamic port
    try:
        allocated_port = get_free_port(default_port)
    except Exception as e:
        print(f"❌ Failed to find free port: {e}", file=sys.stderr)
        sys.exit(2)
        
    # 2. Register service
    register_service(service_name, allocated_port)
    
    # 3. Synchronize environment files based on the service launched
    if service_name == "litellm":
        # Synchronize LiteLLM Proxy endpoint
        url = f"http://localhost:{allocated_port}"
        # Update root env and Next.js env
        update_env_file(ROOT_ENV_PATH, "LITELLM_PORT", str(allocated_port))
        update_env_file(ROOT_ENV_PATH, "LITELLM_URL", url)
        update_env_file(APP_ENV_PATH, "NEXT_PUBLIC_LITELLM_URL", url)
        # Update Hermes config.yaml in Windows User Profile (so WSL2 mirrored networking connects)
        update_hermes_yaml(HERMES_CONFIG_PATH, f"http://localhost:{allocated_port}/v1")
        
    elif service_name == "llama-server":
        # Synchronize llama-server endpoint
        url = f"http://127.0.0.1:{allocated_port}"
        update_env_file(ROOT_ENV_PATH, "LLAMA_SERVER_PORT", str(allocated_port))
        update_env_file(ROOT_ENV_PATH, "LLAMA_SERVER_URL", url)
        update_env_file(APP_ENV_PATH, "NEXT_PUBLIC_LLAMA_SERVER_URL", url)
        
    elif service_name == "knowledge-graph":
        # Synchronize Next.js UI web port
        url = f"http://localhost:{allocated_port}"
        update_env_file(ROOT_ENV_PATH, "NEXT_PUBLIC_PORT", str(allocated_port))
        update_env_file(ROOT_ENV_PATH, "NEXT_PUBLIC_APP_URL", url)
        
    # 4. Print the final port to stdout so calling shell scripts can capture it
    print(allocated_port)
