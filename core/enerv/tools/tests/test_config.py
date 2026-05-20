import json
import pytest
from pathlib import Path
from tools.core.config import ScopeConfig

def test_load_scope_json(tmp_path):
    scope_data = {
        "root": "E:\\",
        "whitelisted": [
            {
                "name": "Wellness & Biohacking",
                "type": "vault",
                "default_confidentiality": "personal"
            },
            {
                "name": "Client Cases",
                "type": "vault",
                "default_confidentiality": "sensitive"
            }
        ],
        "ignored_patterns": ["$RECYCLE.BIN", "~*", "Thumbs.db"]
    }
    scope_file = tmp_path / "scope.json"
    scope_file.write_text(json.dumps(scope_data))

    config = ScopeConfig.load(scope_file)
    assert config.root == "E:\\"
    assert len(config.whitelisted) == 2
    assert config.whitelisted[0]["name"] == "Wellness & Biohacking"

def test_should_index(tmp_path):
    scope_data = {
        "root": "E:\\",
        "whitelisted": [
            {"name": "Wellness & Biohacking", "type": "vault", "default_confidentiality": "personal"}
        ],
        "ignored_patterns": []
    }
    scope_file = tmp_path / "scope.json"
    scope_file.write_text(json.dumps(scope_data))

    config = ScopeConfig.load(scope_file)
    assert config.should_index("Wellness & Biohacking") == True
    assert config.should_index("NonExistent") == False

def test_get_default_confidentiality(tmp_path):
    scope_data = {
        "root": "E:\\",
        "whitelisted": [
            {"name": "Client Cases", "type": "vault", "default_confidentiality": "sensitive"}
        ],
        "ignored_patterns": []
    }
    scope_file = tmp_path / "scope.json"
    scope_file.write_text(json.dumps(scope_data))

    config = ScopeConfig.load(scope_file)
    assert config.get_default_confidentiality("Client Cases") == "sensitive"
    assert config.get_default_confidentiality("Unknown") == "personal"  # Default fallback
