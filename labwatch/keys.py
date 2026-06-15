"""Unified NAUTILUS key store: labeled-HMAC derivation + payload signing.

One per-host 32-byte master yields BOTH the bearer token and the HMAC
signing key via labeled HMAC-SHA256, so only one secret is stored/rotated.
Stdlib only — HMAC-SHA256 is the single primitive; no custom crypto.
"""

import base64
import hashlib
import hmac

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
