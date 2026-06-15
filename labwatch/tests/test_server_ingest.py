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
