# C:\telo\scripts\bw-vault-populate.ps1
# Interactive script: prompts for each secret, creates all telo/ vault items

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Verify BW_SESSION is active
$status = bw status 2>&1 | ConvertFrom-Json -ErrorAction SilentlyContinue
if ($status.status -ne "unlocked") {
    Write-Host "[bw-populate] ERROR: vault is locked. Run: `$env:BW_SESSION = (bw unlock --raw)" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Bitwarden Vault Populate ===" -ForegroundColor Cyan
Write-Host "Enter each secret value when prompted. Input is hidden."
Write-Host "Press Enter to skip an item (will not be created).`n"

function Read-Secret($prompt) {
    $secure = Read-Host -AsSecureString $prompt
    if ($secure.Length -eq 0) { return $null }
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    return $plain
}

function Create-Item($name, $folderId, $password, $notes = $null) {
    if (-not $password) {
        Write-Host "  Skipped: $name" -ForegroundColor Yellow
        return
    }
    $item = bw get template item | ConvertFrom-Json
    $item.name = $name
    $item.folderId = $folderId
    $item.login = [PSCustomObject]@{ username = ""; password = $password }
    if ($notes) { $item.notes = $notes }
    $created = $item | ConvertTo-Json -Depth 10 | bw encode | bw create item | ConvertFrom-Json
    Write-Host "  Created: $($created.name)" -ForegroundColor Green
}

# Get or create telo/ folder
Write-Host "--- Setting up telo/ folder ---"
$existing = bw list folders | ConvertFrom-Json | Where-Object { $_.name -eq "telo" } | Select-Object -First 1
if ($existing) {
    $folderId = $existing.id
    Write-Host "  Found existing folder: $folderId"
} else {
    $folderJson = bw get template folder | ConvertFrom-Json
    $folderJson.name = "telo"
    $folderId = ($folderJson | ConvertTo-Json | bw encode | bw create folder | ConvertFrom-Json).id
    Write-Host "  Created folder: $folderId"
}

# Prompt for each secret
Write-Host "`n--- Enter secret values ---"

$githubPat    = Read-Secret "GitHub PAT (gho_* or ghp_*)"
$vercelKey    = Read-Secret "Vercel AI Gateway key (vck_*)"
$neo4jPass    = Read-Secret "Neo4j AuraDB password"
$googleAiKey  = Read-Secret "Google AI Studio key (AIzaSy*)"
$cfApiToken   = Read-Secret "Cloudflare API Token"
$cfAccountId  = Read-Secret "Cloudflare Account ID"
$cfZoneId     = Read-Secret "Cloudflare Zone ID"

# Build CF notes JSON
$cfNotes = $null
if ($cfAccountId -and $cfZoneId) {
    $cfNotes = "{`"CF_ACCOUNT_ID`":`"$cfAccountId`",`"CF_ZONE_ID`":`"$cfZoneId`"}"
}

# Create items
Write-Host "`n--- Creating vault items ---"
Create-Item "telo/github-pat"        $folderId $githubPat
Create-Item "telo/vercel-ai-gateway" $folderId $vercelKey
Create-Item "telo/neo4j-auradb"      $folderId $neo4jPass
Create-Item "telo/google-ai-studio"  $folderId $googleAiKey
Create-Item "telo/cloudflare"        $folderId $cfApiToken $cfNotes

# Sync and verify
Write-Host "`n--- Syncing and verifying ---"
bw sync 2>&1 | Out-Null
$items = bw list items | ConvertFrom-Json | Where-Object { $_.name -like "telo/*" } | Select-Object name
Write-Host "Items in telo/ folder:"
$items | ForEach-Object { Write-Host "  $($_.name)" -ForegroundColor Green }

Write-Host "`n=== Done ===`n"
