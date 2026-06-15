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
    master = b"\x77" * 32
    krp = tmp_path / "kr.json"
    krp.write_text(json.dumps({"hosts": {"surface": {"active": "s-1",
        "keys": {"s-1": {"material": _b64(master), "created": "t", "revoked": False}}}}}),
        encoding="utf-8")
    monkeypatch.setattr(server, "KEYRING_PATH", str(krp))
    monkeypatch.setattr(server, "DB_PATH_OBS", str(tmp_path / "labwatch.db"))
    httpd = server.make_server(("127.0.0.1", 0))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return server, httpd, port, master


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


def test_critical_fires_and_clears_telegram(tmp_path, monkeypatch):
    server, httpd, port, master = _start(tmp_path, monkeypatch)
    import notify
    sent = []
    monkeypatch.setattr(server, "_tg_token", "TOK")
    monkeypatch.setattr(server, "_tg_chat", "42")
    monkeypatch.setattr(server, "_tg_notified", set())
    monkeypatch.setattr(notify, "send_message",
                        lambda token, chat, text, timeout=5.0: sent.append(text) or True)
    try:
        assert _ingest(port, master,
                       {"services": [{"name": "ollama", "port": 11434, "up": False}],
                        "host_metrics": {"cpu_pct": 1.0}}) == 200
        assert any("ollama" in s and s.startswith("🚨") for s in sent)

        assert _ingest(port, master,
                       {"services": [{"name": "ollama", "port": 11434, "up": True}],
                        "host_metrics": {"cpu_pct": 1.0}}) == 200
        assert any(s.startswith("✅") for s in sent)
    finally:
        httpd.shutdown()


def test_no_telegram_when_unconfigured(tmp_path, monkeypatch):
    server, httpd, port, master = _start(tmp_path, monkeypatch)
    import notify
    sent = []
    monkeypatch.setattr(server, "_tg_token", None)
    monkeypatch.setattr(server, "_tg_notified", set())
    monkeypatch.setattr(notify, "send_message", lambda *a, **k: sent.append(1) or True)
    try:
        _ingest(port, master, {"services": [{"name": "ollama", "port": 11434, "up": False}],
                               "host_metrics": {"cpu_pct": 1.0}})
        assert sent == []
    finally:
        httpd.shutdown()
