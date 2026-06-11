# Bitwarden CLI Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install bw CLI, wire a SessionStart hook that fetches secrets from Bitwarden into env vars, and plumb those vars into the secops docker-compose pipeline.

**Architecture:** A PowerShell startup hook unlocks the vault using a master password stored in Windows Credential Manager, writes secrets to `~/.claude/bw-session.ps1` (current-user-only file) AND to User-level registry env vars, then immediately locks the vault. Claude Code tool calls source the session file; docker-compose reads the User env vars via a wrapper script.

**Tech Stack:** Bitwarden CLI (`bw.exe`), PowerShell 7, Windows Credential Manager (`CredentialManager` PS module), Claude Code hooks (`~/.claude/settings.json`), docker-compose

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `C:\telo\scripts\bw.exe` | Bitwarden CLI binary |
| Create | `C:\telo\scripts\bw-unlock-hook.ps1` | SessionStart hook — unlock → fetch → lock |
| Create | `C:\telo\scripts\bw-lock-hook.ps1` | SessionEnd hook — clear session file + User env vars |
| Create | `C:\telo\scripts\bw-audit.ps1` | Audit script — find all secrets not yet in Bitwarden |
| Create | `C:\telo\secops\start-secops.ps1` | Wrapper that sources env vars then runs docker-compose |
| Modify | `C:\telo\secops\docker-compose.yml` | Add CF env var passthrough to bouncer service |
| Modify | `~/.claude/settings.json` | Register bw-unlock-hook + bw-lock-hook |

---

## Task 1: Install bw CLI

**Files:**
- Create: `C:\telo\scripts\bw.exe`

- [ ] **Step 1: Download bw.exe from GitHub releases**

```powershell
$release = Invoke-RestMethod "https://api.github.com/repos/bitwarden/clients/releases" |
    Where-Object { $_.tag_name -like "cli-v*" } |
    Select-Object -First 1
$asset = $release.assets | Where-Object { $_.name -eq "bw-windows-*" -or $_.name -match "bw-windows" }
Write-Host "Latest CLI release: $($release.tag_name)"
Write-Host "Assets available:"
$release.assets | Select-Object name, browser_download_url | Format-Table
```

Find the `bw-windows-*.zip` asset URL from the output.

- [ ] **Step 2: Download and extract**

```powershell
$url = "https://github.com/bitwarden/clients/releases/download/cli-v2024.11.0/bw-windows-2024.11.0.zip"
# Replace URL with the latest from Step 1
Invoke-WebRequest -Uri $url -OutFile "C:\telo\bw-download.zip"
Expand-Archive "C:\telo\bw-download.zip" -DestinationPath "C:\telo\scripts" -Force
Remove-Item "C:\telo\bw-download.zip"
Remove-Item "C:\telo\bw.zip" -ErrorAction SilentlyContinue
```

- [ ] **Step 3: Verify binary exists**

```powershell
Get-Item "C:\telo\scripts\bw.exe"
```

Expected: file exists, size > 50MB.

- [ ] **Step 4: Add scripts\ to user PATH**

```powershell
$current = [System.Environment]::GetEnvironmentVariable("PATH", "User")
if ($current -notlike "*C:\telo\scripts*") {
    [System.Environment]::SetEnvironmentVariable("PATH", "$current;C:\telo\scripts", "User")
    Write-Host "PATH updated"
} else {
    Write-Host "Already in PATH"
}
```

- [ ] **Step 5: Verify in new PowerShell session**

Open a new PowerShell window (not the current one — PATH change needs a new process) and run:
```powershell
bw --version
```
Expected output: `2024.11.x` (or whichever version was downloaded). **Do not proceed until this works.**

- [ ] **Step 6: Commit**

```powershell
# bw.exe is a binary — add to .gitignore if C:\telo is a git repo
# Otherwise no commit needed; binary install is manual
Write-Host "bw CLI installed at C:\telo\scripts\bw.exe"
```

