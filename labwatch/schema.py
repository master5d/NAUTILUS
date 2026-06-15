"""Versioned reporter payload schema + validation (the reporter→collector contract).

Carries facts, not secrets. additionalProperties is false everywhere so an
unknown/misspelled field fails fast rather than silently passing through.
"""

from jsonschema import Draft202012Validator

SCHEMA_VERSION = 1

_SERVICE = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "up"],
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 64},
        "port": {"type": "integer", "minimum": 1, "maximum": 65535},
        "up": {"type": "boolean"},
        "latency_ms": {"type": ["number", "null"], "minimum": 0},
    },
}

_HOST_METRICS = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "cpu_pct": {"type": ["number", "null"], "minimum": 0, "maximum": 100},
        "ram_used_gb": {"type": ["number", "null"], "minimum": 0},
        "ram_total_gb": {"type": ["number", "null"], "minimum": 0},
        "disk_pct": {"type": ["number", "null"], "minimum": 0, "maximum": 100},
        "temp_c": {"type": ["number", "null"]},
        "power_w": {"type": ["number", "null"]},
    },
}

PAYLOAD_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["services", "host_metrics"],
    "properties": {
        "services": {"type": "array", "items": _SERVICE, "maxItems": 64},
        "host_metrics": _HOST_METRICS,
        "domain": {"type": "object"},
    },
}

_validator = Draft202012Validator(PAYLOAD_SCHEMA)


def validate(payload) -> tuple:
    """Return (True, None) if valid, else (False, error_message)."""
    errors = sorted(_validator.iter_errors(payload), key=lambda e: e.path)
    if not errors:
        return True, None
    e = errors[0]
    loc = "/".join(str(p) for p in e.path) or "<root>"
    return False, f"{loc}: {e.message}"
