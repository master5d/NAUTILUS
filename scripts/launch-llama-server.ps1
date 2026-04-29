# launch-llama-server.ps1
# Agentic AI v3.3 — Эталонный запуск llama-server с Qwen3-Coder-30B-A3B
#
# PREREQUISITE: llama.cpp CUDA 13.1 binaries (release b8943 or b8946)
# See: docs/llama-cpp-setup.md
#
# FORBIDDEN: CUDA 13.2+ (tensor corruption issue #21255, Unsloth #4849)
#
# Usage: pwsh -ExecutionPolicy Bypass -File launch-llama-server.ps1
#        pwsh -File launch-llama-server.ps1 -ModelPath "E:\models\Qwen3-Coder.gguf"

param(
    [string]$ModelPath = "C:\Users\sasha\models\Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf",
    [int]$ContextSize = 32768,
    [int]$Port = 8080,
    [string]$LlamaServerPath = "C:\llama.cpp\llama-server.exe"  # b8943, CUDA 13.1
)

# Validate model file
if (-not (Test-Path $ModelPath)) {
    Write-Error "Model not found: $ModelPath"
    Write-Host "Download from HuggingFace: bartowski/Qwen3-Coder-30B-A3B-Instruct-GGUF"
    Write-Host "File: Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf (~20GB)"
    exit 1
}

# Validate llama-server binary
if (-not (Test-Path $LlamaServerPath)) {
    Write-Error "llama-server not found: $LlamaServerPath"
    Write-Host "See docs/llama-cpp-setup.md for installation instructions"
    exit 1
}

# Get physical core count (for --threads)
$physicalCores = (Get-CimInstance -ClassName Win32_Processor).NumberOfCores
if (-not $physicalCores) { $physicalCores = 8 }  # fallback for i7-13800H
Write-Host "Physical cores detected: $physicalCores"

# RTX 4060 Laptop: 8GB VRAM
# Qwen3-Coder-30B-A3B Q4_K_XL: ~5.5GB resident VRAM
# --ngl 99 = all layers on GPU
# --n-cpu-moe 34 = MoE expert routing on CPU (adjust down if OOM)

$args = @(
    "-m", $ModelPath,
    "--jinja",
    "-ngl", "99",
    "--n-cpu-moe", "34",        # MoE experts on CPU; reduce to 30-32 if OOM
    "-c", $ContextSize,
    "-fa", "on",                # Flash attention (required for -ctk/-ctv)
    "-ctk", "q8_0",
    "-ctv", "q8_0",
    "--no-mmap",
    "--threads", $physicalCores,
    "--threads-batch", $physicalCores,
    "-b", "2048",
    "-ub", "512",
    "--temp", "0.7",
    "--top-p", "0.8",
    "--top-k", "20",
    "--repeat-penalty", "1.05",
    "--port", $Port,
    "--host", "127.0.0.1"
)

Write-Host ""
Write-Host "Starting llama-server..."
Write-Host "Model: $ModelPath"
Write-Host "Context: $ContextSize tokens"
Write-Host "Port: $Port"
Write-Host "Expected throughput: 15-25 tok/s (8-12 tok/s at 32K context)"
Write-Host ""
Write-Host "Command:"
Write-Host "$LlamaServerPath $($args -join ' ')"
Write-Host ""
Write-Host "Health check after startup: http://localhost:$Port/health"
Write-Host ""

& $LlamaServerPath @args

# Tuning notes (printed on exit):
Write-Host ""
Write-Host "Tuning guide:"
Write-Host "  - OOM: reduce --n-cpu-moe by 2-4 (try 30, then 28)"
Write-Host "  - Q5/Q6 quants: --n-cpu-moe 38-40"
Write-Host "  - Smaller context (16K): ~20-30 tok/s"
Write-Host "  - -fa on is REQUIRED when using -ctk/-ctv q8_0"
