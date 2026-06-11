# C:\telo\scripts\bw-unlock-hook.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Security

# Verify bw CLI is available
if (-not (Get-Command bw -ErrorAction SilentlyContinue)) {
    Write-Host "[bw-hook] ERROR: 'bw' CLI not found in PATH. Install to C:\telo\scripts\bw.exe"
    exit 1
}

# 1. Read master password from DPAPI-encrypted file
$claudeHome = if ($env:CLAUDE_HOME) { $env:CLAUDE_HOME } else { "$env:USERPROFILE\.claude" }
$dpapiPath = Join-Path $claudeHome "bw-master.dpapi"
if (-not (Test-Path $dpapiPath)) {
    Write-Host "[bw-hook] ERROR: $dpapiPath not found. Store master password first."
    exit 1
}
$encrypted  = [System.IO.File]::ReadAllBytes($dpapiPath)
$plainBytes = [System.Security.Cryptography.ProtectedData]::Unprotect(
    $encrypted, $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser)
$masterPass = [System.Text.Encoding]::UTF8.GetString($plainBytes)

# 2. Unlock vault — get session token
#    NOTE: do NOT use `2>&1` here — bw may emit stderr warnings (update notices, etc.)
#    which would be concatenated into the session token and corrupt it.
$rawSession = & bw unlock --raw $masterPass 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($rawSession)) {
    Write-Host "[bw-hook] ERROR: bw unlock failed (exit $LASTEXITCODE)"
    Remove-Item Env:BW_SESSION -ErrorAction SilentlyContinue
    exit 1
}
$env:BW_SESSION = $rawSession.Trim()

# 3. Fetch secrets
function Get-BwSecret($type, $name) {
    $val = bw get $type $name
    if ($LASTEXITCODE -ne 0) { throw "bw get $type '$name' failed (exit $LASTEXITCODE)" }
    return $val.Trim()
}

$secrets = [ordered]@{}
try {
    $secrets["VERCEL_API_KEY"] = Get-BwSecret password "telo/vercel-ai-gateway"
    $secrets["GITHUB_PAT"]     = Get-BwSecret password "telo/github-pat"
    $secrets["NEO4J_PASSWORD"] = Get-BwSecret password "telo/neo4j-auradb"
    $secrets["GOOGLE_AI_KEY"]  = Get-BwSecret password "telo/google-ai-studio"
    $secrets["CF_API_TOKEN"]   = Get-BwSecret password "telo/cloudflare"
    $secrets["N8N_API_KEY"]    = Get-BwSecret password "telo/n8n"

    $cfNotes = (Get-BwSecret notes "telo/cloudflare") | ConvertFrom-Json
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

# Validate all secrets were fetched
$missing = $secrets.Keys | Where-Object { [string]::IsNullOrWhiteSpace($secrets[$_]) }
if ($missing) {
    Write-Host "[bw-hook] ERROR: Empty or missing secrets: $($missing -join ', ')"
    exit 1
}

# 5. Write session env file (current user read-only)
$sessionFile = Join-Path $claudeHome "bw-session.ps1"
$lines = $secrets.GetEnumerator() | ForEach-Object {
    $escaped = $_.Value -replace "'", "''"
    "`$env:$($_.Key) = '$escaped'"
}
# Remove prior file first — previous run locked ACL to read-only, so overwrite would fail
if (Test-Path $sessionFile) {
    icacls $sessionFile /grant:r "${env:USERNAME}:(F)" 2>&1 | Out-Null
    Remove-Item $sessionFile -Force
}
$lines | Set-Content $sessionFile -Encoding UTF8
icacls $sessionFile /inheritance:r /grant:r "${env:USERNAME}:(R)" 2>&1 | Out-Null

# 6. Set User env vars (available to new processes spawned this session)
foreach ($kv in $secrets.GetEnumerator()) {
    [System.Environment]::SetEnvironmentVariable($kv.Key, $kv.Value, "User")
}

Write-Host "[bw-hook] $($secrets.Count) secrets loaded from Bitwarden vault"
