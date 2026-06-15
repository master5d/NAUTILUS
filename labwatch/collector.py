"""Collector: pure receive-side logic — verify an ingest, assemble /api/state.

No network or HTTP here (server.py owns the socket); these are pure functions
so they test without sockets.
"""

import hmac
import json
from datetime import datetime, timezone

import keys as keymod
import schema as schemamod
import store as storemod
import watchers as watchersmod

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
        if hmac.compare_digest(keymod.bearer_token(master), token):
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
        "alerts": storemod.get_active_alerts(conn, now_dt=now_dt),
    }


def tick(conn, rules, now_dt: datetime = None):
    """One evaluation cycle: assemble state, evaluate rules, reconcile alerts.
    Returns (state, fired_alerts)."""
    state = assemble_state(conn, now_dt=now_dt)
    fired = watchersmod.evaluate(state, rules)
    storemod.reconcile_alerts(conn, fired, now_dt=now_dt)
    return state, fired
