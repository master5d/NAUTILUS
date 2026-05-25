# master-restart.ps1
# Agentic AI v3.3 — One-click Sovereign Stack Restart
# Usage: pwsh -File master-restart.ps1

Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       SOVRN v3.3 — SOVEREIGN STACK RESTART SEQUENCE     ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 1. Launch Llama Server (Local AI Backbone)
Write-Host "[Step 1/3] Starting Llama Server (Qwen3-Coder-30B)..." -ForegroundColor Yellow
$llamaProc = Start-Process powershell -ArgumentList "-NoExit", "-File", ".\launch-llama-server.ps1" -PassThru
Write-Host "  -> Process ID: $($llamaProc.Id)" -ForegroundColor Gray

# Wait for Llama to bind the port
Write-Host "  -> Waiting 10s for model to load into VRAM..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# 2. Launch LiteLLM (Gateway & Model Pool)
Write-Host "[Step 2/3] Starting LiteLLM Gateway..." -ForegroundColor Yellow
$liteProc = Start-Process powershell -ArgumentList "-NoExit", "-File", ".\launch-litellm.ps1" -PassThru
Write-Host "  -> Process ID: $($liteProc.Id)" -ForegroundColor Gray

# Wait for registry to populate
Start-Sleep -Seconds 2

# 3. Launch Vault Watcher (Ambient Real-time Sync)
Write-Host "[Step 3/3] Starting Obsidian Vault Watcher..." -ForegroundColor Yellow
$watcherProc = Start-Process powershell -ArgumentList "-NoExit", "-Command", "python .\vault_watcher.py" -PassThru
Write-Host "  -> Process ID: $($watcherProc.Id)" -ForegroundColor Gray

# Wait for watcher to register initial index state
Start-Sleep -Seconds 1

# Retrieve active endpoints from services.json registry
$servicesPath = Join-Path $PSScriptRoot "..\config\services.json"
if (Test-Path $servicesPath) {
    $services = Get-Content $servicesPath | ConvertFrom-Json
    $llamaUrl = $services."llama-server".url
    $liteUrl = $services.litellm.url
} else {
    $llamaUrl = "http://127.0.0.1:8080"
    $liteUrl = "http://localhost:4000"
}

Write-Host ""
Write-Host "✔ RESTART SEQUENCE COMPLETE." -ForegroundColor Green
Write-Host "Check health endpoints:" -ForegroundColor Gray
Write-Host "- Llama: $llamaUrl/health" -ForegroundColor Gray
Write-Host "- LiteLLM: $liteUrl/health" -ForegroundColor Gray
Write-Host "- Vault Watcher: Running in background" -ForegroundColor Gray
Write-Host ""
Write-Host "Now back to work, Architect." -ForegroundColor Cyan