---

## Task 2: Store Master Password in Windows Credential Manager

**Files:**
- No file changes — Windows Credential Manager only

- [ ] **Step 1: Store Bitwarden master password via DPAPI**

```powershell
# CredentialManager module incompatible with PS7 (System.Web dependency).
# Use DPAPI instead — encrypts with current user's Windows credentials.
Add-Type -AssemblyName System.Security
$pass = Read-Host -AsSecureString "Bitwarden master password"
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($pass)
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
$plainBytes = [System.Text.Encoding]::UTF8.GetBytes($plain)
$plain = $null
$encrypted = [System.Security.Cryptography.ProtectedData]::Protect(
    $plainBytes, $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser)
$outPath = "$env:USERPROFILE\.claude\bw-master.dpapi"
[System.IO.File]::WriteAllBytes($outPath, $encrypted)
icacls $outPath /inheritance:r /grant:r "${env:USERNAME}:(R)" | Out-Null
Write-Host "Saved to $outPath"
```

Expected: `Saved to C:\Users\sasha\.claude\bw-master.dpapi`

- [ ] **Step 2: Verify file was created**

```powershell
Test-Path "$env:USERPROFILE\.claude\bw-master.dpapi"
(Get-Item "$env:USERPROFILE\.claude\bw-master.dpapi").Length
```

Expected: `True`, then file size > 0.

---

## Task 3: Populate Bitwarden Vault (Manual)

**Files:** None — done in Bitwarden desktop app

This task is manual. Create a folder `telo` in your Bitwarden vault, then create these Login items inside it:

- [ ] **Step 1: Create `telo/cloudflare` item**

  - Name: `telo/cloudflare`
  - Username: `cloudflare`
  - Password: `<CF_API_TOKEN value>`
  - Notes (JSON):
    ```json
    {"CF_ACCOUNT_ID":"<your account id>","CF_ZONE_ID":"<your zone id>"}
    ```

- [ ] **Step 2: Create remaining items**

  | Item name | Password field value |
  |-----------|---------------------|
  | `telo/github-pat` | GitHub PAT (`ghp_*` or `gho_*`) |
  | `telo/vercel-ai-gateway` | Vercel AI Gateway key (`vck_*`) |
  | `telo/neo4j-auradb` | Neo4j AuraDB password |
  | `telo/google-ai-studio` | Google AI key (`AIzaSy*`) |

- [ ] **Step 3: Sync CLI**

```powershell
bw login  # only needed once — follow prompts
bw sync
bw list items --folderName telo | ConvertFrom-Json | Select-Object name
```

Expected: 5 items listed under `telo/`.

---

## Task 4: Write bw-unlock-hook.ps1

**Files:**
- Create: `C:\telo\scripts\bw-unlock-hook.ps1`

- [ ] **Step 1: Write the hook script**

