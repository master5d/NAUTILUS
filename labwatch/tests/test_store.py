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
