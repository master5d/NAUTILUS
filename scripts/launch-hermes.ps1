# launch-hermes.ps1
# Starts Hermes Agent via Ollama and verifies it's running
# Agentic AI v3.3, Phase 0 P1

# Check Ollama is installed
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Error "Ollama not found. Install from: https://ollama.com"
    exit 1
}

$version = (ollama --version 2>&1)
Write-Host "Ollama: $version"

# Check if Hermes is already running
$running = ollama ps 2>&1
if ($running -match "hermes") {
    Write-Host "Hermes already running."
} else {
    Write-Host "Launching Hermes..."
    # ollama launch hermes runs in background; for first-time setup follow
    # docs.ollama.com/integrations/hermes for Telegram bot token configuration
    Start-Process -NoNewWindow -FilePath "ollama" -ArgumentList "launch hermes"
    Start-Sleep -Seconds 5
}

# Verify Hermes is responding
$health = ollama ps 2>&1
if ($health -match "hermes") {
    Write-Host "Hermes is running."
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Configure Telegram bot token in Hermes UI"
    Write-Host "  2. Skills are at: $env:USERPROFILE\.hermes\skills\"
    Write-Host "  3. Memory vault: $env:USERPROFILE\life\"
    Write-Host "  4. Docs: https://docs.ollama.com/integrations/hermes"
} else {
    Write-Warning "Hermes may not have started. Check: ollama ps"
    Write-Host "If 'ollama launch hermes' fails, ensure Ollama >= 0.21"
    Write-Host "Current: $version"
}
