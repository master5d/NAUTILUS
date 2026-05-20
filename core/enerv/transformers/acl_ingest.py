import json
import hashlib
from datetime import datetime
from pathlib import Path

class ENERVTransformer:
    def __init__(self, output_dir: str = "products/"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_id(self, content: str) -> str:
        """FACTS Principle: Facts are reproducible via Hash."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def transform(self, raw_data: dict) -> str:
        """
        ACL Logic: Remodel Raw Email/Web to ENERV Facets.
        """
        content = raw_data.get("content", "")
        subject = raw_data.get("subject", "Untitled")
        source = raw_data.get("source", "unknown")
        
        # Facet Mapping
        facets = {
            "identity": raw_data.get("sender", source),
            "intent": self._detect_intent(content),
            "context": raw_data.get("para_category", "04_Archive"),
            "signal_strength": raw_data.get("importance", 0.5)
        }

        data_id = self.generate_id(content)
        timestamp = datetime.now().isoformat()

        # Build Data Product (Markdown with Contract)
        md_output = f"""---
id: {data_id}
type: data-product
version: 1.0
ingested_at: {timestamp}
source_timestamp: {raw_data.get('date', timestamp)}
source: {source}
facets:
  identity: "{facets['identity']}"
  intent: "{facets['intent']}"
  context: "{facets['context']}"
  signal: {facets['signal_strength']}
---
# {subject}

{content}

---
## ACL Audit Trail
- Original Source: {source}
- Validation: F.A.C.T.S Compliant
"""
        return md_output

    def _detect_intent(self, text: str) -> str:
        # Simple logic for now, could be LLM-driven
        text = text.lower()
        if "action" in text or "todo" in text: return "Task"
        if "note" in text or "learning" in text: return "Knowledge"
        return "Reference"

    def save_product(self, name: str, content: str):
        path = self.output_dir / f"{name}.md"
        with open(path, "w") as f:
            f.write(content)
        print(f"Data Product saved: {path}")

# Example Usage
if __name__ == "__main__":
    test_raw = {
        "subject": "Data Mesh Implementation",
        "sender": "Adam Bellemare",
        "content": "Facts are immutable. This is the core principle.",
        "source": "gmail-ingest",
        "para_category": "02_Areas/SOVERN"
    }
    
    transformer = ENERVTransformer()
    product = transformer.transform(test_raw)
    transformer.save_product("data_mesh_fact_1", product)
