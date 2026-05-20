# HuggingFace A+B Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add HuggingFace Hub as a commit-hash-pinned GGUF model registry and HF Serverless Inference as the 5th fallback in LiteLLM, with a `hf` Hermes skill exposing four management commands over Telegram.

**Architecture:** `HF_TOKEN` propagates to WSL `~/.bashrc`, Hermes `.env`, and Windows env. `~/.hermes/models.yaml` becomes the single manifest for local GGUF models, pinned by full commit hash. Two HF Serverless models (`hf-hermes-70b`, `hf-qwen-72b`) are inserted into LiteLLM's fallback chain between `fast-pool` and `local-fallback`. A `hf` bash script in `~/.hermes/skills/hf-models/` exposes `status / check / download / pin` commands, linked to `/usr/local/bin/hf`.

**Tech Stack:** `huggingface-cli` (in Hermes venv), `urllib.request` + `PyYAML` (stdlib + system), LiteLLM 1.57.4 with `huggingface/` provider prefix, bash

---

### Task 1: Create HF Read-Only Token (Manual Step)

**Files:** None (external action only)

- [ ] **Step 1: Create the token**

  Open: https://huggingface.co/settings/tokens → **New token** → Type: **Read** → Name: `SOVRN-read` → Generate.

  Copy the token value (starts with `hf_`). Store it in your password manager — you'll need it for the next 3 steps.

- [ ] **Step 2: Verify the token works**

  ```bash
  curl -s "https://huggingface.co/api/whoami" \
    -H "Authorization: Bearer hf_YOUR_TOKEN_HERE" | python3 -m json.tool
  ```

  Expected: JSON with `"name": "your_username"` — HTTP 200, no 401.

---

### Task 2: Propagate HF_TOKEN + Enable hf-transfer

**Files:**
- Modify: `/root/.bashrc` (WSL)
- Modify: `/root/.hermes/.env`
- Modify: `C:\Users\sasha\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`

- [ ] **Step 1: Add to WSL ~/.bashrc**

  ```bash
  cat >> ~/.bashrc << 'EOF'

  # HuggingFace Hub
  export HF_TOKEN="hf_YOUR_TOKEN_HERE"
  export HF_HUB_ENABLE_HF_TRANSFER=1
  EOF
  source ~/.bashrc
  echo "HF_TOKEN set: ${HF_TOKEN:0:8}..."
  ```

  Expected: `HF_TOKEN set: hf_abcde...`

- [ ] **Step 2: Verify hf-transfer is importable**

  ```bash
  python3 -c "import hf_transfer; print('hf-transfer OK')"
  ```

  Expected: `hf-transfer OK`

  If `ModuleNotFoundError`:
  ```bash
  pip install hf-transfer -q && python3 -c "import hf_transfer; print('OK')"
  ```

- [ ] **Step 3: Fill HF_TOKEN in Hermes .env**

  The entry `HF_TOKEN=` already exists in `.env` — just fill it:

  ```bash
  sed -i 's/^HF_TOKEN=.*/HF_TOKEN=hf_YOUR_TOKEN_HERE/' /root/.hermes/.env
  grep "^HF_TOKEN" /root/.hermes/.env
  ```

  Expected: `HF_TOKEN=hf_YOUR_TOKEN_HERE`

- [ ] **Step 4: Add to Windows PowerShell profile**

  Add this line to `C:\Users\sasha\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`:

  ```powershell
  $env:HF_TOKEN = "hf_YOUR_TOKEN_HERE"
  ```

  Reload: `. $PROFILE`

  Verify: `$env:HF_TOKEN.Substring(0,8)`  → `hf_abcde`

- [ ] **Step 5: Verify huggingface-cli is in PATH (WSL)**

  ```bash
  which huggingface-cli
  ```

  Expected: `/usr/local/lib/hermes-agent/venv/bin/huggingface-cli` or similar.

  If `not found`, add the Hermes venv bin to PATH:

  ```bash
  echo 'export PATH="/usr/local/lib/hermes-agent/venv/bin:$PATH"' >> ~/.bashrc
  source ~/.bashrc
  which huggingface-cli
  ```

