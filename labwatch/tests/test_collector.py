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
