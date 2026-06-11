# Post-login smoke test for bw unlock → get → lock cycle
# Run AFTER `bw login --apikey` succeeds. Verifies the session-token fix.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

Add-Type -AssemblyName System.Security

Write-Host "=== bw smoke test ===" -ForegroundColor Cyan

# 0. Login state
$status = (& bw status 2>&1 | ConvertFrom-Json)
Write-Host "[0] status: $($status.status) (user: $($status.userEmail))"
if ($status.status -eq "unauthenticated") {
    Write-Host "ERROR: Not logged in. Run 'bw login --apikey' first." -ForegroundColor Red
    exit 1
}

# 1. Decrypt master password from DPAPI
$dpapiPath = "$env:USERPROFILE\.claude\bw-master.dpapi"
if (-not (Test-Path $dpapiPath)) {
    Write-Host "ERROR: $dpapiPath missing" -ForegroundColor Red
    exit 1
}
$enc   = [System.IO.File]::ReadAllBytes($dpapiPath)
$plain = [System.Security.Cryptography.ProtectedData]::Unprotect(
    $enc, $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser)
$pw    = [System.Text.Encoding]::UTF8.GetString($plain)
Write-Host "[1] DPAPI decrypt OK (pw-len: $($pw.Length))"

# 2. Unlock — capture raw session
$session = (& bw unlock --raw $pw 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($session)) {
    Write-Host "ERROR: bw unlock failed (exit $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}
$session = $session.Trim()
Write-Host "[2] unlock OK (session-len: $($session.Length))"

# 3. Verify session via status
$env:BW_SESSION = $session
$s2 = & bw status 2>&1 | ConvertFrom-Json
Write-Host "[3] status with session: $($s2.status)"
if ($s2.status -ne "unlocked") {
    Write-Host "FAIL: vault still locked after unlock — bug persists" -ForegroundColor Red
    $env:BW_SESSION = $null
    & bw lock 2>&1 | Out-Null
    exit 1
}

# 4. Fetch each known secret
$items = @(
    "telo/vercel-ai-gateway",
    "telo/github-pat",
    "telo/neo4j-auradb",
    "telo/google-ai-studio",
    "telo/cloudflare",
    "telo/n8n"
)
$ok = 0
$fail = 0
foreach ($name in $items) {
    $val = & bw get password $name 2>&1
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($val)) {
        Write-Host "[4] $name -> OK (len $($val.Trim().Length))" -ForegroundColor Green
        $ok++
    } else {
        Write-Host "[4] $name -> FAIL: $val" -ForegroundColor Red
        $fail++
    }
}

# 5. Cleanup
$env:BW_SESSION = $null
Remove-Item Env:BW_SESSION -ErrorAction SilentlyContinue
& bw lock 2>&1 | Out-Null
Write-Host "[5] vault locked, session cleared"

Write-Host ""
if ($fail -eq 0) {
    Write-Host "=== PASS: $ok/$($items.Count) secrets retrieved ===" -ForegroundColor Green
    exit 0
} else {
    Write-Host "=== PARTIAL: $ok OK, $fail FAIL ===" -ForegroundColor Yellow
    exit 1
}
