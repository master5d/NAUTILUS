"""sqlite persistence for observability snapshots (+ history/alerts tables).

Phase 0 uses `snapshots` (latest per host). `history` and `alerts` tables are
created now but written/used in later phases. Thin by design — not a TSDB.
"""

import json
import sqlite3
from datetime import datetime, timezone

# Freshness thresholds (seconds). stale = 3x report interval; down = 10x.
STALE_FACTOR = 3
DOWN_FACTOR = 10


def connect(path: str, check_same_thread: bool = True) -> sqlite3.Connection:
    # The collector runs under ThreadingHTTPServer (a thread per request), so the
    # server opens this with check_same_thread=False and serializes all access
    # with a single lock. Tests use the default (single-threaded).
    conn = sqlite3.connect(path, timeout=5, check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS snapshots (
            host        TEXT PRIMARY KEY,
            ts          TEXT NOT NULL,
            received    TEXT NOT NULL,
            payload     TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS history (
            host TEXT, ts TEXT, metric TEXT, value REAL
        );
        CREATE INDEX IF NOT EXISTS idx_history_host_metric ON history(host, metric, ts);
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT, host TEXT, severity TEXT, state TEXT,
            first_seen TEXT, last_seen TEXT, resolved_at TEXT,
            PRIMARY KEY (id, host)
        );
        """
    )
    conn.commit()


def upsert_snapshot(conn, host: str, ts: str, payload: dict):
    received = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO snapshots (host, ts, received, payload) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(host) DO UPDATE SET ts=excluded.ts, received=excluded.received, "
        "payload=excluded.payload",
        (host, ts, received, json.dumps(payload, ensure_ascii=False)),
    )
    conn.commit()


def freshness(age_s: float, interval: int = 30) -> str:
    if age_s <= interval * STALE_FACTOR:
        return "live"
    if age_s <= interval * DOWN_FACTOR:
        return "stale"
    return "down"


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def get_snapshots(conn, now_dt: datetime = None, interval: int = 30) -> dict:
    now_dt = now_dt or datetime.now(timezone.utc)
    out = {}
    for row in conn.execute("SELECT host, ts, received, payload FROM snapshots"):
        try:
            age = (now_dt - _parse(row["ts"])).total_seconds()
        except Exception:
            age = float("inf")
        out[row["host"]] = {
            "ts": row["ts"],
            "received": row["received"],
            "age_s": age,
            "freshness": freshness(age, interval),
            "payload": json.loads(row["payload"]),
        }
    return out


def reconcile_alerts(conn, fired: list, now_dt: datetime = None):
    """Upsert currently-fired alerts as 'firing'; mark previously-firing alerts
    that are no longer fired as 'resolved'. Alert identity is (id, host)."""
    now = (now_dt or datetime.now(timezone.utc)).isoformat()
    fired_keys = {(a["id"], a["host"]) for a in fired}
    for a in fired:
        conn.execute(
            "INSERT INTO alerts (id, host, severity, state, first_seen, last_seen, resolved_at) "
            "VALUES (?, ?, ?, 'firing', ?, ?, NULL) "
            "ON CONFLICT(id, host) DO UPDATE SET state='firing', severity=excluded.severity, "
            "last_seen=excluded.last_seen, resolved_at=NULL",
            (a["id"], a["host"], a.get("severity", "warning"), now, now),
        )
    for row in conn.execute("SELECT id, host FROM alerts WHERE state='firing'").fetchall():
        if (row["id"], row["host"]) not in fired_keys:
            conn.execute(
                "UPDATE alerts SET state='resolved', resolved_at=? WHERE id=? AND host=?",
                (now, row["id"], row["host"]),
            )
    conn.commit()


def get_active_alerts(conn, now_dt: datetime = None, linger_min: int = 30) -> list:
    """Firing alerts + recently-resolved ones (within linger_min) so the UI can
    show what just cleared. Each item is a plain dict of the alert row."""
    now_dt = now_dt or datetime.now(timezone.utc)
    out = []
    for r in conn.execute(
        "SELECT id, host, severity, state, first_seen, last_seen, resolved_at FROM alerts"
    ):
        if r["state"] == "firing":
            out.append(dict(r))
        elif r["resolved_at"]:
            try:
                if (now_dt - _parse(r["resolved_at"])).total_seconds() <= linger_min * 60:
                    out.append(dict(r))
            except Exception:
                pass
    return out
