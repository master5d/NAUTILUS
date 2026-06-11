import os
import re
from pathlib import Path
from typing import List, Dict

class SemanticRefiner:
    """
    NAUTILUS Semantic Layer.
    Refines raw transcripts into STIER-compliant graph nodes.
    Classifies into Drive (⚡) vs Duty (🛠️) and extracts Entities.
    """

    def __init__(self, model_gateway_url: str = "http://localhost:4000"):
        self.gateway_url = model_gateway_url

    def extract_stier_resonance(self, text: str) -> str:
        """
        Logic for determining Resonance:
        - ⚡ Drive: Personal interests, games, vision, creation, 'energy-giving' topics.
        - 🛠️ Duty: Obligations, maintenance, routine, 'energy-consuming' tasks.
        """
        # Simple keyword heuristic for now (will be replaced by LLM call)
        drive_keywords = ['game', 'vision', 'idea', 'creative', 'future', 'design', 'resonance']
        duty_keywords = ['fix', 'report', 'routine', 'maintenance', 'must', 'should', 'update']
        
        text_lower = text.lower()
        drive_score = sum(1 for k in drive_keywords if k in text_lower)
        duty_score = sum(1 for k in duty_keywords if k in text_lower)
        
        return "⚡" if drive_score >= duty_score else "🛠️"

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extracts key entities for the Knowledge Graph.
        """
        # Placeholder for LLM Entity Extraction (People, Tools, Concepts)
        return {
            "people": [],
            "tools": [],
            "concepts": []
        }

    def refine_transcript(self, transcript_path: Path):
        """
        Reads a transcript, updates its metadata with Resonance and Entities.
        """
        if not transcript_path.exists():
            return

        content = transcript_path.read_text(encoding="utf-8")
        resonance = self.extract_stier_resonance(content)
        
        # Update Frontmatter
        new_frontmatter = f"""---
type: transcript
resonance: {resonance}
status: refined
refined_at: {os.path.getmtime(transcript_path)}
---
"""
        # Remove old frontmatter if exists
        cleaned_content = re.sub(r'^---.*?---', '', content, flags=re.DOTALL)
        
        refined_path = transcript_path.with_suffix(".refined.md")
        refined_path.write_text(new_frontmatter + cleaned_content, encoding="utf-8")
        print(f"[+] Refined: {transcript_path.name} -> {resonance}")

if __name__ == "__main__":
    refiner = SemanticRefiner()
    target_dir = Path("C:/Users/sasha/Downloads/Notes_ACE")
    for transcript in target_dir.rglob("*.transcript.md"):
        refiner.refine_transcript(transcript)
