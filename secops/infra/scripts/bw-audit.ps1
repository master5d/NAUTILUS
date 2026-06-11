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
    Where-Object { $_.FullName -notlike "*\.git\*" -and $_.FullName -notlike "*node_modules*" -and $_.Name -notlike "*.example" }
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
