---
name: The Shredder
type: workflow
execution: stateful
description: Automated bilingual (RU/EN) transcription of media files using Echo.
---

# 📼 The Shredder Skill

This skill implements the **Media Digest Pipeline** for NAUTILUS. It converts raw sensory data (video/audio) into searchable Knowledge Graph nodes.

## DeepVista Mandates
- **Execution**: `stateful` (creates files in `Calendar/Inbox` and `Notes_ACE`).
- **Dry-Run**: Must list target media files and expected output paths before execution.

## Steps

### 1. Ingest Scan
Scan `C:\telo\Calendar\Inbox` and `C:\telo\Notes_ACE` for unprocessed media:
- Extensions: `.mp4`, `.mkv`, `.mov`, `.mp3`, `.wav`, `.m4a`.
- Ignore files that already have a `.transcript.md` sibling.

### 2. Transcription via Echo
Invoke the **Echo** bilingual engine for each file:
- Mode: Local-first inference.
- Language: Auto-detect (RU/EN).
- Output: Structured Markdown with `type: transcript` frontmatter.

### 3. Verification & Cleanup
- Preserve original video for manual verification (Phase 1).
- In Phase 2 (Future), automatically move verified originals to `Atlas/Archives/Media/`.

## Usage
- **Hermes Trigger**: `hermes shred inbox`
- **Manual Trigger**: `python core/enerv/transformers/media_shredder.py`

---

## Related Skills
- Resonance Audit
- Nautilus Mesh
- Echo Sync
