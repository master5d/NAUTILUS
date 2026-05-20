import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

def test_tech_schema_valid():
    schema_path = Path(__file__).parent.parent / "schemas" / "tech.schema.json"
    with open(schema_path) as f:
        schema = json.load(f)

    valid_meta = {
        "identifier": "proj-20260420-3f9a",
        "title": "Card Benefits Hub",
        "type": "project",
        "status": "active",
        "created": "2026-04-20",
        "updated": "2026-04-20",
        "team": "ai",
        "domain": ["fintech"],
        "tech": ["nextjs"]
    }

    # Should not raise
    validate(instance=valid_meta, schema=schema)

def test_tech_schema_missing_required():
    schema_path = Path(__file__).parent.parent / "schemas" / "tech.schema.json"
    with open(schema_path) as f:
        schema = json.load(f)

    invalid_meta = {
        "identifier": "proj-20260420-3f9a",
        # missing "title"
        "type": "project"
    }

    with pytest.raises(ValidationError):
        validate(instance=invalid_meta, schema=schema)

def test_knowledge_schema_valid():
    schema_path = Path(__file__).parent.parent / "schemas" / "knowledge.schema.json"
    with open(schema_path) as f:
        schema = json.load(f)

    valid_meta = {
        "identifier": "vault-20260420-abc1",
        "title": "Wellness & Biohacking",
        "type": "vault",
        "status": "active",
        "created": "2026-04-20",
        "updated": "2026-04-20",
        "subject_area": "wellness",
        "source_type": ["book", "course"],
        "modality": ["text", "video"]
    }

    validate(instance=valid_meta, schema=schema)
