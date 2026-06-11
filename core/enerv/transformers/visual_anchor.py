import os
import json
from pathlib import Path
from typing import Optional, Dict

class VisualAnchor:
    """
    NAUTILUS Multimodal Anchor Module.
    Pairs images with voice-transcribed descriptions (Voice-Shadows) 
    to create a searchable semantic layer for visual assets.
    """

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.svg'}

    def pair_voice_shadow(self, image_path: Path) -> Optional[Path]:
        """
        Finds a transcript file with the same name as the image.
        If image is 'scheme_01.png', looks for 'scheme_01.transcript.md' or 'scheme_01.md'.
        """
        base_name = image_path.stem
        # Possible transcript patterns
        patterns = [f"{base_name}.transcript.md", f"{base_name}.md"]
        
        for pattern in patterns:
            shadow_path = image_path.parent / pattern
            if shadow_path.exists():
                return shadow_path
        return None

    def generate_metadata(self, image_path: Path, transcript_path: Optional[Path]) -> Dict:
        """
        Generates a consolidated metadata object for the image.
        Includes visual descriptors and user voice comments.
        """
        metadata = {
            "id": image_path.name,
            "type": "visual_anchor",
            "path": str(image_path.absolute()),
            "resonance": "⚡", # Default to Drive for manual captures
            "voice_shadow": str(transcript_path.absolute()) if transcript_path else None,
            "content_summary": ""
        }
        
        if transcript_path:
            # Extract content from the voice shadow
            content = transcript_path.read_text(encoding="utf-8")
            metadata["content_summary"] = content[:500] # Grab initial context
            
        return metadata

    def process_directory(self, dir_path: Path):
        """Scans directory to link images with their voice shadows."""
        print(f"[*] Linking Visual Anchors in: {dir_path}")
        anchors = []
        
        for file in dir_path.rglob("*"):
            if file.suffix.lower() in self.image_extensions:
                shadow = self.pair_voice_shadow(file)
                if shadow:
                    print(f"[+] Anchor Found: {file.name} <-> {shadow.name}")
                    meta = self.generate_metadata(file, shadow)
                    anchors.append(meta)
        
        # Save anchor registry for the Knowledge Graph
        registry_path = dir_path / "visual_anchors.json"
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(anchors, f, indent=4, ensure_ascii=False)
        
        print(f"[!] Created registry with {len(anchors)} anchors at {registry_path}")

if __name__ == "__main__":
    # Example usage for the current sandbox
    vault = Path("C:/Users/sasha/Downloads/Notes_ACE")
    anchor_manager = VisualAnchor(vault)
    anchor_manager.process_directory(vault)