---

### Task 3: Create ~/.hermes/models.yaml

**Files:**
- Create: `/root/.hermes/models.yaml`

- [ ] **Step 1: Get current commit hash for the GGUF repo**

  ```bash
  HASH=$(curl -s "https://huggingface.co/api/models/unsloth/Qwen3-Coder-30B-A3B-GGUF" \
    -H "Authorization: Bearer $HF_TOKEN" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['sha'])")
  echo "Commit hash: $HASH"
  ```

  Expected: 40-character hex string like `a1b2c3d4e5f6...`. This is the value for `revision`.

- [ ] **Step 2: Create models.yaml**

  ```bash
  cat > ~/.hermes/models.yaml << EOF
  models:
    - name: Qwen3-Coder-30B-A3B
      repo: unsloth/Qwen3-Coder-30B-A3B-GGUF
      revision: ${HASH}
      file: Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf
      path: /mnt/c/Users/sasha/models
  EOF
  ```

- [ ] **Step 3: Verify**

  ```bash
  cat ~/.hermes/models.yaml
  ```

  Expected: YAML with a 40-char hex string as `revision` — never the string `"main"`.

---

### Task 4: Add HF Models to LiteLLM

**Files:**
- Modify: `C:\telo\Efforts\Ongoing\SOVRN\config\litellm-config.yaml`
- Modify: `C:\telo\Atlas\Scripts\hermes_startup.ps1`

- [ ] **Step 1: Add HF model entries to litellm-config.yaml**

  After the `local-fallback` entry (around line 70), before the `# --- Reasoning models` block, insert:

  ```yaml
    # --- HF Serverless Inference (5th fallback, free tier, ~5-30s cold start) ---
    - model_name: hf-hermes-70b
      litellm_params:
        model: huggingface/NousResearch/Hermes-3-Llama-3.1-70B
        api_key: os.environ/HF_TOKEN
        api_base: https://api-inference.huggingface.co/v1

    - model_name: hf-qwen-72b
      litellm_params:
        model: huggingface/Qwen/Qwen2.5-72B-Instruct
        api_key: os.environ/HF_TOKEN
        api_base: https://api-inference.huggingface.co/v1
  ```

- [ ] **Step 2: Update the fallback chain in litellm_settings**

  **Before** (current `fallbacks` block, lines ~86-89):
  ```yaml
  fallbacks:
    - {"google/gemini-3-flash-preview": ["fast-pool", "local-fallback"]}
    - {"fast-pool": ["local-fallback"]}
    - {"reasoning": ["reasoning-local"]}
  ```

  **After:**
  ```yaml
  fallbacks:
    - {"google/gemini-3-flash-preview": ["fast-pool", "hf-hermes-70b", "local-fallback"]}
    - {"fast-pool": ["hf-hermes-70b", "local-fallback"]}
    - {"hf-hermes-70b": ["hf-qwen-72b", "local-fallback"]}
    - {"hf-qwen-72b": ["local-fallback"]}
    - {"reasoning": ["reasoning-local"]}
  ```

- [ ] **Step 3: Add --config flag to hermes_startup.ps1**

  The current LiteLLM launch block (around line 83-87) does not pass `--config`. Fix it.

  **Before** (around line 83):
  ```powershell
  $log = LogPath "lite_llm"
  Start-Process -FilePath $litellmExe -ArgumentList @("--host","127.0.0.1","--port","4000") `
      -RedirectStandardOutput $log.out -RedirectStandardError $log.err -NoNewWindow
  ```

  **After:**
  ```powershell
  $log = LogPath "lite_llm"
  $litellmConfig = Join-Path $projectRoot "Efforts/Ongoing\SOVRN\config\litellm-config.yaml"
  Start-Process -FilePath $litellmExe `
      -ArgumentList @("--config", $litellmConfig, "--host", "127.0.0.1", "--port", "4000") `
      -RedirectStandardOutput $log.out -RedirectStandardError $log.err -NoNewWindow
  ```

- [ ] **Step 4: Restart LiteLLM with the updated config (PowerShell)**

  ```powershell
  Stop-Process -Name "litellm" -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 3

  $env:HF_TOKEN = "hf_YOUR_TOKEN_HERE"
  $configPath = "C:\telo\Efforts\Ongoing\SOVRN\config\litellm-config.yaml"
  Start-Process `
    -FilePath "C:\Users\sasha\AppData\Local\Programs\Python\Python313\Scripts\litellm.exe" `
    -ArgumentList @("--config", $configPath, "--host", "127.0.0.1", "--port", "4000") `
    -NoNewWindow
  Start-Sleep -Seconds 20
  ```

