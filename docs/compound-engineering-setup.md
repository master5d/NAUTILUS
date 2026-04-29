# Compound Engineering Plugin Setup

Agentic AI v3.3 | Phase 0 P2

## What it is

Compound Engineering plugin by Klaassen — adds structured coding loop to Claude Code:
- `/workflows` — multi-step task sequences with checkpoints
- `/lfg` — fast execution mode with automatic learning capture to CLAUDE.md

Loop: **Plan → Work → Assess → Compound**

## Installation

```bash
# In Claude Code CLI:
claude code plugin install compound-engineering

# Or via Claude Code marketplace (if available in your version)
```

If the above fails (plugin name may vary):
1. Check Claude Code marketplace: `/marketplace` or `claude marketplace`
2. Search "Compound Engineering" or "Klaassen"
3. Alternatively: https://github.com/klaassenj/compound-engineering (check for latest install instructions)

## Verify installation

```bash
# In a Claude Code session, type:
/workflows
# Should show available workflow templates

/lfg
# Should enter fast execution mode
```

## Usage in Agentic AI v3.3

The `compound_engineering` Hermes skill (`~/.hermes/skills/compound_engineering.md`) wraps this plugin.

**Typical flow:**
1. Hermes receives task via Telegram
2. Hermes dispatches to Claude Code with `compound_engineering` skill active
3. Claude Code runs `/workflows` for structured tasks or `/lfg` for fast edits
4. After completion, learnings captured to CLAUDE.md + daily note

## Review agents (run in Assess phase)

The plugin triggers 3 parallel review agents after each Work phase:
- **Security reviewer** — OWASP top 10, secrets, injection
- **Architect reviewer** — design decisions, tech debt, v3.x alignment
- **Quality reviewer** — test coverage, edge cases, error handling

Each produces a structured report that feeds the Compound step.
