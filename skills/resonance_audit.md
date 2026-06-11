---
name: Resonance Audit
type: workflow
execution: stateful
description: Audit the Efforts folder to balance "Drive" (Interests) and "Duty" (Obligations) projects using the STIER model and the NAUTILUS Digest & Encode architecture.
---

# ⚖️ Resonance Audit & Semantic Layers

## 🏛️ NAUTILUS: Digest & Encode
The workspace follows a three-layer refinement process to maintain a high signal-to-noise ratio in the Knowledge Graph:

### Layer 1: The Shredder (Media Destruction)
- **Tool:** `core/enerv/transformers/media_shredder.py`
- **Action:** Convert binary media (mp4, mp3) into structured `.transcript.md` files.
- **Goal:** Replace large binary bloat with searchable, semantic text.

### Layer 2: Multimodal Anchors (Visual Context)
- **Tool:** `core/enerv/transformers/visual_anchor.py`
- **Action:** Link images to "Voice-Shadow" transcripts (manual voice descriptions).
- **Goal:** Enable searching images by user-defined intent and voice context.

### Layer 3: Resonance Graph (STIER)
- **Tool:** `core/enerv/transformers/semantic_refiner.py`
- **Action:** Classify nodes into **⚡ Drive** (Interests) or **🛠️ Duty** (Obligations).
- **Goal:** Ensure the Knowledge Graph prioritizes energy-giving creation over routine maintenance.

---

# ⚖️ Resonance Audit Logic

This skill allows the **Hermes Agent** to monitor cognitive bandwidth and energy balance.

## Steps

### 1. Project Classification
Scan `Efforts/On` and `Efforts/Ongoing` for project prefixes and frontmatter:
- **Drive (⚡):** Projects linked to `Interests MOC`.
- **Duty (🛠️):** Maintenance or administrative projects.

### 2. Bandwidth Calculation
Calculate the **Resonance Ratio**:
- `Ratio = Count(Drive) / Count(Duty)`

### 3. Energy Forecast
Analyze recent `Calendar/Logs/` to see where time was actually spent versus the intended priority.

### 4. Recommendation Engine
- **If Ratio < 0.3:** Trigger **Burnout Alert**. Recommend demoting one Duty to `Simmering` or starting a 2-hour "Drive Sprint".
- **Alchemy Suggestion:** Identify a Duty project that has been active for >10 days and suggest an "Automation Bridge" to a Drive interest.

## Side Effects
- Updates `resonance` metadata in transcripts.
- Updates the `Interests MOC.md` with current project links.

## Usage
- **Hermes Cron:** Run every Sunday at 18:00 for the week ahead.
- **Manual Trigger:** `hermes audit resonance`