- [ ] **Step 5: Verify HF models are registered**

  ```powershell
  (Invoke-WebRequest "http://127.0.0.1:4000/v1/models" -UseBasicParsing).Content |
    python3 -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin)['data']]"
  ```

  Expected output includes lines: `hf-hermes-70b` and `hf-qwen-72b`

- [ ] **Step 6: Test a live HF inference call**

  ```bash
  curl -s http://127.0.0.1:4000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"hf-hermes-70b","messages":[{"role":"user","content":"Reply with exactly: HF OK"}],"max_tokens":10}' \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
  ```

  Expected: `HF OK` (allow 5-30s on cold start — this is a serverless endpoint)

- [ ] **Step 7: Commit**

  ```bash
  cd "C:/telo"
  git add "Efforts/Ongoing/SOVRN/config/litellm-config.yaml" "Atlas/Scripts/hermes_startup.ps1"
  git commit -m "feat(SOVRN): add HF Serverless as 5th fallback in LiteLLM (A+B)"
  ```

---

### Task 5: Create hf-models Hermes Skill

**Files:**
- Create: `/root/.hermes/skills/hf-models/SKILL.md`
- Create: `/root/.hermes/skills/hf-models/hf` (executable bash script)

- [ ] **Step 1: Create directory + verify PyYAML**

  ```bash
  mkdir -p ~/.hermes/skills/hf-models
  python3 -c "import yaml; print('PyYAML OK')" 2>/dev/null || pip3 install pyyaml -q
  python3 -c "import yaml; print('PyYAML OK')"
  ```

  Expected: `PyYAML OK`

- [ ] **Step 2: Create SKILL.md**

  Create `/root/.hermes/skills/hf-models/SKILL.md`:

  ```markdown
  ---
  name: HF Model Manager
  type: tool
  execution: stateful
  description: Download, pin, and verify GGUF models from HuggingFace Hub.
  
  ## Side Effects
  - Writes to ~/.hermes/models.yaml
  - Downloads files to /mnt/c/Users/sasha/models/
  
  ## Commands
  - hf status   → show models.yaml, current hashes, disk usage
  - hf check    → compare local hashes with latest on Hub
  - hf download <model-name>  → download via manifest with progress
  - hf pin <model-name> <hash>  → update revision in models.yaml
  ---
  
  Use the `hf` command to manage local GGUF models from HuggingFace Hub.
  
  Examples:
  - "hf status" — show registered models and their disk usage
  - "hf check" — check if newer versions are available on HuggingFace Hub
  - "hf download Qwen3-Coder-30B-A3B" — download the model per manifest
  - "hf pin Qwen3-Coder-30B-A3B abc123def456..." — pin to a specific commit hash
  ```

