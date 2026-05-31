---
name: Resonance Audit
type: workflow
execution: stateful
description: Audit the Efforts folder to balance "Drive" (Interests) and "Duty" (Obligations) projects using the STIER model.
---

# ⚖️ Resonance Audit Skill

This skill allows the **Hermes Agent** to monitor the user's cognitive bandwidth and energy balance. It prevents burnout by ensuring that the "Adulting" chores don't overwhelm the "Solo Vibe" interests.

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
- **If Ratio > 1.0:** Trigger **Focus Warning**. Ensure high-energy projects aren't causing neglect of essential maintenance.
- **Alchemy Suggestion:** Identify a Duty project that has been active for >10 days and suggest an "Automation Bridge" to a Drive interest.

## Side Effects
- Sends a **Resonance Report** to the Telegram control plane.
- May suggest moving folders to `Efforts/Simmering`.
- Updates the `Interests MOC.md` with current project links.

## Usage
- **Hermes Cron:** Run every Sunday at 18:00 for the week ahead.
- **Manual Trigger:** `hermes audit resonance`

---

## Related Skills
- Architect Framing
- Dry Run Gate
- Consolidate Daily
