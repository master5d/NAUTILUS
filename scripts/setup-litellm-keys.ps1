# setup-litellm-keys.ps1
# Securely set LiteLLM provider API keys as persistent user environment variables.
# Keys are never echoed to console or stored in shell history.
#
# Usage: pwsh -ExecutionPolicy Bypass -File setup-litellm-keys.ps1

function Read-SecureKey {
    param([string]$Prompt, [string]$EnvVar)

    $secure = Read-Host $Prompt -AsSecureString
    $bstr   = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $plain  = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

    if (-not $plain -or $plain.Length -lt 10) {
        Write-Error "Key too short or empty — skipping $EnvVar"
        return
    }

    [System.Environment]::SetEnvironmentVariable($EnvVar, $plain, "User")
    [System.Environment]::SetEnvironmentVariable($EnvVar, $plain, "Process")

    $masked = $plain.Substring(0, [Math]::Min(8, $plain.Length)) + "***"
    Write-Host "  $EnvVar = $masked  [saved]" -ForegroundColor Green

    $plain = $null
}

Write-Host ""
Write-Host "LiteLLM API Key Setup" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
Write-Host "Keys are saved to Windows User environment (persistent across reboots)."
Write-Host "Press Enter without typing to skip a key."
Write-Host ""

Read-SecureKey -Prompt "Cerebras API key"   -EnvVar "CEREBRAS_API_KEY"
Read-SecureKey -Prompt "Groq API key"       -EnvVar "GROQ_API_KEY"
Read-SecureKey -Prompt "NIM API key"        -EnvVar "NIM_API_KEY"
Read-SecureKey -Prompt "OpenRouter API key" -EnvVar "OPENROUTER_API_KEY"
Read-SecureKey -Prompt "Google AI Studio (Gemini) API key" -EnvVar "GEMINI_API_KEY"
Read-SecureKey -Prompt "HuggingFace token (HF fallback tier)" -EnvVar "HF_TOKEN"

Write-Host ""
Write-Host "Done. Now set Langfuse keys for LiteLLM tracing."
Write-Host "Open http://localhost:3002 → Settings → API Keys → Create."
Write-Host ""

Read-SecureKey -Prompt "Langfuse Public key"  -EnvVar "LANGFUSE_PUBLIC_KEY"
Read-SecureKey -Prompt "Langfuse Secret key"  -EnvVar "LANGFUSE_SECRET_KEY"

Write-Host ""
Write-Host "All keys saved. Start LiteLLM with:" -ForegroundColor Cyan
Write-Host '  pip install "litellm[proxy]==1.57.4"'
Write-Host '  pwsh -File C:\telo\Efforts\Ongoing\NAUTILUS\scripts\launch-litellm.ps1'
Write-Host ""
