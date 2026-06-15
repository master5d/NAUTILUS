import watchers

RULES = {
    "service-down":   {"enabled": True, "severity": "critical", "channels": ["tray", "telegram"]},
    "host-silent":    {"enabled": True, "severity": "critical", "channels": ["tray", "telegram"]},
    "disk-pressure":  {"enabled": True, "severity": "warning", "threshold": 90, "channels": ["tray"]},
    "ram-pressure":   {"enabled": True, "severity": "warning", "threshold": 90, "channels": ["tray"]},
    "secops-pending": {"enabled": True, "severity": "warning", "channels": ["tray"]},
    "egress-anomaly": {"enabled": True, "severity": "critical", "threshold": 0, "channels": ["tray", "telegram"]},
}


def _state(host="m4", freshness="live", services=None, hm=None, domain=None):
    return {"hosts": {host: {"freshness": freshness, "payload": {
        "services": services or [], "host_metrics": hm or {}, "domain": domain or {}}}}}


def test_service_down_fires_per_service():
    st = _state(services=[{"name": "litellm", "up": True}, {"name": "stt", "up": False}])
    fired = watchers.evaluate(st, RULES)
    ids = {a["id"] for a in fired}
    assert ids == {"service-down:stt"}
    assert fired[0]["host"] == "m4" and fired[0]["severity"] == "critical"


def test_host_silent_fires_on_down_freshness():
    fired = watchers.evaluate(_state(freshness="down"), RULES)
    assert any(a["id"] == "host-silent" for a in fired)


def test_host_silent_not_fired_when_live():
    assert not any(a["id"] == "host-silent" for a in watchers.evaluate(_state(freshness="live"), RULES))


def test_disk_pressure_threshold():
    assert any(a["id"] == "disk-pressure" for a in watchers.evaluate(_state(hm={"disk_pct": 95.0}), RULES))
    assert not any(a["id"] == "disk-pressure" for a in watchers.evaluate(_state(hm={"disk_pct": 80.0}), RULES))


def test_ram_pressure_uses_ratio():
    st = _state(hm={"ram_used_gb": 15.2, "ram_total_gb": 16.0})  # 95%
    assert any(a["id"] == "ram-pressure" for a in watchers.evaluate(st, RULES))
    st2 = _state(hm={"ram_used_gb": 8.0, "ram_total_gb": 16.0})  # 50%
    assert not any(a["id"] == "ram-pressure" for a in watchers.evaluate(st2, RULES))


def test_secops_pending_fires():
    st = _state(domain={"secops": {"rotations_pending": [{"x": 1}, {"y": 2}]}})
    fired = [a for a in watchers.evaluate(st, RULES) if a["id"] == "secops-pending"]
    assert fired and "2" in fired[0]["message"]


def test_egress_anomaly_fires_on_novel():
    st = _state(domain={"secops": {"egress": {"novel_today": 3}}})
    assert any(a["id"] == "egress-anomaly" for a in watchers.evaluate(st, RULES))


def test_disabled_rule_does_not_fire():
    rules = dict(RULES, **{"disk-pressure": {"enabled": False, "severity": "warning", "threshold": 90}})
    assert not any(a["id"] == "disk-pressure" for a in watchers.evaluate(_state(hm={"disk_pct": 99.0}), rules))
