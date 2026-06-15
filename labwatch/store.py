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
