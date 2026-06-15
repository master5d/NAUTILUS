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


def test_reconcile_fires_then_resolves_then_lingers():
    conn = store.connect(":memory:")
    store.init_db(conn)
    now = datetime.now(timezone.utc)

    store.reconcile_alerts(conn, [{"id": "service-down:stt", "host": "m4", "severity": "critical"}], now_dt=now)
    active = store.get_active_alerts(conn, now_dt=now)
    assert len(active) == 1 and active[0]["state"] == "firing"
    first_seen = active[0]["first_seen"]

    later = now + timedelta(seconds=30)
    store.reconcile_alerts(conn, [{"id": "service-down:stt", "host": "m4", "severity": "critical"}], now_dt=later)
    active = store.get_active_alerts(conn, now_dt=later)
    assert active[0]["first_seen"] == first_seen
    assert active[0]["last_seen"] != first_seen

    later2 = later + timedelta(seconds=30)
    store.reconcile_alerts(conn, [], now_dt=later2)
    active = store.get_active_alerts(conn, now_dt=later2)
    assert len(active) == 1 and active[0]["state"] == "resolved"

    way_later = later2 + timedelta(minutes=31)
    assert store.get_active_alerts(conn, now_dt=way_later) == []


def test_resolved_then_refires_clears_resolved_at():
    conn = store.connect(":memory:")
    store.init_db(conn)
    now = datetime.now(timezone.utc)
    a = {"id": "host-silent", "host": "surface", "severity": "critical"}
    store.reconcile_alerts(conn, [a], now_dt=now)
    store.reconcile_alerts(conn, [], now_dt=now + timedelta(seconds=10))
    store.reconcile_alerts(conn, [a], now_dt=now + timedelta(seconds=20))
    active = store.get_active_alerts(conn, now_dt=now + timedelta(seconds=20))
    assert len(active) == 1 and active[0]["state"] == "firing"
    assert active[0]["resolved_at"] is None
