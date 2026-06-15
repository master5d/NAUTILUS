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
