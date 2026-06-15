import base64
import json
import threading
from datetime import datetime, timezone

import http.client

import keys


def _b64(raw):
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _start(tmp_path, monkeypatch):
    import server
    master = b"\x66" * 32
    krp = tmp_path / "kr.json"
    krp.write_text(json.dumps({"hosts": {"surface": {"active": "s-1",
        "keys": {"s-1": {"material": _b64(master), "created": "t", "revoked": False}}}}}),
        encoding="utf-8")
    monkeypatch.setattr(server, "KEYRING_PATH", str(krp))
    monkeypatch.setattr(server, "DB_PATH_OBS", str(tmp_path / "labwatch.db"))
    httpd = server.make_server(("127.0.0.1", 0))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port, master


def _ingest(port, master, payload):
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    env = json.dumps({"host": "surface", "ts": datetime.now(timezone.utc).isoformat(),
                      "sig": keys.sign_payload(master, canon), "payload": payload}).encode()
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    c.request("POST", "/ingest", body=env,
              headers={"Authorization": "Bearer " + keys.bearer_token(master)})
    st = c.getresponse().status
    c.close()
    return st


def test_ingest_down_service_surfaces_in_api_alerts(tmp_path, monkeypatch):
    httpd, port, master = _start(tmp_path, monkeypatch)
    try:
        payload = {"services": [{"name": "ollama", "port": 11434, "up": False}],
                   "host_metrics": {"cpu_pct": 1.0}}
        assert _ingest(port, master, payload) == 200

        c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        c.request("GET", "/api/alerts")
        body = json.loads(c.getresponse().read()); c.close()
        ids = {a["id"] for a in body["alerts"]}
        assert "service-down:ollama" in ids
        assert body["max_severity"] == "critical"
    finally:
        httpd.shutdown()
