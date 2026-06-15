import json

import keys
import reporter
import schema


def test_host_metrics_shape():
    m = reporter.host_metrics()
    for k in ("cpu_pct", "ram_used_gb", "ram_total_gb", "disk_pct", "temp_c", "power_w"):
        assert k in m


def test_probe_down_service_is_false(monkeypatch):
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


def test_load_master_reads_active_key(tmp_path):
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
