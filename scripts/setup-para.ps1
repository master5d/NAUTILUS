# setup-para.ps1
# Felix/PARA fast path — creates ~/life/ Obsidian vault structure
# Phase 0, P4 — Agentic AI v3.3
# Run once: pwsh -ExecutionPolicy Bypass -File setup-para.ps1

$vault = "$env:USERPROFILE\life"

$dirs = @(
    "projects\01-knowledge-graph-foundation",
    "projects\02-affiliate-agency",
    "projects\03-digital-goods",
    "projects\04-android-tg-bots",
    "projects\05-yt-social",
    "projects\06-game-defi",
    "projects\07-native-windows-apps",
    "areas",
    "resources\AI-Ingest",
    "archives\evernote",
    "daily",
    "tacit"
)

foreach ($dir in $dirs) {
    $path = Join-Path $vault $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "  created: $path"
    } else {
        Write-Host "  exists:  $path"
    }
}

# Seed Atlas/Workflows/ files (only if not present)
$tacitFiles = @{
    "communication-preferences.md" = @"
---
title: Communication Preferences
updated: $(Get-Date -Format 'yyyy-MM-dd')
---

## Preferred channels
- Telegram (primary control plane)
- Claude Code CLI (deep work)

## Response style
- Concise by default; expand on request
- Russian + English mix acceptable
- No emoji unless explicitly requested

## Feedback style
- Direct corrections welcome
- Flag when assumptions are made
"@
    "workflow-habits.md" = @"
---
title: Workflow Habits
updated: $(Get-Date -Format 'yyyy-MM-dd')
---

## Daily rhythm
- Morning: review overnight digests, set sprint focus
- Deep work: local llama.cpp + Claude Code sessions
- Evening: daily.md consolidation via Hermes

## Coding style
- Solo Vibe Coder — speed > ceremony
- Plan mode before non-trivial changes
- Verification step before claiming done

## Tools order of preference
1. Claude Code CLI (depth)
2. Aider (CLI/git refactors)
3. Cline (VS Code long sessions)
"@
    "hard-rules.md" = @"
---
title: Hard Rules
updated: $(Get-Date -Format 'yyyy-MM-dd')
---

## Sovereignty rules
- Surface Laptop NEVER production server
- No Cursor (proprietary context routing)
- No Trae IDE (ByteDance telemetry, 5yr retention)
- No Stitch/Google (sovereignty-hostile)
- CUDA 13.2+ FORBIDDEN for llama.cpp (tensor corruption, issue #21255)

## Cost rules
- Walk-away pricing: every subscription must have exit path
- GCP $300 credit: budget alert at $250, walk away day 90
- Claude Code Max: only if >50M tokens/month measured

## Security
- 2x YubiKey 5C NFC on all critical accounts
- Gitleaks pre-commit on all repos
- Never commit credentials; use env vars

## Agent rules
- No self-modification meta-agent (Loop 3 verdict)
- stateful skills require --dry-run or confirmation
- Hermes = orchestration only, NOT coding harness
"@
    "lessons-from-past-mistakes.md" = @"
---
title: Lessons from Past Mistakes
updated: $(Get-Date -Format 'yyyy-MM-dd')
---

## v3.0 → v3.1
- CrewAI as primary orchestrator — too much ceremony, replaced by Pydantic AI
- Custom Next.js dashboard — productivity trap for solo operator

## v3.1 → v3.2
- Vulkan backend for llama.cpp — 5GB VRAM claim unverified, CUDA wins
- WSL2 for Hermes — unnecessary complexity, ollama-native exists
- Neo4j JVM on laptop — memory bloat, replaced by FalkorDB

## v3.2 → v3.3
- Building graphiti from scratch day 1 — PARA fast path first
- thinking_budget_tokens — deprecated in Claude 4.6+, use effort parameter
- 1-phase graphiti migration — 2-phase (PARA first) is safer

## Ongoing watch
- Pyrogram — abandoned, use aiogram 3.x
- Fly.io free tier — closed Oct 2024
"@
}

foreach ($name in $tacitFiles.Keys) {
    $path = Join-Path $vault "tacit\$name"
    if (-not (Test-Path $path)) {
        Set-Content -Path $path -Value $tacitFiles[$name] -Encoding UTF8
        Write-Host "  created: $path"
    } else {
        Write-Host "  exists:  $path (skipped)"
    }
}

# Create today's daily note
$today = Get-Date -Format 'yyyy-MM-dd'
$dailyPath = Join-Path $vault "daily\$today.md"
if (-not (Test-Path $dailyPath)) {
    $dailyContent = @"
---
date: $today
---

## Focus
- [ ] Phase 0: PARA setup complete
- [ ] Phase 0: Hermes launch
- [ ] Phase 0: Skills schema

## Notes


## Durable facts to consolidate

"@
    Set-Content -Path $dailyPath -Value $dailyContent -Encoding UTF8
    Write-Host "  created: $dailyPath"
}

# Create .obsidian stub so Obsidian recognizes the vault
$obsidianDir = Join-Path $vault ".obsidian"
if (-not (Test-Path $obsidianDir)) {
    New-Item -ItemType Directory -Path $obsidianDir -Force | Out-Null
    Set-Content -Path "$obsidianDir\app.json" -Value '{}' -Encoding UTF8
    Write-Host "  created: .obsidian/app.json (vault marker)"
}

Write-Host ""
Write-Host "PARA vault ready at: $vault"
Write-Host "Open in Obsidian: File > Open vault > $vault"
