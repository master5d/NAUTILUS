"""Pure tray-state logic — no GUI, no I/O, fully unit-testable.

status_color maps an /api/state snapshot to an indicator color. Until Phase 2
adds alerts, color is driven by host freshness; the alert branches are already
wired so the same function works unchanged once alerts exist.
"""


def alert_keys(state) -> set:
    """Stable identity set for the current alerts: (id, host) pairs."""
    return {(a.get("id"), a.get("host")) for a in (state.get("alerts") or [])}


def new_alert_keys(prev: set, state) -> set:
    """Alerts present now that were not in prev (→ toast these)."""
    return alert_keys(state) - (prev or set())


def status_color(state) -> str:
    alerts = state.get("alerts") or []
    severities = {a.get("severity") for a in alerts if a.get("state") != "resolved"}
    hosts = state.get("hosts") or {}
    freshness = {h.get("freshness") for h in hosts.values()}
    if "critical" in severities or "down" in freshness:
        return "red"
    if "warning" in severities or "stale" in freshness:
        return "amber"
    if not hosts:
        return "gray"
    return "green"
