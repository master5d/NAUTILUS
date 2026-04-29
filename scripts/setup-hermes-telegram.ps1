# setup-hermes-telegram.ps1
# Agentic AI v3.3 — Hermes Telegram gateway setup
#
# Usage: pwsh -ExecutionPolicy Bypass -File setup-hermes-telegram.ps1
#
# Prerequisites:
#   1. Create bot via @BotFather in Telegram → /newbot → copy token
#   2. Get your Telegram user ID via @userinfobot
#   3. WSL2 with Hermes installed (hermes --version should work)

param(
    [string]$HermesEnvPath = "/root/.hermes/.env"
)

Write-Host ""
Write-Host "Hermes Telegram Setup"
Write-Host "====================="
Write-Host ""
Write-Host "Prerequisites:"
Write-Host "  1. Open Telegram → @BotFather → /newbot"
Write-Host "  2. Get your user ID → @userinfobot"
Write-Host ""

# Read token as SecureString — not visible in console, not in history
$secureToken = Read-Host "Paste bot token from @BotFather" -AsSecureString
$tokenBSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
$token = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($tokenBSTR)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenBSTR)

if (-not $token -or $token -notmatch '^\d+:[A-Za-z0-9_-]{35,}$') {
    Write-Error "Invalid token format. Expected: 123456789:ABCdef..."
    exit 1
}

$userId = Read-Host "Your Telegram user ID (from @userinfobot)"
if (-not $userId -or $userId -notmatch '^\d+$') {
    Write-Error "Invalid user ID. Expected numeric value."
    exit 1
}

Write-Host ""
Write-Host "Writing config to WSL2 $HermesEnvPath ..."

# Build env content — read existing file, patch/append the two vars
$envContent = wsl -e bash -c "cat $HermesEnvPath 2>/dev/null"

# Remove existing TELEGRAM lines if any
$envLines = $envContent -split "`n" | Where-Object {
    $_ -notmatch '^#?\s*TELEGRAM_BOT_TOKEN=' -and
    $_ -notmatch '^#?\s*TELEGRAM_ALLOWED_USERS='
}

$newLines = $envLines + @(
    "",
    "TELEGRAM_BOT_TOKEN=$token",
    "TELEGRAM_ALLOWED_USERS=$userId"
)

$newContent = ($newLines -join "`n").TrimStart()

# Write via WSL — tr -d '\r' strips Windows CRLF before writing to Linux .env
$newContent | wsl -e bash -c "tr -d '\r' > $HermesEnvPath"

# Clear token from memory
$token = $null
$newContent = $null

Write-Host "Config written."
Write-Host ""

# Verify (show file without revealing token value)
$check = wsl -e bash -c "grep -E 'TELEGRAM_' $HermesEnvPath"
$check | ForEach-Object {
    if ($_ -match '^TELEGRAM_BOT_TOKEN=(.+)$') {
        $masked = $Matches[1].Substring(0, [Math]::Min(10, $Matches[1].Length)) + "***"
        Write-Host "  TELEGRAM_BOT_TOKEN=$masked"
    } else {
        Write-Host "  $_"
    }
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Start gateway:  wsl -e bash -c 'hermes gateway run'"
Write-Host "  2. Open your bot in Telegram and send /start"
Write-Host "  3. For background service: wsl -e bash -c 'hermes gateway install && hermes gateway start'"
Write-Host ""
