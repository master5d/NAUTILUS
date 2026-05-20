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

Write-Host "Starting LiteLLM proxy on http://localhost:4000 ..." -ForegroundColor Cyan
litellm --config "C:\telo\Efforts\Ongoing\SOVERN\config\litellm-config.yaml" --port 4000