```powershell
# C:\telo\scripts\bw-unlock-hook.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Import-Module CredentialManager -ErrorAction Stop

# 1. Read master password from Credential Manager
$stored = Get-StoredCredential -Target "bitwarden-master"
if (-not $stored) {
    Write-Host "[bw-hook] ERROR: bitwarden-master not found in Credential Manager. Run Task 2 first."
    exit 1
}
$masterPass = $stored.GetNetworkCredential().Password

# 2. Unlock vault — get session token
$env:BW_SESSION = (bw unlock --raw $masterPass 2>&1)
if ($LASTEXITCODE -ne 0 -or -not $env:BW_SESSION) {
    Write-Host "[bw-hook] ERROR: bw unlock failed (exit $LASTEXITCODE)"
    Remove-Item Env:BW_SESSION -ErrorAction SilentlyContinue
    exit 1
}

# 3. Fetch secrets
$secrets = [ordered]@{}
try {
    $secrets["VERCEL_API_KEY"] = (bw get password "telo/vercel-ai-gateway" 2>&1).Trim()
    $secrets["GITHUB_PAT"]     = (bw get password "telo/github-pat" 2>&1).Trim()
    $secrets["NEO4J_PASSWORD"] = (bw get password "telo/neo4j-auradb" 2>&1).Trim()
    $secrets["GOOGLE_AI_KEY"]  = (bw get password "telo/google-ai-studio" 2>&1).Trim()
    $secrets["CF_API_TOKEN"]   = (bw get password "telo/cloudflare" 2>&1).Trim()

    $cfNotes = (bw get notes "telo/cloudflare" 2>&1).Trim() | ConvertFrom-Json
    $secrets["CF_ACCOUNT_ID"]  = $cfNotes.CF_ACCOUNT_ID
    $secrets["CF_ZONE_ID"]     = $cfNotes.CF_ZONE_ID
} catch {
    Write-Host "[bw-hook] ERROR fetching secrets: $_"
    exit 1
} finally {
    # 4. Destroy session token regardless of success/failure
    $env:BW_SESSION = $null
    Remove-Item Env:BW_SESSION -ErrorAction SilentlyContinue
    bw lock 2>&1 | Out-Null
}

# 5. Write session env file (current user read-only)
$sessionFile = "$env:USERPROFILE\.claude\bw-session.ps1"
$lines = $secrets.GetEnumerator() | ForEach-Object {
    "`$env:$($_.Key) = '$($_.Value)'"
}
$lines | Set-Content $sessionFile -Encoding UTF8
icacls $sessionFile /inheritance:r /grant:r "${env:USERNAME}:(R)" 2>&1 | Out-Null

# 6. Set User env vars (available to new processes spawned this session)
foreach ($kv in $secrets.GetEnumerator()) {
    [System.Environment]::SetEnvironmentVariable($kv.Key, $kv.Value, "User")
}

Write-Host "[bw-hook] $($secrets.Count) secrets loaded from Bitwarden vault"
```

- [ ] **Step 2: Test the hook manually**

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File C:\telo\scripts\bw-unlock-hook.ps1
```

Expected output: `[bw-hook] 7 secrets loaded from Bitwarden vault`

- [ ] **Step 3: Verify session file was created**

```powershell
Test-Path "$env:USERPROFILE\.claude\bw-session.ps1"
# Verify it has content (line count only — DO NOT print values)
(Get-Content "$env:USERPROFILE\.claude\bw-session.ps1").Count
```

Expected: `True`, then `7`

- [ ] **Step 4: Verify User env vars were set**

```powershell
# Verify vars exist (check names only, not values)
@("VERCEL_API_KEY","GITHUB_PAT","NEO4J_PASSWORD","GOOGLE_AI_KEY","CF_API_TOKEN","CF_ACCOUNT_ID","CF_ZONE_ID") |
    ForEach-Object {
        $val = [System.Environment]::GetEnvironmentVariable($_, "User")
        [PSCustomObject]@{ Var = $_; Set = ($null -ne $val -and $val.Length -gt 0) }
    } | Format-Table
```

Expected: all 7 rows show `Set = True`

---

## Task 5: Write bw-lock-hook.ps1

**Files:**
- Create: `C:\telo\scripts\bw-lock-hook.ps1`

- [ ] **Step 1: Write the cleanup hook**

```powershell
# C:\telo\scripts\bw-lock-hook.ps1
$sessionFile = "$env:USERPROFILE\.claude\bw-session.ps1"

# Remove session file
if (Test-Path $sessionFile) {
    Remove-Item $sessionFile -Force
    Write-Host "[bw-hook] Session file removed"
}

# Clear User env vars
$vars = @("VERCEL_API_KEY","GITHUB_PAT","NEO4J_PASSWORD","GOOGLE_AI_KEY",
          "CF_API_TOKEN","CF_ACCOUNT_ID","CF_ZONE_ID")
foreach ($var in $vars) {
    [System.Environment]::SetEnvironmentVariable($var, $null, "User")
}

Write-Host "[bw-hook] $($vars.Count) secrets cleared from User env"
```

