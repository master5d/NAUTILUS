"""Unified NAUTILUS key store: labeled-HMAC derivation + payload signing.

One per-host 32-byte master yields BOTH the bearer token and the HMAC
signing key via labeled HMAC-SHA256, so only one secret is stored/rotated.
Stdlib only — HMAC-SHA256 is the single primitive; no custom crypto.
"""

import base64
import hashlib
import hmac
import json
import os

LABEL_BEARER = b"nautilus/observability/bearer/v1"
LABEL_SIGN = b"nautilus/observability/sign/v1"


def _derive(master: bytes, label: bytes) -> bytes:
    return hmac.new(master, label, hashlib.sha256).digest()


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def bearer_token(master: bytes) -> str:
    """URL-safe bearer token derived from the master (sent in Authorization)."""
    return _b64(_derive(master, LABEL_BEARER))


def signing_key(master: bytes) -> bytes:
    """HMAC key for payload signatures, derived from the master."""
    return _derive(master, LABEL_SIGN)


def sign_payload(master: bytes, body: bytes) -> str:
    mac = hmac.new(signing_key(master), body, hashlib.sha256).digest()
    return _b64(mac)


def verify_payload(master: bytes, body: bytes, sig: str) -> bool:
    expected = sign_payload(master, body)
    return hmac.compare_digest(expected, sig or "")


SECRETS_DIR = os.path.join(os.path.expanduser("~"), ".config", "nautilus", "secrets")
KEYRING_PATH = os.path.join(SECRETS_DIR, "observability.keyring.json")


def load_keyring(path: str = KEYRING_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("hosts", {})
        return data
    except Exception:
        return {"hosts": {}}


def _decode(material_b64: str) -> bytes:
    pad = "=" * (-len(material_b64) % 4)
    return base64.urlsafe_b64decode(material_b64 + pad)


def active_key_id(keyring: dict, host: str) -> str:
    return ((keyring.get("hosts") or {}).get(host) or {}).get("active", "")


def material(keyring: dict, host: str, key_id: str) -> bytes:
    entry = (((keyring.get("hosts") or {}).get(host) or {}).get("keys") or {}).get(key_id)
    if not entry:
        raise KeyError(f"no key {key_id} for host {host}")
    return _decode(entry["material"])


def acceptable(keyring: dict, host: str):
    """[(key_id, master_bytes)] for all non-revoked keys of a host."""
    out = []
    keys_map = (((keyring.get("hosts") or {}).get(host) or {}).get("keys") or {})
    for kid, entry in keys_map.items():
        if not entry.get("revoked"):
            out.append((kid, _decode(entry["material"])))
    return out
