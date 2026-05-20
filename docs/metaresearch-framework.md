# Meta-Research Framework: Automation and Cron Specification

## 1. Objective
Enable autonomous monitoring, evaluation, and consolidation of new technical inputs (papers, tools, newsletters) into the SOVRN memory (PARA/Graphiti) and skill ecosystem.

## 2. Components
- **Ingest**: Apify (scraping), n8n (Gmail "AI Ingest"/RSS), Karakeep (Web).
- **Process**: Hermes Skill `research_consolidate` (Extraction + Evaluation).
- **Memory**: Write to `~/life/Atlas/References/research/` + Graphiti Episode.
- **Trigger**: Cron (Linux crontab) calling `hermes gateway run`.

## 3. Data Flow
1. **Cron Trigger**: Nightly trigger at 03:00 AM.
2. **Collection**: Fetch pending items from `AI-Ingest` folder and external webhooks.
3. **Reasoning Step**:
   - Extraction: Use Qwen3-8B (local) to extract entities/TLDR.
   - Alignment: Use 'fast-pool' (LiteLLM) to score novelty (0-1) vs. SOVRN v3.3.
4. **Action**:
   - If novelty > 0.8: Create a high-priority task in Todoist/PARA.
   - If contradictory: Log to `~/life/Atlas/Workflows/contradictions.md` for manual review.
5. **Consolidation**: Append to PARA Resources and trigger Graphiti episode write.

## 4. Cron Configuration
```bash
# Research Consolidation: Run every night at 3 AM
0 3 * * * /usr/local/bin/hermes run research_consolidate --context "daily consolidation"

# Weekly Research Digest: Every Monday at 9 AM
0 9 * * 1 /usr/local/bin/hermes run research_digest --deliver "telegram"
```
