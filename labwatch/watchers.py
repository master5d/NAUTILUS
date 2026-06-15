"""Pure watchers rules engine — maps an /api/state snapshot to fired alerts.

NO eval(): each rule type is a named evaluator. Rules come from watchers.json,
keyed by type with {enabled, severity, threshold, channels}. Alert identity is
(id, host); per-target rules encode the target in id ("service-down:litellm").
"""


def _alert(aid, host, rule, message):
    return {
        "id": aid,
        "host": host,
        "severity": rule.get("severity", "warning"),
        "message": message,
        "channels": rule.get("channels", ["tray"]),
    }


def evaluate(state, rules) -> list:
    fired = []
    for host, h in (state.get("hosts") or {}).items():
        payload = h.get("payload") or {}
        hm = payload.get("host_metrics") or {}
        secops = (payload.get("domain") or {}).get("secops") or {}

        r = rules.get("host-silent") or {}
        if r.get("enabled") and h.get("freshness") == "down":
            fired.append(_alert("host-silent", host, r, f"{host} silent — no snapshot"))

        r = rules.get("service-down") or {}
        if r.get("enabled"):
            for s in payload.get("services") or []:
                if s.get("up") is False:
                    name = s.get("name", "?")
                    fired.append(_alert(f"service-down:{name}", host, r, f"{name} down on {host}"))

        r = rules.get("disk-pressure") or {}
        disk = hm.get("disk_pct")
        if r.get("enabled") and isinstance(disk, (int, float)) and disk > r.get("threshold", 90):
            fired.append(_alert("disk-pressure", host, r, f"disk {disk:.0f}% on {host}"))

        r = rules.get("ram-pressure") or {}
        used, total = hm.get("ram_used_gb"), hm.get("ram_total_gb")
        if (r.get("enabled") and isinstance(used, (int, float))
                and isinstance(total, (int, float)) and total > 0):
            pct = used / total * 100
            if pct > r.get("threshold", 90):
                fired.append(_alert("ram-pressure", host, r, f"ram {pct:.0f}% on {host}"))

        r = rules.get("secops-pending") or {}
        pend = secops.get("rotations_pending")
        if r.get("enabled") and isinstance(pend, list) and len(pend) > 0:
            fired.append(_alert("secops-pending", host, r, f"{len(pend)} secret rotation(s) pending"))

        r = rules.get("egress-anomaly") or {}
        nov = (secops.get("egress") or {}).get("novel_today")
        if r.get("enabled") and isinstance(nov, int) and nov > r.get("threshold", 0):
            fired.append(_alert("egress-anomaly", host, r, f"{nov} novel egress domain(s) today"))
    return fired
