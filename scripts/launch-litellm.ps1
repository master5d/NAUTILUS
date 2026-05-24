# launch-litellm.ps1
# Load API keys from Windows User environment and start LiteLLM proxy on port 4000.
# Usage: pwsh -ExecutionPolicy Bypass -File launch-litellm.ps1

$keys = @(
    'CEREBRAS_API_KEY','GROQ_API_KEY','NIM_API_KEY','OPENROUTER_API_KEY',
    'GEMINI_API_KEY','LANGFUSE_PUBLIC_KEY','LANGFUSE_SECRET_KEY'
)

foreach ($k in $keys) {
    $val = [System.Environment]::GetEnvironmentVariable($k, 'User')
    if ($val) { [System.Environment]::SetEnvironmentVariable($k, $val, 'Process') }
    else { Write-Warning "$k not set — run setup-litellm-keys.ps1 first" }
}

# 1. Allocate a dynamic port using the port broker
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$brokerPath = Join-Path $scriptRoot "port_broker.py"
$configPath = Join-Path (Split-Path -Parent $scriptRoot) "config\litellm-config.yaml"

$allocatedPortStr = python $brokerPath "litellm" 4000 | Select-Object -Last 1
$allocatedPort = [int]$allocatedPortStr.Trim()

Write-Host "Starting LiteLLM proxy on http://localhost:$allocatedPort ..." -ForegroundColor Cyan
litellm --config $configPath --port $allocatedPort