- [ ] **Step 3: Create the `hf` executable bash script**

  Create `/root/.hermes/skills/hf-models/hf`:

  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  
  MODELS_YAML="$HOME/.hermes/models.yaml"
  COMMAND="${1:-status}"
  
  case "$COMMAND" in
    status)
      echo "=== ~/.hermes/models.yaml ==="
      cat "$MODELS_YAML"
      echo ""
      echo "=== Disk usage ==="
      python3 - "$MODELS_YAML" << 'PYEOF'
  import sys, yaml, os
  with open(sys.argv[1]) as f:
      data = yaml.safe_load(f)
  for m in data['models']:
      filepath = os.path.join(m['path'], m['file'])
      if os.path.exists(filepath):
          size_gb = os.path.getsize(filepath) / (1024**3)
          print(f"  {m['name']}: {size_gb:.1f} GB  [rev: {m['revision'][:8]}...]")
      else:
          print(f"  {m['name']}: NOT FOUND  (expected: {filepath})")
  PYEOF
      ;;
  
    check)
      echo "=== HuggingFace Hub version check ==="
      python3 - "$MODELS_YAML" << 'PYEOF'
  import sys, yaml, json, urllib.request, os
  token = os.environ.get('HF_TOKEN', '')
  with open(sys.argv[1]) as f:
      data = yaml.safe_load(f)
  for m in data['models']:
      req = urllib.request.Request(
          f"https://huggingface.co/api/models/{m['repo']}",
          headers={"Authorization": f"Bearer {token}"}
      )
      with urllib.request.urlopen(req) as r:
          info = json.loads(r.read())
      latest = info.get('sha', 'unknown')
      pinned = m['revision']
      if pinned == latest:
          status = "UP TO DATE"
      else:
          status = f"UPDATE AVAILABLE → {latest[:8]}..."
      print(f"  {m['name']}: pinned={pinned[:8]}...  {status}")
  PYEOF
      ;;
  
    download)
      MODEL_NAME="${2:-}"
      if [ -z "$MODEL_NAME" ]; then
        echo "Usage: hf download <model-name>"
        echo "Available models:"
        python3 -c "import yaml; d=yaml.safe_load(open('$MODELS_YAML')); [print(' -', m['name']) for m in d['models']]"
        exit 1
      fi
      python3 - "$MODELS_YAML" "$MODEL_NAME" << 'PYEOF'
  import sys, yaml, subprocess
  with open(sys.argv[1]) as f:
      data = yaml.safe_load(f)
  name = sys.argv[2]
  models = {m['name']: m for m in data['models']}
  if name not in models:
      print(f"Model not found: {name}")
      print(f"Available: {list(models.keys())}")
      sys.exit(1)
  m = models[name]
  cmd = [
      'huggingface-cli', 'download',
      m['repo'], m['file'],
      '--revision', m['revision'],
      '--local-dir', m['path']
  ]
  print(f"Downloading {name}...")
  print(f"Command: {' '.join(cmd)}")
  subprocess.run(cmd, check=True)
  print(f"Done → {m['path']}/{m['file']}")
  PYEOF
      ;;
  
    pin)
      MODEL_NAME="${2:-}"
      NEW_HASH="${3:-}"
      if [ -z "$MODEL_NAME" ] || [ -z "$NEW_HASH" ]; then
        echo "Usage: hf pin <model-name> <hash>"
        exit 1
      fi
      python3 - "$MODELS_YAML" "$MODEL_NAME" "$NEW_HASH" << 'PYEOF'
  import sys, yaml
  models_file, name, new_hash = sys.argv[1], sys.argv[2], sys.argv[3]
  with open(models_file) as f:
      data = yaml.safe_load(f)
  found = False
  for m in data['models']:
      if m['name'] == name:
          old_hash = m['revision']
          m['revision'] = new_hash
          found = True
          print(f"Pinned {name}: {old_hash[:8]}... → {new_hash[:8]}...")
          break
  if not found:
      print(f"Model not found: {name}")
      print(f"Available: {[m['name'] for m in data['models']]}")
      sys.exit(1)
  with open(models_file, 'w') as f:
      yaml.dump(data, f, default_flow_style=False, sort_keys=False)
  print("models.yaml updated.")
  PYEOF
      ;;
  
    *)
      echo "Unknown command: $COMMAND"
      echo "Usage: hf <status|check|download <name>|pin <name> <hash>>"
      exit 1
      ;;
  esac
  ```

- [ ] **Step 4: Make executable and link to PATH**

  ```bash
  chmod +x ~/.hermes/skills/hf-models/hf
  sudo ln -sf ~/.hermes/skills/hf-models/hf /usr/local/bin/hf
  which hf
  ```

  Expected: `/usr/local/bin/hf`

- [ ] **Step 5: Test `hf status`**

  ```bash
  hf status
  ```

  Expected:
  ```
  === ~/.hermes/models.yaml ===
  models:
    - name: Qwen3-Coder-30B-A3B
      ...
  === Disk usage ===
    Qwen3-Coder-30B-A3B: 20.3 GB  [rev: a1b2c3d4...]
  ```

- [ ] **Step 6: Test `hf check`**

  ```bash
  hf check
  ```

  Expected:
  ```
  === HuggingFace Hub version check ===
    Qwen3-Coder-30B-A3B: pinned=a1b2c3d4...  UP TO DATE
  ```

- [ ] **Step 7: Test `hf pin` (round-trip, no-op)**

  ```bash
  CURRENT_HASH=$(python3 -c "import yaml; d=yaml.safe_load(open('/root/.hermes/models.yaml')); print(d['models'][0]['revision'])")
  hf pin Qwen3-Coder-30B-A3B "$CURRENT_HASH"
  ```

  Expected: `Pinned Qwen3-Coder-30B-A3B: a1b2c3d4... → a1b2c3d4...` then `models.yaml updated.`

- [ ] **Step 8: Test `hf download` usage error**

  ```bash
  hf download
  ```

  Expected: `Usage: hf download <model-name>` followed by available model list.

- [ ] **Step 9: Version-control the skill files**

  ```bash
  mkdir -p "C:/telo/Efforts/Ongoing/SOVRN/skills/hf-models"
  cp ~/.hermes/skills/hf-models/SKILL.md "C:/telo/Efforts/Ongoing/SOVRN/skills/hf-models/"
  cp ~/.hermes/skills/hf-models/hf "C:/telo/Efforts/Ongoing/SOVRN/skills/hf-models/"
  cd "C:/telo"
  git add Efforts/Ongoing/SOVRN/skills/hf-models/
  git commit -m "feat(hermes): add hf-models skill (status/check/download/pin)"
  ```

---

### Task 6: End-to-End Verification

- [ ] **Step 1: Verify complete fallback chain**

  ```bash
  curl -s http://127.0.0.1:4000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"fast-pool","messages":[{"role":"user","content":"Say: chain OK"}],"max_tokens":8}' \
    | python3 -c "import sys,json; r=json.load(sys.stdin); print(r['choices'][0]['message']['content'], '| via:', r.get('model','?'))"
  ```

  Expected: `chain OK | via: <model-name>` with no errors.

- [ ] **Step 2: Test Hermes Telegram commands**

  In the Hermes Telegram chat, send each command and verify the response:

  | Command | Expected response |
  |---|---|
  | `hf status` | Models table with name, size, revision prefix |
  | `hf check` | UP TO DATE or UPDATE AVAILABLE lines |
  | `hf pin Qwen3-Coder-30B-A3B <current-hash>` | "Pinned ... models.yaml updated." |

  For `hf download` — skip in Telegram unless you want to actually re-download 20 GB. The unit test in Task 5 Step 8 covers the usage-error path.

- [ ] **Step 3: Restart via startup script and confirm HF_TOKEN loads**

  ```powershell
  . "C:\telo\Atlas\Scripts\hermes_startup.ps1"
  ```

  Watch the LiteLLM log — no `KeyError: HF_TOKEN` or `AuthenticationError` should appear.

  ```powershell
  Get-Content "C:\telo\Calendar\Logs\lite_llm.err.log" -Tail 20
  ```

  Expected: clean startup, no HF auth errors.

- [ ] **Step 4: Final commit**

  ```bash
  cd "C:/telo"
  git status
  git commit -m "feat(SOVRN): HuggingFace A+B integration complete — registry + LiteLLM fallback"
  ```
