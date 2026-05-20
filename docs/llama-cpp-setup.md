# llama.cpp CUDA 13.1 Setup — Windows 11

SOVRN v3.3 | Phase 0

## Critical version constraints

| | OK | FORBIDDEN |
|--|--|--|
| CUDA | 13.1 | **13.2+** (tensor corruption issue #21255, Unsloth #4849, fix unconfirmed in 13.3) |
| llama.cpp release | b8943 or b8946 | anything built against CUDA 13.2+ |
| Model format | GGUF | other formats need conversion first |

## Step 1: Download llama.cpp binary

1. Go to: https://github.com/ggml-org/llama.cpp/releases
2. Find release **b8943** or **b8946**
3. Download: `llama-b8943-bin-win-cuda-cu12.1-x64.zip` (CUDA 12.1 binaries run fine on CUDA 13.1 runtime)
4. Extract to `C:\llama.cpp\`
5. Verify: `C:\llama.cpp\llama-server.exe` exists

> Note: If the release page only shows newer builds, use the Releases search:
> `https://github.com/ggml-org/llama.cpp/releases/tag/b8943`

## Step 2: Install CUDA Toolkit 13.1 (if not present)

Check current CUDA version:
```powershell
nvcc --version
# or
nvidia-smi | Select-String "CUDA Version"
```

If CUDA version is 13.2+, do NOT use those binaries with llama.cpp.
Install CUDA 13.1 toolkit alongside (multiple CUDA versions can coexist):
- Download from NVIDIA Developer: CUDA Toolkit Archive → 13.1

## Step 3: Download Qwen3-Coder-30B-A3B model

**Model:** `Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf`
**Size:** ~20GB
**Source:** HuggingFace — bartowski/Qwen3-Coder-30B-A3B-Instruct-GGUF

```powershell
# Install huggingface-cli if needed
pip install huggingface_hub

# Download (saves to ~/models/ by default)
huggingface-cli download bartowski/Qwen3-Coder-30B-A3B-Instruct-GGUF `
  Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf `
  --local-dir "$env:USERPROFILE\models"
```

Alternatively download via browser and place at:
`C:\Users\sasha\models\Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf`

## Step 4: Launch

```powershell
# Use the pre-configured launch script:
pwsh -ExecutionPolicy Bypass -File "C:\telo\Efforts\Ongoing\SOVERN\Atlas\Scripts\launch-llama-server.ps1"

# Or with custom model path:
pwsh -File launch-llama-server.ps1 -ModelPath "E:\models\Qwen3-Coder.gguf"
```

## Step 5: Verify

```powershell
# After startup (takes ~30s to load 20GB model):
Invoke-RestMethod http://localhost:8080/health
# Expected: {"status":"ok"}

# Test completion:
$body = @{model="qwen3-coder"; messages=@(@{role="user"; content="Hello"})} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8080/v1/chat/completions -Method POST `
  -ContentType "application/json" -Body $body
```

## Tier ladder

| Model | Use case | VRAM | Speed |
|-------|----------|------|-------|
| Qwen3-Coder-30B-A3B Q4 | Daily coding (primary) | ~5.5GB | 15–25 tok/s |
| Qwen3.6-35B-A3B Q4 | Heavy reasoning fallback | ~7GB | 12–18 tok/s |
| Qwen3.5-9B Q4 | Fast autocomplete / 200K ctx | full GPU | 50+ tok/s |
| Qwen3-8B Instruct Q4 | graphiti extraction LLM | ~5GB | 30–50 tok/s |

## OOM troubleshooting

If you get out-of-memory errors:
1. Reduce `--n-cpu-moe` from 34 → 30 → 28 (MoE experts on CPU)
2. For Q5/Q6 quants: use `--n-cpu-moe 38-40`
3. Reduce context: `-c 16384` instead of 32768
4. Flash attention (`-fa on`) is REQUIRED when using `-ctk q8_0 -ctv q8_0`
