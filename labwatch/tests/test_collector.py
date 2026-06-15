import base64
import json
from datetime import datetime, timedelta, timezone

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


def test_missing_authorization_header_rejected_401():
    master = b"\x11" * 32
    kr = _keyring(master)
    for auth in (None, ""):
        ok, *_rest, status, err = collector.verify_ingest(auth, _body(master), kr,
                                                          now=datetime.now(timezone.utc))
        assert ok is False and status == 401


def test_revoked_key_rejected_401():
    master = b"\x11" * 32
    kr = _keyring(master)
    kr["hosts"]["m4"]["keys"]["m4-1"]["revoked"] = True
    auth = "Bearer " + keys.bearer_token(master)
    ok, *_rest, status, err = collector.verify_ingest(auth, _body(master), kr,
                                                      now=datetime.now(timezone.utc))
    assert ok is False and status == 401


def test_dual_key_rotation_overlap_accepted():
    m1 = b"\x11" * 32
    m2 = b"\x22" * 32
    kr = {"hosts": {"m4": {"active": "m4-2", "keys": {
        "m4-1": {"material": _b64(m1), "created": "t", "revoked": False},
        "m4-2": {"material": _b64(m2), "created": "t", "revoked": False},
    }}}}
    auth = "Bearer " + keys.bearer_token(m1)   # old key still valid during overlap
    ok, host, payload, status, err = collector.verify_ingest(auth, _body(m1), kr,
                                                            now=datetime.now(timezone.utc))
    assert ok is True and status == 200


def test_replay_window_boundaries():
    master = b"\x11" * 32
    kr = _keyring(master)
    auth = "Bearer " + keys.bearer_token(master)
    now = datetime.now(timezone.utc)
    ts_edge = (now - timedelta(seconds=120)).isoformat()      # exactly 120s → accepted
    ok, *_r, status, _e = collector.verify_ingest(auth, _body(master, ts=ts_edge), kr, now=now)
    assert ok is True
    ts_over = (now - timedelta(seconds=121)).isoformat()      # 121s old → rejected
    ok, *_r, status, _e = collector.verify_ingest(auth, _body(master, ts=ts_over), kr, now=now)
    assert ok is False and status == 401
    ts_future = (now + timedelta(seconds=121)).isoformat()    # 121s future → rejected
    ok, *_r, status, _e = collector.verify_ingest(auth, _body(master, ts=ts_future), kr, now=now)
    assert ok is False and status == 401


def test_oversized_body_rejected_413():
    master = b"\x11" * 32
    kr = _keyring(master)
    auth = "Bearer " + keys.bearer_token(master)
    big = b"x" * (collector.MAX_BODY + 1)
    ok, *_rest, status, err = collector.verify_ingest(auth, big, kr, now=datetime.now(timezone.utc))
    assert ok is False and status == 413


def test_tick_fires_service_down_and_assemble_includes_it():
    conn = store.connect(":memory:")
    store.init_db(conn)
    now = datetime.now(timezone.utc)
    payload = {"services": [{"name": "ollama", "port": 11434, "up": False}],
               "host_metrics": {"cpu_pct": 5.0}}
    store.upsert_snapshot(conn, "surface", now.isoformat(), payload)
    rules = {"service-down": {"enabled": True, "severity": "critical", "channels": ["tray"]}}

    state, fired = collector.tick(conn, rules, now_dt=now)
    assert any(a["id"] == "service-down:ollama" for a in fired)

    state2 = collector.assemble_state(conn, now_dt=now)
    ids = {a["id"] for a in state2["alerts"]}
    assert "service-down:ollama" in ids
