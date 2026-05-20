# Hermes Sovereignty Auto-Start Script (v3.4)
# Delegates startup orchestration to canonical launcher.

$CanonicalStartup = "C:\telo\Atlas\Scripts\hermes_startup.ps1"

Write-Host "--- Initiating Sovereignty Recovery (canonical startup) ---" -ForegroundColor Cyan

if (Test-Path $CanonicalStartup) {
    Start-Process powershell.exe -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $CanonicalStartup) -WindowStyle Minimized
    Write-Host "Launched canonical startup: $CanonicalStartup" -ForegroundColor Green
} else {
    Write-Host "[!] Canonical startup script not found at $CanonicalStartup" -ForegroundColor Yellow
}
