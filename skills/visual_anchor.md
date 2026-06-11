---
name: Visual Anchor
type: workflow
execution: stateful
description: Links Echo voice descriptions with images to create searchable semantic anchors.
---

# 🖼️ Visual Anchor Skill

This skill solves the problem of "uninterpretable images" by using **Echo** as a sensory bridge. It allows Sasha to provide personal context to visual assets that AI cannot inherently understand.

## DeepVista Mandates
- **Execution**: `stateful` (creates/updates sidecar `.md` files).
- **Dry-Run**: Must identify orphaned images and matching Echo audio snippets before merging.

## Steps

### 1. Resonance Pairing
Scan `Notes_ACE` and `Calendar/Inbox` for pairing candidates:
- **Image**: `image_name.jpg/png/svg`
- **Echo Note**: `image_name.echo.md` (created by Echo transcription) or `image_name.m4a`.

### 2. Sidecar Generation
Generate or update a sidecar Markdown file (`image_name.md`) containing:
- An embedded link to the image: `![[image_name.jpg]]`
- The transcribed text from Echo: `## 🎙️ Sasha's Context`
- Semantic tags derived from the voice note.

### 3. Knowledge Graph Injection
Inject the paired relationship into Neo4j:
- `(ImageEntity)-[:ANCHORED_BY]->(VoiceContext)`

## Usage
- **Hermes Trigger**: `hermes anchor visuals`
- **Automatic**: Triggered after `The Shredder` completion.

---

## Related Skills
- The Shredder
- Echo Sync
- Nautilus Mesh
