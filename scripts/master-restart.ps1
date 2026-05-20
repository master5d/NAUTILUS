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
Write-Host "[Step 1/2] Starting Llama Server (Qwen3-Coder-30B)..." -ForegroundColor Yellow
$llamaProc = Start-Process powershell -ArgumentList "-NoExit", "-File", ".\launch-llama-server.ps1" -PassThru
Write-Host "  -> Process ID: $($llamaProc.Id)" -ForegroundColor Gray

# Wait for Llama to bind the port
Write-Host "  -> Waiting 10s for model to load into VRAM..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# 2. Launch LiteLLM (Gateway & Model Pool)
Write-Host "[Step 2/2] Starting LiteLLM Gateway (Port 4000)..." -ForegroundColor Yellow
$liteProc = Start-Process powershell -ArgumentList "-NoExit", "-File", ".\launch-litellm.ps1" -PassThru
Write-Host "  -> Process ID: $($liteProc.Id)" -ForegroundColor Gray

Write-Host ""
Write-Host "✔ RESTART SEQUENCE COMPLETE." -ForegroundColor Green
Write-Host "Check health endpoints:" -ForegroundColor Gray
Write-Host "- Llama: http://localhost:8080/health" -ForegroundColor Gray
Write-Host "- LiteLLM: http://localhost:4000/health" -ForegroundColor Gray
Write-Host ""
Write-Host "Now back to work, Architect." -ForegroundColor Cyan
