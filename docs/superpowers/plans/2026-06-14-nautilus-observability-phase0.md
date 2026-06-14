# NAUTILUS Observability — Phase 0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace labwatch's broken single-host model with the push-collection foundation — a unified key store, a signed payload contract, an authenticated `/ingest` endpoint, a sqlite snapshot store, and an M4 self-reporter — so the dashboard renders per-host state from snapshots instead of localhost-pinned probes.

**Architecture:** Each host runs a *reporter* that collects only its own local state and POSTs a token+HMAC-signed snapshot to the *collector* on M4. The collector verifies, stores the latest snapshot per host in sqlite, and serves `/api/state`. Phase 0 wires this loop for a single host (M4 reporting to itself) and removes the old central localhost probes.

**Tech Stack:** Python 3.12 (stdlib `http.server`, `sqlite3`, `hmac`, `hashlib`, `secrets`, `base64`), `jsonschema` (payload validation), `psutil` (host metrics). Tests: `pytest`. No new heavy stacks — borrow libraries, not frameworks.

**Spec:** `docs/superpowers/specs/2026-06-14-nautilus-observability-design.md`

---

## Scope of this plan

This plan implements **Phase 0 only** (the spec's §7 table, row 0):

- Unified key store + `nautilus-keys` helper (labeled-HMAC derivation, keyring, rotation).
- Versioned payload schema + validation.
- `/ingest` (bearer token + HMAC + anti-replay + size cap + schema).
- sqlite snapshot/history/alerts tables (alerts table created, used in Phase 2).
- M4 reporter (localhost probes + psutil host metrics + M4 domain data).
- `/api/state` assembled from snapshots, with `live/stale/down` freshness.
- Removal of the old central localhost probes (`services_health` targets).

**Out of scope (later phases, each gets its own plan once Phase 0 interfaces are concrete):**
Phase 1 (Surface reporter + wallets fix + tray), Phase 2 (watchers + `/api/alerts` + Telegram), Phase 3 (Hetzner reporter + advisory tier), Phase 4 (web-view charts redesign), Phase 5 (64GB node).

## File structure (Phase 0)

Flat modules inside `labwatch/` (matches the current `python server.py` run model — no package gymnastics; tests add the dir to `sys.path` via conftest).

| File | Responsibility |
|------|----------------|
| `labwatch/keys.py` | Labeled-HMAC key derivation (bearer + signing from one master), payload sign/verify, keyring load/material/acceptable. |
| `labwatch/keys_cli.py` | `nautilus-keys` CLI: `gen`/`list`/`rotate`/`revoke`. Never prints key material. |
| `labwatch/schema.py` | Versioned payload JSON Schema + `validate()`. |
| `labwatch/store.py` | sqlite: create tables, upsert snapshot, read snapshots, freshness classification. |
| `labwatch/collector.py` | Pure receive-side: `verify_ingest()` and `assemble_state()`. |
| `labwatch/reporter.py` | Self-report: service probes, psutil host metrics, M4 domain, build/sign/POST + spool-retry, main loop. |
| `labwatch/server.py` | **Modify:** add `/ingest`, serve `/api/state` from store, security headers, remove old localhost probes. Keep `/api/orchestrator`, static. |
| `labwatch/requirements.txt` | `jsonschema`, `psutil`. |
| `labwatch/tests/conftest.py` | Put `labwatch/` on `sys.path`; shared fixtures. |
| `labwatch/tests/test_keys.py` | Derivation, sign/verify, keyring. |
| `labwatch/tests/test_schema.py` | Good/bad payloads. |
| `labwatch/tests/test_store.py` | Upsert, read, freshness. |
| `labwatch/tests/test_collector.py` | Ingest verify (auth/HMAC/replay/size/schema), state assembly. |
| `labwatch/tests/test_reporter.py` | Payload build (mocked sources) validates against schema. |
| `labwatch/run/run-reporter.sh` | M4 launch wrapper (PATH + venv) for the reporter. |

**Canonical contract (used by both sides):** the HMAC signature covers `canonical(payload)` where
`canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")`.
The bearer token and signing key are both derived from one per-host master via labeled HMAC, so only one secret per host is stored and rotated.

---

## Task 1: Scaffold deps, test harness, and a green baseline

**Files:**
- Create: `labwatch/requirements.txt`
- Create: `labwatch/tests/conftest.py`
- Create: `labwatch/tests/test_smoke.py`

- [ ] **Step 1: Write requirements.txt**

Create `labwatch/requirements.txt`:

```
jsonschema>=4.0
psutil>=5.9
```

- [ ] **Step 2: Install into the dev venv**

Run: `python -m pip install -r labwatch/requirements.txt`
Expected: jsonschema and psutil install (or "already satisfied").

- [ ] **Step 3: Write conftest that exposes flat modules**

Create `labwatch/tests/conftest.py`:

```python
import os
import sys

LABWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if LABWATCH_DIR not in sys.path:
    sys.path.insert(0, LABWATCH_DIR)
```

- [ ] **Step 4: Write a smoke test that proves the harness works**

Create `labwatch/tests/test_smoke.py`:

```python
def test_imports_available():
    import jsonschema  # noqa: F401
    import psutil  # noqa: F401
    assert True
```

- [ ] **Step 5: Run it**

Run: `python -m pytest labwatch/tests/test_smoke.py -v`
Expected: PASS (1 passed).

- [ ] **Step 6: Commit**

```bash
git add labwatch/requirements.txt labwatch/tests/conftest.py labwatch/tests/test_smoke.py
git commit -m "test: labwatch test harness + observability deps (jsonschema, psutil)"
```

---

## Task 2: Key derivation + payload sign/verify

**Files:**
- Create: `labwatch/keys.py`
- Test: `labwatch/tests/test_keys.py`

- [ ] **Step 1: Write the failing test**

Create `labwatch/tests/test_keys.py`:

```python
import keys


def test_bearer_and_signing_keys_are_distinct_and_deterministic():
    master = b"\x01" * 32
    b1 = keys.bearer_token(master)
    b2 = keys.bearer_token(master)
    assert b1 == b2                      # deterministic
    assert keys.signing_key(master) != master
    assert keys.bearer_token(master).encode() != keys.signing_key(master)


def test_sign_then_verify_roundtrip():
    master = b"\x02" * 32
    body = b'{"a":1,"b":2}'
    sig = keys.sign_payload(master, body)
    assert keys.verify_payload(master, body, sig) is True


def test_verify_rejects_tampered_body_and_wrong_key():
    master = b"\x03" * 32
    sig = keys.sign_payload(master, b'{"a":1}')
    assert keys.verify_payload(master, b'{"a":2}', sig) is False
    assert keys.verify_payload(b"\x04" * 32, b'{"a":1}', sig) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_keys.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'keys'`.

- [ ] **Step 3: Write minimal implementation**

Create `labwatch/keys.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_keys.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add labwatch/keys.py labwatch/tests/test_keys.py
git commit -m "feat(keys): labeled-HMAC derivation + payload sign/verify"
```

---

## Task 3: Keyring load + material + acceptable keys

**Files:**
- Modify: `labwatch/keys.py`
- Test: `labwatch/tests/test_keys.py`

- [ ] **Step 1: Write the failing test (append)**

Append to `labwatch/tests/test_keys.py`:

```python
import base64


def _b64(raw):
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def test_keyring_material_and_acceptable(tmp_path):
    import json
    kr = {
        "hosts": {
            "m4": {
                "active": "m4-2",
                "keys": {
                    "m4-1": {"material": _b64(b"\xaa" * 32), "created": "t", "revoked": True},
                    "m4-2": {"material": _b64(b"\xbb" * 32), "created": "t", "revoked": False},
                },
            }
        }
    }
    p = tmp_path / "kr.json"
    p.write_text(json.dumps(kr), encoding="utf-8")

    loaded = keys.load_keyring(str(p))
    assert keys.active_key_id(loaded, "m4") == "m4-2"
    assert keys.material(loaded, "m4", "m4-2") == b"\xbb" * 32

    acc = dict(keys.acceptable(loaded, "m4"))
    assert set(acc) == {"m4-2"}          # revoked m4-1 excluded
    assert acc["m4-2"] == b"\xbb" * 32


def test_load_keyring_missing_file_returns_empty():
    assert keys.load_keyring("/no/such/keyring.json") == {"hosts": {}}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_keys.py -v`
Expected: FAIL with `AttributeError: module 'keys' has no attribute 'load_keyring'`.

- [ ] **Step 3: Write minimal implementation (append to keys.py)**

Append to `labwatch/keys.py`:

```python
import json
import os

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_keys.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add labwatch/keys.py labwatch/tests/test_keys.py
git commit -m "feat(keys): keyring load, active/material lookup, acceptable (non-revoked) keys"
```

---

## Task 4: `nautilus-keys` CLI (gen / list / rotate / revoke)

**Files:**
- Create: `labwatch/keys_cli.py`
- Test: `labwatch/tests/test_keys_cli.py`

- [ ] **Step 1: Write the failing test**

Create `labwatch/tests/test_keys_cli.py`:

```python
import json

import keys
import keys_cli


def _read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def test_gen_creates_active_key_and_no_material_in_stdout(tmp_path, capsys):
    krp = tmp_path / "kr.json"
    rc = keys_cli.main(["gen", "--host", "m4", "--keyring", str(krp)])
    assert rc == 0
    kr = _read(krp)
    kid = keys.active_key_id(kr, "m4")
    assert kid.startswith("m4-")
    mat = keys.material(kr, "m4", kid)
    assert len(mat) == 32
    out = capsys.readouterr().out
    # fingerprint printed, raw material never printed
    import base64
    assert base64.urlsafe_b64encode(mat).decode().rstrip("=") not in out
    assert kid in out


def test_rotate_adds_new_active_keeps_old_then_revoke(tmp_path):
    krp = tmp_path / "kr.json"
    keys_cli.main(["gen", "--host", "m4", "--keyring", str(krp)])
    first = keys.active_key_id(_read(krp), "m4")
    keys_cli.main(["rotate", "--host", "m4", "--keyring", str(krp)])
    kr = _read(krp)
    second = keys.active_key_id(kr, "m4")
    assert second != first
    assert {first, second} <= set(kr["hosts"]["m4"]["keys"])     # both retained
    assert dict(keys.acceptable(kr, "m4")).keys() == {first, second}  # overlap window

    keys_cli.main(["revoke", "--host", "m4", "--key-id", first, "--keyring", str(krp)])
    kr = _read(krp)
    assert set(dict(keys.acceptable(kr, "m4"))) == {second}       # old revoked
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_keys_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'keys_cli'`.

- [ ] **Step 3: Write minimal implementation**

Create `labwatch/keys_cli.py`:

```python
"""nautilus-keys — manage the unified NAUTILUS key store.

Subcommands: gen | list | rotate | revoke.
Never prints raw key material; prints key IDs and SHA-256 fingerprints only
(silent-capture standing principle).

Usage:
    python -m keys_cli gen --host m4
    python keys_cli.py list
"""

import argparse
import base64
import hashlib
import json
import os
import secrets
from datetime import datetime, timezone

import keys as keymod


def _now():
    return datetime.now(timezone.utc).isoformat()


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _fingerprint(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()[:8]


def _load(path: str) -> dict:
    return keymod.load_keyring(path)


def _save(path: str, kr: dict):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(kr, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _next_id(kr: dict, host: str) -> str:
    existing = ((kr.get("hosts") or {}).get(host) or {}).get("keys") or {}
    n = 1 + len(existing)
    return f"{host}-{n}"


def _add_key(kr: dict, host: str) -> str:
    kr.setdefault("hosts", {}).setdefault(host, {"active": "", "keys": {}})
    kid = _next_id(kr, host)
    raw = secrets.token_bytes(32)
    kr["hosts"][host]["keys"][kid] = {
        "material": _b64(raw), "created": _now(), "revoked": False,
    }
    kr["hosts"][host]["active"] = kid
    return kid


def cmd_gen(args):
    kr = _load(args.keyring)
    kid = _add_key(kr, args.host)
    _save(args.keyring, kr)
    raw = keymod.material(kr, args.host, kid)
    print(f"generated {kid} fp={_fingerprint(raw)} (active)")
    return 0


def cmd_rotate(args):
    kr = _load(args.keyring)
    if args.host not in (kr.get("hosts") or {}):
        print(f"unknown host: {args.host}")
        return 1
    kid = _add_key(kr, args.host)
    _save(args.keyring, kr)
    raw = keymod.material(kr, args.host, kid)
    print(f"rotated -> {kid} fp={_fingerprint(raw)} (active; prior keys retained for overlap)")
    return 0


def cmd_revoke(args):
    kr = _load(args.keyring)
    keys_map = (((kr.get("hosts") or {}).get(args.host) or {}).get("keys") or {})
    if args.key_id not in keys_map:
        print(f"unknown key: {args.key_id}")
        return 1
    keys_map[args.key_id]["revoked"] = True
    keys_map[args.key_id]["rotated"] = _now()
    _save(args.keyring, kr)
    print(f"revoked {args.key_id}")
    return 0


def cmd_list(args):
    kr = _load(args.keyring)
    for host, h in (kr.get("hosts") or {}).items():
        for kid, e in (h.get("keys") or {}).items():
            flag = "active" if kid == h.get("active") else ("revoked" if e.get("revoked") else "ok")
            print(f"{host} {kid} {flag} created={e.get('created')}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="nautilus-keys")
    p.add_argument("--keyring", default=keymod.KEYRING_PATH)
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen"); g.add_argument("--host", required=True); g.set_defaults(fn=cmd_gen)
    r = sub.add_parser("rotate"); r.add_argument("--host", required=True); r.set_defaults(fn=cmd_rotate)
    v = sub.add_parser("revoke"); v.add_argument("--host", required=True); v.add_argument("--key-id", required=True); v.set_defaults(fn=cmd_revoke)
    l = sub.add_parser("list"); l.set_defaults(fn=cmd_list)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_keys_cli.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add labwatch/keys_cli.py labwatch/tests/test_keys_cli.py
git commit -m "feat(keys): nautilus-keys CLI (gen/list/rotate/revoke), fingerprints only"
```

---

## Task 5: Payload schema + validation

**Files:**
- Create: `labwatch/schema.py`
- Test: `labwatch/tests/test_schema.py`

- [ ] **Step 1: Write the failing test**

Create `labwatch/tests/test_schema.py`:

```python
import schema


def _good():
    return {
        "name": "litellm", "port": 4000, "up": True, "latency_ms": 12,
    }


def good_payload():
    return {
        "services": [_good()],
        "host_metrics": {
            "cpu_pct": 18.0, "ram_used_gb": 6.4, "ram_total_gb": 16.0,
            "disk_pct": 41.0, "temp_c": 47.0, "power_w": 9.0,
        },
        "domain": {"anything": 1},
    }


def test_valid_payload_passes():
    ok, err = schema.validate(good_payload())
    assert ok is True
    assert err is None


def test_unknown_top_level_field_rejected():
    p = good_payload()
    p["surprise"] = 1
    ok, err = schema.validate(p)
    assert ok is False
    assert "surprise" in err or "additional" in err.lower()


def test_missing_required_services_rejected():
    p = good_payload()
    del p["services"]
    ok, err = schema.validate(p)
    assert ok is False


def test_wrong_type_rejected():
    p = good_payload()
    p["host_metrics"]["cpu_pct"] = "high"
    ok, err = schema.validate(p)
    assert ok is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_schema.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'schema'`.

- [ ] **Step 3: Write minimal implementation**

Create `labwatch/schema.py`:

```python
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
        "domain": {"type": "object"},  # host-specific, free-form (facts only)
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_schema.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add labwatch/schema.py labwatch/tests/test_schema.py
git commit -m "feat(schema): versioned reporter payload schema + validation"
```

---

## Task 6: Snapshot store + freshness

**Files:**
- Create: `labwatch/store.py`
- Test: `labwatch/tests/test_store.py`

- [ ] **Step 1: Write the failing test**

Create `labwatch/tests/test_store.py`:

```python
from datetime import datetime, timedelta, timezone

import store


def _iso(dt):
    return dt.isoformat()


def test_init_upsert_and_read_latest():
    conn = store.connect(":memory:")
    store.init_db(conn)
    now = datetime.now(timezone.utc)
    store.upsert_snapshot(conn, "m4", _iso(now), {"services": [], "host_metrics": {}})
    store.upsert_snapshot(conn, "m4", _iso(now + timedelta(seconds=30)),
                          {"services": [{"name": "litellm", "up": True}], "host_metrics": {}})
    snaps = store.get_snapshots(conn, now_dt=now + timedelta(seconds=31))
    assert set(snaps) == {"m4"}                      # upsert: one row per host
    assert snaps["m4"]["payload"]["services"][0]["name"] == "litellm"
    assert snaps["m4"]["freshness"] == "live"        # 1s old


def test_freshness_classification():
    assert store.freshness(10, interval=30) == "live"
    assert store.freshness(95, interval=30) == "stale"
    assert store.freshness(400, interval=30) == "down"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_store.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'store'`.

- [ ] **Step 3: Write minimal implementation**

Create `labwatch/store.py`:

```python
"""sqlite persistence for observability snapshots (+ history/alerts tables).

Phase 0 uses `snapshots` (latest per host). `history` and `alerts` tables are
created now but written/used in later phases. Thin by design — not a TSDB.
"""

import json
import sqlite3
from datetime import datetime, timezone

# Freshness thresholds (seconds). stale = 3x report interval; down = 10x.
STALE_FACTOR = 3
DOWN_FACTOR = 10


def connect(path: str, check_same_thread: bool = True) -> sqlite3.Connection:
    # The collector runs under ThreadingHTTPServer (a thread per request), so the
    # server opens this with check_same_thread=False and serializes all access
    # with a single lock. Tests use the default (single-threaded).
    conn = sqlite3.connect(path, timeout=5, check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS snapshots (
            host        TEXT PRIMARY KEY,
            ts          TEXT NOT NULL,
            received    TEXT NOT NULL,
            payload     TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS history (
            host TEXT, ts TEXT, metric TEXT, value REAL
        );
        CREATE INDEX IF NOT EXISTS idx_history_host_metric ON history(host, metric, ts);
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT, host TEXT, severity TEXT, state TEXT,
            first_seen TEXT, last_seen TEXT, resolved_at TEXT,
            PRIMARY KEY (id, host)
        );
        """
    )
    conn.commit()


def upsert_snapshot(conn, host: str, ts: str, payload: dict):
    received = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO snapshots (host, ts, received, payload) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(host) DO UPDATE SET ts=excluded.ts, received=excluded.received, "
        "payload=excluded.payload",
        (host, ts, received, json.dumps(payload, ensure_ascii=False)),
    )
    conn.commit()


def freshness(age_s: float, interval: int = 30) -> str:
    if age_s <= interval * STALE_FACTOR:
        return "live"
    if age_s <= interval * DOWN_FACTOR:
        return "stale"
    return "down"


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def get_snapshots(conn, now_dt: datetime = None, interval: int = 30) -> dict:
    now_dt = now_dt or datetime.now(timezone.utc)
    out = {}
    for row in conn.execute("SELECT host, ts, received, payload FROM snapshots"):
        try:
            age = (now_dt - _parse(row["ts"])).total_seconds()
        except Exception:
            age = float("inf")
        out[row["host"]] = {
            "ts": row["ts"],
            "received": row["received"],
            "age_s": age,
            "freshness": freshness(age, interval),
            "payload": json.loads(row["payload"]),
        }
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_store.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add labwatch/store.py labwatch/tests/test_store.py
git commit -m "feat(store): sqlite snapshots + freshness classification (history/alerts tables stubbed)"
```

---

## Task 7: Collector — verify_ingest + assemble_state

**Files:**
- Create: `labwatch/collector.py`
- Test: `labwatch/tests/test_collector.py`

- [ ] **Step 1: Write the failing test**

Create `labwatch/tests/test_collector.py`:

```python
import base64
import json
from datetime import datetime, timezone

import collector
import keys
import store


def _b64(raw):
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _keyring(master):
    return {"hosts": {"m4": {"active": "m4-1",
            "keys": {"m4-1": {"material": _b64(master), "created": "t", "revoked": False}}}}}


def _payload():
    return {"services": [{"name": "litellm", "port": 4000, "up": True}],
            "host_metrics": {"cpu_pct": 10.0}}


def _body(master, host="m4", ts=None, payload=None):
    payload = payload or _payload()
    ts = ts or datetime.now(timezone.utc).isoformat()
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    sig = keys.sign_payload(master, canon)
    return json.dumps({"host": host, "ts": ts, "sig": sig, "payload": payload}).encode()


def test_valid_ingest_accepted():
    master = b"\x11" * 32
    kr = _keyring(master)
    auth = "Bearer " + keys.bearer_token(master)
    ok, host, payload, status, err = collector.verify_ingest(auth, _body(master), kr,
                                                             now=datetime.now(timezone.utc))
    assert ok is True and host == "m4" and status == 200
    assert payload["services"][0]["name"] == "litellm"


def test_bad_bearer_rejected_401():
    master = b"\x11" * 32
    kr = _keyring(master)
    ok, *_rest, status, err = collector.verify_ingest("Bearer nope", _body(master), kr,
                                                      now=datetime.now(timezone.utc))
    assert ok is False and status == 401


def test_tampered_payload_rejected_401():
    master = b"\x11" * 32
    kr = _keyring(master)
    auth = "Bearer " + keys.bearer_token(master)
    body = json.loads(_body(master))
    body["payload"]["services"][0]["up"] = False    # tamper after signing
    ok, *_rest, status, err = collector.verify_ingest(auth, json.dumps(body).encode(), kr,
                                                      now=datetime.now(timezone.utc))
    assert ok is False and status == 401


def test_stale_timestamp_rejected_401():
    master = b"\x11" * 32
    kr = _keyring(master)
    auth = "Bearer " + keys.bearer_token(master)
    old = datetime(2000, 1, 1, tzinfo=timezone.utc).isoformat()
    ok, *_rest, status, err = collector.verify_ingest(auth, _body(master, ts=old), kr,
                                                      now=datetime.now(timezone.utc))
    assert ok is False and status == 401


def test_bad_schema_rejected_400():
    master = b"\x11" * 32
    kr = _keyring(master)
    auth = "Bearer " + keys.bearer_token(master)
    bad = {"services": "not-a-list", "host_metrics": {}}
    ok, *_rest, status, err = collector.verify_ingest(auth, _body(master, payload=bad), kr,
                                                      now=datetime.now(timezone.utc))
    assert ok is False and status == 400


def test_assemble_state_shape():
    conn = store.connect(":memory:")
    store.init_db(conn)
    now = datetime.now(timezone.utc)
    store.upsert_snapshot(conn, "m4", now.isoformat(), _payload())
    state = collector.assemble_state(conn, now_dt=now)
    assert "hosts" in state and "m4" in state["hosts"]
    assert state["hosts"]["m4"]["freshness"] == "live"
    assert state["alerts"] == []                 # Phase 2 fills this
    assert "generated" in state
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_collector.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'collector'`.

- [ ] **Step 3: Write minimal implementation**

Create `labwatch/collector.py`:

```python
"""Collector: pure receive-side logic — verify an ingest, assemble /api/state.

No network or HTTP here (server.py owns the socket); these are pure functions
so they test without sockets.
"""

import json
from datetime import datetime, timezone

import keys as keymod
import schema as schemamod
import store as storemod

MAX_BODY = 256 * 1024          # 256 KB cap
REPLAY_WINDOW_S = 120          # ±120s


def _canonical(payload) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_ingest(auth_header: str, body: bytes, keyring: dict, now: datetime = None):
    """Return (ok, host, payload, status, err).

    Checks, in order: size, JSON shape, known host, bearer token (any
    non-revoked key), HMAC over canonical payload, replay window, schema.
    """
    now = now or datetime.now(timezone.utc)
    if body is None or len(body) > MAX_BODY:
        return False, None, None, 413, "missing or oversized body"
    try:
        env = json.loads(body)
        host = env["host"]; ts = env["ts"]; sig = env["sig"]; payload = env["payload"]
    except Exception:
        return False, None, None, 400, "malformed envelope"

    accept = keymod.acceptable(keyring, host)
    if not accept:
        return False, None, None, 401, "unknown host"

    token = (auth_header or "").removeprefix("Bearer ").strip()
    matched = None
    for _kid, master in accept:
        if keymod.bearer_token(master) == token:
            matched = master
            break
    if matched is None:
        return False, None, None, 401, "bad bearer token"

    if not keymod.verify_payload(matched, _canonical(payload), sig):
        return False, None, None, 401, "bad signature"

    try:
        skew = abs((now - datetime.fromisoformat(ts)).total_seconds())
    except Exception:
        return False, None, None, 401, "bad timestamp"
    if skew > REPLAY_WINDOW_S:
        return False, None, None, 401, "timestamp outside replay window"

    ok, err = schemamod.validate(payload)
    if not ok:
        return False, None, None, 400, f"schema: {err}"

    return True, host, payload, 200, None


def assemble_state(conn, now_dt: datetime = None) -> dict:
    now_dt = now_dt or datetime.now(timezone.utc)
    hosts = storemod.get_snapshots(conn, now_dt=now_dt)
    return {
        "generated": now_dt.isoformat(),
        "hosts": hosts,
        "alerts": [],          # populated in Phase 2
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_collector.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add labwatch/collector.py labwatch/tests/test_collector.py
git commit -m "feat(collector): verify_ingest (auth/HMAC/replay/size/schema) + assemble_state"
```

---

## Task 8: Reporter — probes, host metrics, M4 domain, build/sign

**Files:**
- Create: `labwatch/reporter.py`
- Test: `labwatch/tests/test_reporter.py`

- [ ] **Step 1: Write the failing test**

Create `labwatch/tests/test_reporter.py`:

```python
import json

import keys
import reporter
import schema


def test_host_metrics_shape():
    m = reporter.host_metrics()
    # psutil-backed; values may be None on some platforms but keys must exist
    for k in ("cpu_pct", "ram_used_gb", "ram_total_gb", "disk_pct", "temp_c", "power_w"):
        assert k in m


def test_probe_down_service_is_false(monkeypatch):
    # point at a port nothing listens on
    r = reporter.probe("nothing", "http://127.0.0.1:9", timeout=0.2)
    assert r["name"] == "nothing"
    assert r["up"] is False


def test_build_payload_validates_against_schema(monkeypatch):
    monkeypatch.setattr(reporter, "probe_all", lambda cfg: [{"name": "litellm", "port": 4000, "up": True, "latency_ms": 5}])
    monkeypatch.setattr(reporter, "host_metrics", lambda: {"cpu_pct": 1.0, "ram_used_gb": 1.0,
                        "ram_total_gb": 16.0, "disk_pct": 1.0, "temp_c": None, "power_w": None})
    monkeypatch.setattr(reporter, "domain_m4", lambda: {"usage": {"total_rows": 0}})
    payload = reporter.build_payload(services_cfg=[("litellm", "http://127.0.0.1:4000/health/liveliness")])
    ok, err = schema.validate(payload)
    assert ok is True, err


def test_sign_envelope_roundtrips(monkeypatch):
    master = b"\x33" * 32
    payload = {"services": [], "host_metrics": {"cpu_pct": 1.0}}
    env = reporter.sign_envelope("m4", payload, master)
    body = json.loads(env)
    assert body["host"] == "m4"
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    assert keys.verify_payload(master, canon, body["sig"]) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_reporter.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'reporter'`.

- [ ] **Step 3: Write minimal implementation**

Create `labwatch/reporter.py`:

```python
"""Reporter: collect THIS host's own state, sign it, POST to the collector.

Phase 0 = M4 self-report. Single file (probes + host metrics + M4 domain +
build/sign/post + loop); split per-host when more hosts arrive.
"""

import http.client
import json
import os
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import keys as keymod

# --- service probes (localhost only — each host probes its OWN services) ----

def probe(name: str, url: str, timeout: float = 2.0) -> dict:
    p = urlparse(url)
    port = p.port or (443 if p.scheme == "https" else 80)
    path = p.path or "/"
    t0 = time.time()
    try:
        conn = http.client.HTTPConnection(p.hostname or "127.0.0.1", port, timeout=timeout)
        try:
            conn.request("GET", path, headers={"User-Agent": "labwatch-reporter"})
            status = conn.getresponse().status
            up = 200 <= status < 500
        finally:
            conn.close()
    except Exception:
        return {"name": name, "port": port, "up": False, "latency_ms": None}
    return {"name": name, "port": port, "up": up,
            "latency_ms": round((time.time() - t0) * 1000, 1)}


def probe_all(services_cfg) -> list:
    return [probe(name, url) for name, url in services_cfg]


# --- host metrics (psutil, best-effort per platform) -----------------------

def host_metrics() -> dict:
    import psutil
    vm = psutil.virtual_memory()
    try:
        disk = psutil.disk_usage("/").percent
    except Exception:
        disk = None
    temp = None
    try:
        sensors = psutil.sensors_temperatures()  # absent on macOS/Windows → {}
        if sensors:
            first = next(iter(sensors.values()))
            if first:
                temp = float(first[0].current)
    except Exception:
        temp = None
    return {
        "cpu_pct": float(psutil.cpu_percent(interval=0.1)),
        "ram_used_gb": round((vm.total - vm.available) / 1e9, 2),
        "ram_total_gb": round(vm.total / 1e9, 2),
        "disk_pct": float(disk) if disk is not None else None,
        "temp_c": temp,
        "power_w": None,   # populated later via platform-specific source
    }


# --- M4 domain (reuse existing labwatch collectors) ------------------------

def domain_m4() -> dict:
    import server  # reuse usage_stats/secops_state/_read_json without HTTP
    return {
        "usage": server.usage_stats(),
        "secops": server.secops_state(),
        "quotas": server._read_json(server.QUOTAS_PATH),
        "econ": server._read_json(server.ECON_PATH),
    }


# --- assemble + sign + post ------------------------------------------------

_UNSET = object()


def build_payload(services_cfg, domain=_UNSET) -> dict:
    # domain omitted  -> default to domain_m4() (the M4 self-report case)
    # domain=None/{}   -> no domain block (non-M4 hosts in later phases)
    # domain=<dict>    -> use it verbatim
    payload = {
        "services": probe_all(services_cfg),
        "host_metrics": host_metrics(),
    }
    dom = domain_m4() if domain is _UNSET else domain
    if dom:
        payload["domain"] = dom
    return payload


def sign_envelope(host: str, payload: dict, master: bytes) -> bytes:
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = keymod.sign_payload(master, canon)
    env = {"host": host, "ts": datetime.now(timezone.utc).isoformat(),
           "sig": sig, "payload": payload}
    return json.dumps(env).encode("utf-8")


def post_snapshot(ingest_url: str, host: str, master: bytes, body: bytes,
                  spool_path: str = None) -> bool:
    p = urlparse(ingest_url)
    headers = {"Authorization": "Bearer " + keymod.bearer_token(master),
               "Content-Type": "application/json"}
    try:
        conn = http.client.HTTPConnection(p.hostname, p.port or 80, timeout=5)
        conn.request("POST", p.path or "/ingest", body=body, headers=headers)
        ok = conn.getresponse().status == 200
        conn.close()
    except Exception:
        ok = False
    if not ok and spool_path:
        try:
            with open(spool_path, "ab") as f:
                f.write(body + b"\n")
        except OSError:
            pass
    return ok
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_reporter.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add labwatch/reporter.py labwatch/tests/test_reporter.py
git commit -m "feat(reporter): probes + psutil host metrics + M4 domain + sign/post"
```

---

## Task 9: Reporter main loop (config + interval + key load)

**Files:**
- Modify: `labwatch/reporter.py`
- Test: `labwatch/tests/test_reporter.py`

- [ ] **Step 1: Write the failing test (append)**

Append to `labwatch/tests/test_reporter.py`:

```python
def test_load_master_reads_active_key(tmp_path):
    import base64, json as _json
    import keys_cli
    krp = tmp_path / "kr.json"
    keys_cli.main(["gen", "--host", "m4", "--keyring", str(krp)])
    master = reporter.load_master("m4", keyring_path=str(krp))
    assert isinstance(master, bytes) and len(master) == 32


def test_run_once_posts_and_returns_bool(monkeypatch):
    captured = {}
    monkeypatch.setattr(reporter, "build_payload", lambda cfg, domain=None: {"services": [], "host_metrics": {"cpu_pct": 1.0}})
    monkeypatch.setattr(reporter, "load_master", lambda host, keyring_path=None: b"\x44" * 32)

    def fake_post(url, host, master, body, spool_path=None):
        captured["host"] = host
        captured["url"] = url
        return True

    monkeypatch.setattr(reporter, "post_snapshot", fake_post)
    ok = reporter.run_once(host="m4", ingest_url="http://127.0.0.1:4002/ingest",
                           services_cfg=[], keyring_path="x")
    assert ok is True
    assert captured["host"] == "m4"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_reporter.py -k "load_master or run_once" -v`
Expected: FAIL with `AttributeError: module 'reporter' has no attribute 'load_master'`.

- [ ] **Step 3: Write minimal implementation (append to reporter.py)**

Append to `labwatch/reporter.py`:

```python
# --- config + main loop ----------------------------------------------------

DEFAULT_SERVICES = {
    "m4": [
        ("litellm", "http://127.0.0.1:4000/health/liveliness"),
        ("stt", "http://127.0.0.1:4100/health"),
        ("labwatch", "http://127.0.0.1:4002/health"),
    ],
}


def load_master(host: str, keyring_path: str = None) -> bytes:
    kr = keymod.load_keyring(keyring_path or keymod.KEYRING_PATH)
    return keymod.material(kr, host, keymod.active_key_id(kr, host))


def run_once(host: str, ingest_url: str, services_cfg, keyring_path: str = None,
             spool_path: str = None) -> bool:
    master = load_master(host, keyring_path)
    # m4 omits the arg so build_payload defaults to domain_m4(); other hosts
    # pass domain=None (no domain block) until their domain is added in Phase 1.
    payload = build_payload(services_cfg) if host == "m4" \
        else build_payload(services_cfg, domain=None)
    body = sign_envelope(host, payload, master)
    return post_snapshot(ingest_url, host, master, body, spool_path=spool_path)


def main():
    host = os.environ.get("REPORTER_HOST", "m4")
    ingest = os.environ.get("INGEST_URL", "http://127.0.0.1:4002/ingest")
    interval = int(os.environ.get("REPORTER_INTERVAL", "30"))
    spool = os.environ.get("REPORTER_SPOOL", os.path.join(os.path.dirname(__file__), "spool.jsonl"))
    services = DEFAULT_SERVICES.get(host, [])
    while True:
        try:
            run_once(host, ingest, services, spool_path=spool)
        except Exception as e:  # never let the loop die
            print(f"[reporter] cycle error: {type(e).__name__}", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_reporter.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add labwatch/reporter.py labwatch/tests/test_reporter.py
git commit -m "feat(reporter): load_master from keyring + run_once + main loop"
```

---

## Task 10: Wire collector into server (`/ingest`, `/api/state`, headers, drop old probes)

**Files:**
- Modify: `labwatch/server.py`
- Test: `labwatch/tests/test_server_ingest.py`

- [ ] **Step 1: Write the failing integration test**

Create `labwatch/tests/test_server_ingest.py`:

```python
import base64
import json
import threading
from datetime import datetime, timezone

import http.client

import keys


def _b64(raw):
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _start_server(tmp_path, monkeypatch):
    import server
    master = b"\x55" * 32
    krp = tmp_path / "kr.json"
    krp.write_text(json.dumps({"hosts": {"m4": {"active": "m4-1",
        "keys": {"m4-1": {"material": _b64(master), "created": "t", "revoked": False}}}}}),
        encoding="utf-8")
    monkeypatch.setattr(server, "KEYRING_PATH", str(krp))
    monkeypatch.setattr(server, "DB_PATH_OBS", str(tmp_path / "labwatch.db"))
    server.init_observability()
    httpd = server.make_server(("127.0.0.1", 0))
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port, master


def _post(port, body, token):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    c.request("POST", "/ingest", body=body,
              headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    r = c.getresponse()
    out = (r.status, r.read())
    c.close()
    return out


def test_ingest_then_state_roundtrip(tmp_path, monkeypatch):
    httpd, port, master = _start_server(tmp_path, monkeypatch)
    try:
        payload = {"services": [{"name": "litellm", "port": 4000, "up": True}],
                   "host_metrics": {"cpu_pct": 5.0}}
        canon = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        env = json.dumps({"host": "m4", "ts": datetime.now(timezone.utc).isoformat(),
                          "sig": keys.sign_payload(master, canon), "payload": payload}).encode()
        status, _ = _post(port, env, keys.bearer_token(master))
        assert status == 200

        c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        c.request("GET", "/api/state")
        r = c.getresponse()
        state = json.loads(r.read()); c.close()
        assert "m4" in state["hosts"]
        assert state["hosts"]["m4"]["payload"]["services"][0]["name"] == "litellm"
        assert state["hosts"]["m4"]["freshness"] == "live"
    finally:
        httpd.shutdown()


def test_ingest_bad_token_rejected(tmp_path, monkeypatch):
    httpd, port, master = _start_server(tmp_path, monkeypatch)
    try:
        status, _ = _post(port, b'{"host":"m4","ts":"x","sig":"x","payload":{}}', "wrong")
        assert status in (400, 401)
    finally:
        httpd.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_server_ingest.py -v`
Expected: FAIL (e.g. `AttributeError: module 'server' has no attribute 'init_observability'`).

- [ ] **Step 3: Modify server.py — imports + observability wiring**

In `labwatch/server.py`, add near the existing imports (after line 19):

```python
import collector
import keys as keymod
import store as storemod
```

Add new module constants after the existing path constants (after `PORT = 4002`):

```python
KEYRING_PATH = keymod.KEYRING_PATH
DB_PATH_OBS = os.path.join(HERE, "labwatch.db")   # snapshots/history/alerts
_obs_conn = None
_obs_lock = threading.Lock()


def init_observability():
    """Open the observability DB and ensure tables exist (idempotent).

    check_same_thread=False because ThreadingHTTPServer handles each request on
    its own thread; all reads/writes are serialized by _obs_lock.
    """
    global _obs_conn
    _obs_conn = storemod.connect(DB_PATH_OBS, check_same_thread=False)
    storemod.init_db(_obs_conn)
```

- [ ] **Step 4: Modify server.py — replace the old central probes**

Delete the `services_health()` function (the `targets={...}` + ThreadPoolExecutor block) and the now-unused `_probe`, `_local_port_path`, `_litellm_url`, `_health_cache`, `_health_lock`. In `build_state()`, replace the line `"services": services_health(),` so the function becomes:

```python
def build_state():
    """Legacy aggregate retained for /api/state fallback fields (econ/quotas/budget)
    that are not yet host-scoped. Host/service data now comes from snapshots."""
    quotas = _read_json(QUOTAS_PATH)
    usage = usage_stats()
    providers_today = usage["today"]["providers"]
    budget_tpd = sum(p["tpd"] for p in quotas.get("providers", {}).values() if p.get("tpd"))
    used_tokens = sum(v["tokens"] for v in providers_today.values())
    with _obs_lock:
        obs = collector.assemble_state(_obs_conn)
    return {
        "generated": obs["generated"],
        "hosts": obs["hosts"],
        "alerts": obs["alerts"],
        "secops": secops_state(),
        "orchestrator": _read_json(ORCH_PATH),
        "quotas": quotas,
        "econ": _read_json(ECON_PATH),
        "usage": usage,
        "budget": {
            "free_tpd_capacity": budget_tpd,
            "tokens_today": used_tokens,
            "calls_today": sum(v["calls"] for v in providers_today.values()),
        },
    }
```

- [ ] **Step 5: Modify server.py — add `/ingest`, `make_server`, security headers**

In the `Handler.do_POST`, add an `/ingest` branch before the existing `/api/orchestrator` handling:

```python
        if self.path == "/ingest":
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = self.rfile.read(length) if 0 < length <= collector.MAX_BODY else None
            kr = keymod.load_keyring(KEYRING_PATH)
            ok, host, payload, status, err = collector.verify_ingest(
                self.headers.get("Authorization"), body, kr)
            if ok:
                ts = json.loads(body)["ts"]
                with _obs_lock:
                    storemod.upsert_snapshot(_obs_conn, host, ts, payload)
                self._send(200, {"ok": True})
            else:
                self._send(status, {"ok": False, "error": err})
            return
```

In `Handler._send`, after `self.send_response(code)` add hardening headers:

```python
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:")
```

Add a `make_server` factory and update `__main__` near the bottom:

```python
def make_server(addr=("127.0.0.1", PORT)):
    init_observability()
    return ThreadingHTTPServer(addr, Handler)


if __name__ == "__main__":
    srv = make_server(("127.0.0.1", PORT))
    print(f"SOVERN Labwatch on http://localhost:{PORT}")
    srv.serve_forever()
```

(Replace the previous `server = ThreadingHTTPServer(...)` / `server.serve_forever()` block.)

- [ ] **Step 6: Run the integration test**

Run: `python -m pytest labwatch/tests/test_server_ingest.py -v`
Expected: PASS (2 passed).

- [ ] **Step 7: Run the full suite**

Run: `python -m pytest labwatch/tests/ -v`
Expected: PASS (all tasks' tests green).

- [ ] **Step 8: Commit**

```bash
git add labwatch/server.py labwatch/tests/test_server_ingest.py
git commit -m "feat(server): /ingest endpoint + /api/state from snapshots + CSP headers; drop central localhost probes"
```

---

## Task 11: Update web-view to render per-host snapshots + freshness

**Files:**
- Modify: `labwatch/static/index.html`
- Test: manual (browser) — covered by the `/api/state` contract test in Task 10.

- [ ] **Step 1: Replace the services-dots renderer**

In `labwatch/static/index.html`, replace the services block (the `const names = {...}` + `#dots` innerHTML lines, ~178-181) with a per-host renderer reading the new `state.hosts` shape:

```javascript
  // hosts + services (new push-model shape)
  const hosts = s.hosts || {};
  const freshCls = f => f === 'live' ? 'up' : (f === 'stale' ? 'warn' : '');
  document.getElementById('dots').innerHTML = Object.entries(hosts).map(([host, h]) => {
    const svc = ((h.payload || {}).services || [])
      .map(x => `<span class="dot ${x.up ? 'up' : ''}">${x.name}:${x.port || '?'}</span>`).join('');
    const badge = `<span class="pill ${freshCls(h.freshness)}">${host} · ${h.freshness}</span>`;
    return `<div class="host-row">${badge} ${svc || '<span class="dim">no services</span>'}</div>`;
  }).join('') || '<span class="dim">no hosts reporting yet</span>';
```

- [ ] **Step 2: Add minimal styles for host rows**

In the `<style>` block of `index.html`, add:

```css
  .host-row { display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin:4px 0; }
  .pill.warn { color: var(--warn); }
  .dim { color: var(--dim, #888); }
```

- [ ] **Step 3: Manual verify locally**

Run (dev shell): `python labwatch/server.py` then open `http://localhost:4002`.
Expected: page loads without JS errors; "no hosts reporting yet" until a reporter posts. (A full live check happens on M4 in Task 12.)

- [ ] **Step 4: Commit**

```bash
git add labwatch/static/index.html
git commit -m "feat(web): render per-host snapshots with live/stale/down freshness badges"
```

---

## Task 12: Deploy Phase 0 to M4 (key gen, reporter daemon, verify loop)

**Files:**
- Create: `labwatch/run/run-reporter.sh`
- Ops: M4 keyring, LaunchDaemon `com.sovern.reporter`, labwatch redeploy.

> These steps run against the live M4 (`ssh m4` / `scp` from the Surface PowerShell). They are operational, not unit-tested; verification is explicit curl/log checks.

- [ ] **Step 1: Write the reporter run wrapper**

Create `labwatch/run/run-reporter.sh`:

```sh
#!/bin/sh
# M4 reporter launcher — ensures Homebrew tools on PATH and uses the labwatch venv.
export PATH="/opt/homebrew/bin:$PATH"
export REPORTER_HOST="m4"
export INGEST_URL="http://127.0.0.1:4002/ingest"
export REPORTER_INTERVAL="30"
cd "$HOME/nautilus/labwatch" || exit 1
exec "$HOME/nautilus/.venv/bin/python" reporter.py
```

- [ ] **Step 2: Sync code + deps to M4**

Run (PowerShell):
```powershell
scp labwatch/keys.py labwatch/keys_cli.py labwatch/schema.py labwatch/store.py labwatch/collector.py labwatch/reporter.py labwatch/server.py m4:/Users/sovrnnode03/nautilus/labwatch/
scp labwatch/requirements.txt m4:/Users/sovrnnode03/nautilus/labwatch/
scp labwatch/static/index.html m4:/Users/sovrnnode03/nautilus/labwatch/static/
scp labwatch/run/run-reporter.sh m4:/Users/sovrnnode03/nautilus/labwatch/run/
ssh m4 "chmod +x ~/nautilus/labwatch/run/run-reporter.sh && ~/nautilus/.venv/bin/pip install -r ~/nautilus/labwatch/requirements.txt"
```
Expected: deps install cleanly on M4.

- [ ] **Step 3: Generate the M4 key in the unified store**

Run (PowerShell):
```powershell
ssh m4 "~/nautilus/.venv/bin/python ~/nautilus/labwatch/keys_cli.py gen --host m4 && chmod 700 ~/.config/nautilus/secrets"
```
Expected: prints `generated m4-1 fp=........ (active)`. No key material printed.

- [ ] **Step 4: Restart labwatch (collector) and install the reporter daemon**

Create the daemon plist and load it (mirrors the existing `com.sovern.*` daemons):
```powershell
ssh m4 "sudo launchctl kickstart -k system/com.sovern.labwatch"
ssh m4 "printf '%s\n' '<?xml version=\"1.0\" encoding=\"UTF-8\"?>' '<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">' '<plist version=\"1.0\"><dict>' '<key>Label</key><string>com.sovern.reporter</string>' '<key>ProgramArguments</key><array><string>/Users/sovrnnode03/nautilus/labwatch/run/run-reporter.sh</string></array>' '<key>RunAtLoad</key><true/>' '<key>KeepAlive</key><true/>' '</dict></plist>' | tr -d '\r' | sudo tee /Library/LaunchDaemons/com.sovern.reporter.plist >/dev/null && sudo launchctl load -w /Library/LaunchDaemons/com.sovern.reporter.plist"
```
Expected: no errors; `com.sovern.reporter` loaded.

- [ ] **Step 5: Verify the loop end-to-end on M4**

Run (PowerShell):
```powershell
ssh m4 "sleep 35 && curl -s http://127.0.0.1:4002/api/state" 
```
Expected: JSON with `hosts.m4` present, `freshness":"live"`, and a `services` array showing `litellm` up.

- [ ] **Step 6: Verify via the tunnel from Surface**

Run (PowerShell): with the existing tunnel up (`ssh -N -L 4002:localhost:4002 m4`), open `http://localhost:4002`.
Expected: the dashboard shows an `m4 · live` host row with service dots — no phantom-red foreign services.

- [ ] **Step 7: Commit the run wrapper**

```bash
git add labwatch/run/run-reporter.sh
git commit -m "ops(reporter): M4 run wrapper + LaunchDaemon for the self-reporter (Phase 0 live)"
```

---

## Phase 0 self-review checklist (run before handoff)

- [ ] Full suite green: `python -m pytest labwatch/tests/ -v`
- [ ] gitleaks clean on the final commit: `gitleaks protect --staged --no-banner`
- [ ] `/api/state` returns `hosts.m4` live on M4; old localhost-probe phantoms gone
- [ ] No key material in any committed file or any CLI stdout
- [ ] `wallets.json` hint still appears (expected — Surface reporter is Phase 1)

---

## Roadmap (subsequent phases — each gets its own plan)

| Phase | Headline | Key new units | Depends on |
|-------|----------|---------------|------------|
| **1** | Surface reporter + tray; fix wallets correctly | `reporter` Surface domain (port of `collect-wallets.ps1`), Windows host-metrics, `tray` (pystray): SSH-tunnel mgr + indicator | Phase 0 contract |
| **2** | Watchers + alerting + Telegram escape | `watchers.py` (pure `(state,rules)->alerts`), `watchers.json`, `/api/alerts`, Telegram CC sender | Phase 0 store/state |
| **3** | Hetzner reporter + advisory tier | Hetzner reporter (CF-tunnel snapshot), pinned-allowlist pull, advisory computations (deprecation/backup/reachability) | Phases 0–2 |
| **4** | Web-view redesign + charts | per-host cards, `/api/history` rollups, vendored uPlot charts | Phases 0–3 |
| **5** | 64GB node reporter | drop-in reporter (same contract) | Phase 0 contract |

After Phase 0 lands and its interfaces are real, generate the Phase 1 plan with the writing-plans skill.