- [ ] **Step 2: Test cleanup**

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File C:\telo\scripts\bw-lock-hook.ps1
```

Expected:
```
[bw-hook] Session file removed
[bw-hook] 7 secrets cleared from User env
```

- [ ] **Step 3: Verify file is gone and vars are cleared**

```powershell
Test-Path "$env:USERPROFILE\.claude\bw-session.ps1"
[System.Environment]::GetEnvironmentVariable("CF_API_TOKEN", "User")
```

Expected: `False`, then empty/null output.

---

## Task 6: Write bw-audit.ps1

**Files:**
- Create: `C:\telo\scripts\bw-audit.ps1`

- [ ] **Step 1: Write the audit script**

```powershell
# C:\telo\scripts\bw-audit.ps1
# Reports migration status: what's in Bitwarden vs. what's still elsewhere
# Never prints secret values — reports presence only

$knownVars = @("VERCEL_API_KEY","GITHUB_PAT","NEO4J_PASSWORD","GOOGLE_AI_KEY",
               "CF_API_TOKEN","CF_ACCOUNT_ID","CF_ZONE_ID")

Write-Host "`n=== Bitwarden Migration Audit ===" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm')`n"

# Check 1: User env vars (from BW hook or legacy setx)
Write-Host "--- User Environment Variables ---"
foreach ($var in $knownVars) {
    $val = [System.Environment]::GetEnvironmentVariable($var, "User")
    $status = if ($null -ne $val -and $val.Length -gt 0) { "SET" } else { "MISSING" }
    Write-Host "  $var : $status"
}

# Check 2: Windows Credential Manager known entries
Write-Host "`n--- Windows Credential Manager ---"
Import-Module CredentialManager -ErrorAction SilentlyContinue
$targets = @("bitwarden-master","github-pat","gh:github.com")
foreach ($t in $targets) {
    try {
        $c = Get-StoredCredential -Target $t -ErrorAction Stop
        Write-Host "  $t : FOUND (user: $($c.UserName))"
    } catch {
        Write-Host "  $t : NOT FOUND"
    }
}

# Check 3: .env* files in C:\telo (paths only, no content)
Write-Host "`n--- .env* files in C:\telo (paths only) ---"
$envFiles = Get-ChildItem -Path "C:\telo" -Recurse -Filter ".env*" -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notlike "*\.git\*" -and $_.FullName -notlike "*node_modules*" }
if ($envFiles) {
    $envFiles | ForEach-Object { Write-Host "  $($_.FullName)" }
    Write-Host "  ACTION NEEDED: migrate contents to Bitwarden, then delete" -ForegroundColor Yellow
} else {
    Write-Host "  None found" -ForegroundColor Green
}

