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
