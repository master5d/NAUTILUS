# NAUTILUS\secops\infra\start-secops.ps1
# Sources BW secrets then starts secops stack (Bitwarden integration DORMANT — see ..\BITWARDEN.md)

$sessionFile = "$env:USERPROFILE\.claude\bw-session.ps1"
if (Test-Path $sessionFile) {
    . $sessionFile
    Write-Host "[secops] Bitwarden session env loaded"
} else {
    # Fallback: run the unlock hook manually
    Write-Host "[secops] No session file — running bw-unlock-hook..."
    pwsh -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "scripts\bw-unlock-hook.ps1")
    if (Test-Path $sessionFile) { . $sessionFile }
}

# Verify required vars are present before starting
$required = @("CF_ACCOUNT_ID","CF_ZONE_ID","CF_API_TOKEN")
$missing = $required | Where-Object { -not (Get-Item "Env:$_" -ErrorAction SilentlyContinue) }
if ($missing) {
    Write-Host "[secops] ERROR: missing env vars: $($missing -join ', ')"
    Write-Host "[secops] Check bw-audit.ps1 and ensure telo/ items exist in vault"
    exit 1
}

Write-Host "[secops] Starting secops stack..."
Set-Location $PSScriptRoot
docker compose up -d @args