# Check 4: Bitwarden vault items (requires active session)
Write-Host "`n--- Bitwarden telo/ folder items ---"
$bwStatus = bw status 2>&1 | ConvertFrom-Json -ErrorAction SilentlyContinue
if ($bwStatus.status -eq "unlocked") {
    $items = bw list items 2>&1 | ConvertFrom-Json -ErrorAction SilentlyContinue |
        Where-Object { $_.name -like "telo/*" } |
        Select-Object name
    if ($items) {
        $items | ForEach-Object { Write-Host "  $($_.name) : IN VAULT" -ForegroundColor Green }
    } else {
        Write-Host "  No telo/* items found — run Task 3 to populate vault" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Vault locked — run 'bw unlock' first to check vault items"
}

Write-Host "`n=== Audit Complete ===`n"
```

- [ ] **Step 2: Run the audit**

```powershell
pwsh -File C:\telo\scripts\bw-audit.ps1
```

Review output. Note any `.env*` files that need migration and any missing vars.

---

## Task 7: Register Hooks in settings.json

**Files:**
- Modify: `~/.claude/settings.json`

- [ ] **Step 1: Read current SessionStart hooks array**

```powershell
$settings = Get-Content "$env:USERPROFILE\.claude\settings.json" | ConvertFrom-Json -Depth 20
$sessionStartHooks = $settings.hooks.SessionStart
$sessionStartHooks | ConvertTo-Json -Depth 10
```

Identify the existing matcher block (should be `"startup|resume|clear"`). The new bw hook goes into that same block's `hooks` array.

- [ ] **Step 2: Add bw-unlock-hook to SessionStart**

Open `~/.claude/settings.json` and add the following entry to the `hooks` array inside the `SessionStart` block with matcher `"startup|resume|clear"`:

```json
{
  "type": "command",
  "command": "powershell -NoProfile -ExecutionPolicy Bypass -File \"C:\\telo\\scripts\\bw-unlock-hook.ps1\"",
  "statusMessage": "Loading Bitwarden secrets..."
}
```

Place it **before** the ollama monitor hook (first in the array) so secrets are available before other hooks run.

- [ ] **Step 3: Add bw-lock-hook to SessionEnd**

In the same `settings.json`, find the `SessionEnd` block (matcher `"*"`) and add:

```json
{
  "type": "command",
  "command": "powershell -NoProfile -ExecutionPolicy Bypass -File \"C:\\telo\\scripts\\bw-lock-hook.ps1\"",
  "statusMessage": "Clearing Bitwarden session..."
}
```

Place it **first** in the SessionEnd hooks array.

- [ ] **Step 4: Validate JSON is well-formed**

```powershell
Get-Content "$env:USERPROFILE\.claude\settings.json" | ConvertFrom-Json -Depth 20 | Out-Null
Write-Host "JSON valid"
```

Expected: `JSON valid` with no errors. If errors, fix the JSON before continuing.

- [ ] **Step 5: Test by starting a new Claude Code session**

Start a fresh Claude Code session. The status bar or startup output should show "Loading Bitwarden secrets..." then "7 secrets loaded from Bitwarden vault".

Verify in that session:
```powershell
# In a Bash or PowerShell tool call within Claude Code
. "$env:USERPROFILE\.claude\bw-session.ps1"
[bool]$env:CF_API_TOKEN
```

Expected: `True`

---

## Task 8: Update docker-compose.yml and Add secops Wrapper

**Files:**
- Modify: `C:\telo\secops\docker-compose.yml`
- Create: `C:\telo\secops\start-secops.ps1`

- [ ] **Step 1: Update docker-compose.yml — add CF env passthrough to bouncer**

In `C:\telo\secops\docker-compose.yml`, replace the `crowdsec-cloudflare-bouncer` service block:

```yaml
  # CrowdSec Cloudflare Bouncer (edge blocklist)
  crowdsec-cloudflare-bouncer:
    image: crowdsecurity/cloudflare-bouncer:latest
    container_name: enerv_cs_cloudflare_bouncer
    environment:
      CF_ACCOUNT_ID: ${CF_ACCOUNT_ID}
      CF_ZONE_ID: ${CF_ZONE_ID}
      CF_API_TOKEN: ${CF_API_TOKEN}
    volumes:
      - ./crowdsec/cloudflare-bouncer.yaml:/etc/crowdsec/bouncers/crowdsec-cloudflare-bouncer.yaml
    depends_on:
      - crowdsec
    restart: unless-stopped
```

- [ ] **Step 2: Verify docker-compose can parse the updated file**

```powershell
Set-Location C:\telo\secops
docker compose config --quiet 2>&1
```

Expected: exits 0 (no output if vars are unset is OK — docker compose config validates syntax, not values).

- [ ] **Step 3: Create start-secops.ps1 wrapper**

```powershell
# C:\telo\secops\start-secops.ps1
# Sources BW secrets then starts secops stack

$sessionFile = "$env:USERPROFILE\.claude\bw-session.ps1"
if (Test-Path $sessionFile) {
    . $sessionFile
    Write-Host "[secops] Bitwarden session env loaded"
} else {
    # Fallback: run the unlock hook manually
    Write-Host "[secops] No session file — running bw-unlock-hook..."
    pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\telo\scripts\bw-unlock-hook.ps1"
    if (Test-Path $sessionFile) { . $sessionFile }
}

# Verify required vars are present before starting
$required = @("CF_ACCOUNT_ID","CF_ZONE_ID","CF_API_TOKEN")
$missing = $required | Where-Object { -not $env:($_) }
if ($missing) {
    Write-Host "[secops] ERROR: missing env vars: $($missing -join ', ')"
    Write-Host "[secops] Check bw-audit.ps1 and ensure telo/ items exist in vault"
    exit 1
}

Write-Host "[secops] Starting secops stack..."
Set-Location $PSScriptRoot
docker compose up -d @args
```

- [ ] **Step 4: Test the wrapper (dry run)**

```powershell
# First run the unlock hook to populate session file
pwsh -File C:\telo\scripts\bw-unlock-hook.ps1

# Then test wrapper with --dry-run (docker compose 2.x supports this)
pwsh -File C:\telo\secops\start-secops.ps1 --dry-run
```

Expected: `[secops] Bitwarden session env loaded` then docker-compose dry run output.

- [ ] **Step 5: Commit**

```powershell
cd C:\telo
git add secops/docker-compose.yml secops/start-secops.ps1 scripts/bw-unlock-hook.ps1 scripts/bw-lock-hook.ps1 scripts/bw-audit.ps1
git commit -m "feat: bitwarden CLI integration — hook + secops passthrough"
```

(If C:\telo is not a git repo, skip commit.)

---

## Task 9: Run Full Audit and Migrate Remaining Secrets

**Files:**
- No new files — migration work

- [ ] **Step 1: Run the unlock hook to get a live session**

```powershell
pwsh -File C:\telo\scripts\bw-unlock-hook.ps1
```

- [ ] **Step 2: Run full audit**

```powershell
bw unlock  # unlock for vault check portion
pwsh -File C:\telo\scripts\bw-audit.ps1
```

- [ ] **Step 3: Migrate any remaining .env* files**

For each `.env*` file reported by the audit:
1. Open the file (manually in a text editor — not via Claude Code tool which denies `.env*` reads)
2. For each key=value, create or update the corresponding Bitwarden item in `telo/`
3. After confirming the secret is in Bitwarden and the hook loads it correctly, delete the `.env*` file

- [ ] **Step 4: Remove legacy setx env vars**

After verifying the hook correctly loads all secrets, remove legacy `setx`-persisted env vars:

```powershell
# Remove only vars now managed by Bitwarden hook
# (these will be re-set each session by the hook)
# Do NOT run this until you have confirmed hook loads them correctly
#
# NOTE: GITHUB_PERSONAL_ACCESS_TOKEN is managed separately via `gh auth token`
# and is required by the GitHub MCP plugin — do NOT remove it here.
# Only remove vars that the audit confirms are duplicated in Bitwarden.
$legacyVars = @()  # populate from audit output — e.g. @("VERCEL_API_KEY") if set via old setx
foreach ($v in $legacyVars) {
    [System.Environment]::SetEnvironmentVariable($v, $null, "User")
    Write-Host "Removed legacy: $v"
}
```

- [ ] **Step 5: Re-run audit to confirm clean state**

```powershell
pwsh -File C:\telo\scripts\bw-audit.ps1
```

Expected: no `.env*` files, all vars SET, all `telo/` items IN VAULT.

---

## Prerequisites Checklist

Before starting Task 4+:
- [ ] Bitwarden desktop app installed and logged in
- [ ] `bw login` completed in CLI (Task 3 Step 3)
- [ ] All `telo/` vault items created (Task 3)
- [ ] `bitwarden-master` stored in Windows Credential Manager (Task 2)
