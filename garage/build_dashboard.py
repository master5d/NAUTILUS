#!/usr/bin/env python3
"""Garage dashboard generator.

Reads the garage source-of-truth files (fleet.json, workloads.json,
MIGRATION_PLAN.md) and renders a self-contained dark-theme dashboard.html
with the data inlined — so it opens by double-click (file://) with no server
and no fetch/CORS issues. Re-run after editing the JSON to refresh.

    python build_dashboard.py        # -> ./dashboard.html
"""

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FLEET = HERE / "fleet.json"
WORKLOADS = HERE / "workloads.json"
PLAN = HERE / "MIGRATION_PLAN.md"
OUT = HERE / "dashboard.html"

# status token -> (label, css-class)
STATUS_CLASS = {
    "active": "ok",
    "migrated": "ok",
    "onboarded-live": "ok",
    "onboarded": "live",
    "planned": "warn",
    "planned-shopping": "warn",
    "pending-onboarding": "warn",
    "shopping": "info",
    "wishlist": "info",
    "blocked": "bad",
    "sold": "muted",
    "resale": "muted",
}


def status_class(status: str) -> str:
    s = (status or "").lower()
    for key, cls in STATUS_CLASS.items():
        if s.startswith(key):
            return cls
    return "muted"


def esc(x) -> str:
    return html.escape(str(x)) if x is not None else ""


def specs_str(specs: dict) -> str:
    if not specs:
        return ""
    parts = []
    for k, v in specs.items():
        if k == "note":
            continue
        parts.append(f"{esc(v)}")
    return " · ".join(p for p in parts if p)


def phase_progress(plan_text: str):
    """Parse '## Phase N — title <marker>' headers for status markers."""
    rows = []
    for line in plan_text.splitlines():
        m = re.match(r"^##\s+(Phase\s+\d[^\n]*)", line)
        if not m:
            continue
        head = m.group(1).strip()
        if "✅" in head or "DONE" in head.upper():
            state = ("done", "ok")
        elif "🟡" in head or "MOSTLY" in head.upper() or "PROGRESS" in head.upper():
            state = ("in progress", "warn")
        elif "⬜" in head or "NOT STARTED" in head.upper():
            state = ("not started", "muted")
        else:
            state = ("—", "muted")
        # strip emoji/markers from the displayed title
        title = re.sub(r"[✅🟡⬜]", "", head)
        title = re.sub(r"\b(DONE|MOSTLY DONE|NOT STARTED|IN PROGRESS)\b", "", title, flags=re.I)
        title = title.strip(" —")
        rows.append((title, state[0], state[1]))
    return rows


def card(unit: dict) -> str:
    st = unit.get("status", "")
    net = unit.get("net", {}) or {}
    power = unit.get("power", {}) or {}
    ip = net.get("ip")
    always = power.get("always_on")
    badges = [f'<span class="pill {status_class(st)}">{esc(st)}</span>']
    if always is True:
        badges.append('<span class="pill tiny ok">always-on</span>')
    elif always is False:
        badges.append('<span class="pill tiny muted">on-demand</span>')
    cost = unit.get("cost_usd")
    resale = unit.get("resale_usd")
    meta = []
    if ip:
        meta.append(f'<code>{esc(ip)}</code>')
    sp = specs_str(unit.get("specs", {}))
    if sp:
        meta.append(esc(sp))
    if cost:
        meta.append(f"${cost}")
    if resale:
        meta.append(f"resale ${resale}")
    if unit.get("cost_eur_mo"):
        meta.append(f"€{unit['cost_eur_mo']}/mo")
    role = unit.get("role_now") or unit.get("role") or ""
    target = unit.get("role_target")
    blocker = unit.get("blocker")
    body = f'<div class="role">{esc(role)}</div>' if role else ""
    if target:
        body += f'<div class="target"><span class="lbl">target</span> {esc(target)}</div>'
    if blocker:
        body += f'<div class="blocker">⛔ {esc(blocker)}</div>'
    return f"""
      <div class="card">
        <div class="card-head">
          <div class="card-title">{esc(unit.get('label', unit.get('id')))}</div>
          <div class="badges">{''.join(badges)}</div>
        </div>
        <div class="card-meta">{' &middot; '.join(meta)}</div>
        {body}
      </div>"""


def iot_card(unit: dict) -> str:
    st = unit.get("status", "")
    cat = unit.get("category", "")
    badges = [f'<span class="pill {status_class(st)}">{esc(st)}</span>']
    if unit.get("priority"):
        badges.append(f'<span class="pill tiny info">{esc(unit["priority"])}</span>')
    return f"""
      <div class="card">
        <div class="card-head">
          <div class="card-title">{esc(unit.get('label', unit.get('id')))}</div>
          <div class="badges">{''.join(badges)}</div>
        </div>
        <div class="card-meta"><span class="tag">{esc(cat)}</span></div>
        <div class="role">{esc(unit.get('role', ''))}</div>
        {f'<div class="note">{esc(unit.get("note"))}</div>' if unit.get('note') else ''}
      </div>"""


def main():
    fleet = json.loads(FLEET.read_text(encoding="utf-8"))
    workloads = json.loads(WORKLOADS.read_text(encoding="utf-8"))
    plan_text = PLAN.read_text(encoding="utf-8") if PLAN.exists() else ""

    units = fleet.get("units", [])
    iot = fleet.get("iot", [])
    peripherals = fleet.get("peripherals", [])
    wl = workloads.get("workloads", [])

    # rollups
    capex = sum(u.get("cost_usd") or 0 for u in units)
    resale = sum(u.get("resale_usd") or 0 for u in units if "resale" in (u.get("role_target", "").lower()))
    monthly_eur = sum(u.get("cost_eur_mo") or 0 for u in units)
    always_on_units = sum(1 for u in units if (u.get("power") or {}).get("always_on") is True)
    always_on_wl = sum(1 for w in wl if w.get("always_on"))

    # group units by tier
    tier_order = ["workstation", "local_always_on", "cloud"]
    tier_labels = {
        "workstation": "Workstation",
        "local_always_on": "Local always-on",
        "cloud": "Cloud",
    }
    by_tier = {t: [] for t in tier_order}
    for u in units:
        by_tier.setdefault(u.get("tier", "other"), []).append(u)

    fleet_sections = ""
    for t in tier_order:
        us = by_tier.get(t, [])
        if not us:
            continue
        fleet_sections += f'<h3 class="tier">{tier_labels.get(t, t)} <span class="count">{len(us)}</span></h3>'
        fleet_sections += '<div class="grid">' + "".join(card(u) for u in us) + "</div>"

    iot_html = '<div class="grid">' + "".join(iot_card(u) for u in iot) + "</div>"

    periph_html = " ".join(
        f'<span class="periph"><b>{esc(p.get("label"))}</b> — {esc(p.get("role"))}</span>'
        for p in peripherals
    )

    wl_rows = ""
    for w in wl:
        st = w.get("status", "")
        ao = '<span class="pill tiny ok">always-on</span>' if w.get("always_on") else '<span class="pill tiny muted">on-demand</span>'
        wl_rows += f"""
        <tr>
          <td class="svc">{esc(w.get('service'))}</td>
          <td>{ao}</td>
          <td><code>{esc(w.get('host_now'))}</code></td>
          <td><code>{esc(w.get('host_target'))}</code></td>
          <td>{f'<span class="pill {status_class(st)}">{esc(st)}</span>' if st else '<span class="dim">—</span>'}</td>
        </tr>"""

    phases = phase_progress(plan_text)
    phase_rows = "".join(
        f'<div class="phase"><span class="pill {cls}">{esc(state)}</span><span class="ptitle">{esc(title)}</span></div>'
        for title, state, cls in phases
    )

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    variant = fleet.get("variant", "")
    as_of = fleet.get("as_of", "")

    doc = TEMPLATE.format(
        as_of=esc(as_of),
        generated=esc(generated),
        variant=esc(variant),
        n_units=len(units),
        n_iot=len(iot),
        always_on_units=always_on_units,
        always_on_wl=always_on_wl,
        n_wl=len(wl),
        capex=f"{capex:,.0f}",
        resale=f"{resale:,.0f}",
        monthly_eur=f"{monthly_eur:.2f}",
        fleet_sections=fleet_sections,
        iot_html=iot_html,
        periph_html=periph_html,
        wl_rows=wl_rows,
        phase_rows=phase_rows,
    )
    OUT.write_text(doc, encoding="utf-8")
    print(f"wrote {OUT}  ({len(doc):,} bytes)  units={len(units)} iot={len(iot)} workloads={len(wl)} phases={len(phases)}")


TEMPLATE = """<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Garage — NAUTILUS fleet dashboard</title>
<style>
  :root {{
    --bg:#020617; --panel:#0b1220; --panel2:#0f1a2e; --border:#1e293b;
    --text:#e2e8f0; --muted:#94a3b8; --dim:#64748b; --accent:#38bdf8;
    --ok:#22c55e; --warn:#f59e0b; --info:#60a5fa; --bad:#ef4444;
    --live:#2dd4bf; --mutedp:#64748b;
  }}
  [data-theme="light"] {{
    --bg:#f8fafc; --panel:#ffffff; --panel2:#f1f5f9; --border:#e2e8f0;
    --text:#0f172a; --muted:#475569; --dim:#94a3b8;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--text);
    font-family:'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
    line-height:1.5; padding:28px 32px 64px;
  }}
  a {{ color:var(--accent); }}
  header {{ display:flex; align-items:flex-start; justify-content:space-between; gap:20px; flex-wrap:wrap; }}
  h1 {{ font-size:22px; margin:0 0 4px; letter-spacing:.5px; }}
  h1 .wrench {{ color:var(--accent); }}
  .sub {{ color:var(--muted); font-size:13px; }}
  .variant {{ color:var(--dim); font-size:12px; margin-top:6px; max-width:760px; }}
  .toggle {{
    background:var(--panel); border:1px solid var(--border); color:var(--text);
    border-radius:8px; padding:7px 12px; cursor:pointer; font:inherit; font-size:12px;
  }}
  .toggle:hover {{ border-color:var(--accent); }}
  .stats {{ display:flex; gap:14px; flex-wrap:wrap; margin:22px 0 6px; }}
  .stat {{
    background:var(--panel); border:1px solid var(--border); border-radius:12px;
    padding:14px 18px; min-width:130px;
  }}
  .stat .num {{ font-size:26px; font-weight:700; }}
  .stat .lbl {{ color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.6px; margin-top:2px; }}
  h2 {{ font-size:14px; text-transform:uppercase; letter-spacing:1.2px; color:var(--accent);
        margin:36px 0 14px; border-bottom:1px solid var(--border); padding-bottom:8px; }}
  h3.tier {{ font-size:13px; color:var(--muted); margin:20px 0 10px; font-weight:600; }}
  h3.tier .count {{ color:var(--dim); font-weight:400; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(330px,1fr)); gap:14px; }}
  .card {{
    background:var(--panel); border:1px solid var(--border); border-radius:12px;
    padding:14px 16px; display:flex; flex-direction:column; gap:8px;
  }}
  .card:hover {{ border-color:#334155; }}
  .card-head {{ display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }}
  .card-title {{ font-weight:700; font-size:14px; }}
  .badges {{ display:flex; gap:5px; flex-wrap:wrap; justify-content:flex-end; }}
  .card-meta {{ color:var(--muted); font-size:12px; }}
  .card-meta code {{ color:var(--accent); }}
  .role {{ font-size:12.5px; color:var(--text); }}
  .target {{ font-size:12px; color:var(--muted); }}
  .target .lbl {{ color:var(--dim); text-transform:uppercase; font-size:10px; letter-spacing:.5px; }}
  .blocker {{ font-size:12px; color:var(--bad); }}
  .note {{ font-size:11.5px; color:var(--dim); font-style:italic; }}
  .tag {{ background:var(--panel2); border:1px solid var(--border); border-radius:6px;
          padding:2px 8px; font-size:11px; color:var(--muted); }}
  .pill {{ font-size:11px; padding:2px 9px; border-radius:999px; font-weight:600; white-space:nowrap; }}
  .pill.tiny {{ font-size:10px; padding:1px 7px; font-weight:500; }}
  .pill.ok   {{ background:rgba(34,197,94,.15);  color:#4ade80; border:1px solid rgba(34,197,94,.35); }}
  .pill.warn {{ background:rgba(245,158,11,.15); color:#fbbf24; border:1px solid rgba(245,158,11,.35); }}
  .pill.info {{ background:rgba(96,165,250,.15); color:#93c5fd; border:1px solid rgba(96,165,250,.35); }}
  .pill.bad  {{ background:rgba(239,68,68,.15);  color:#f87171; border:1px solid rgba(239,68,68,.35); }}
  .pill.live {{ background:rgba(45,212,191,.15); color:#5eead4; border:1px solid rgba(45,212,191,.35); }}
  .pill.muted{{ background:rgba(100,116,139,.15);color:#cbd5e1; border:1px solid rgba(100,116,139,.35); }}
  table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
  th, td {{ text-align:left; padding:9px 10px; border-bottom:1px solid var(--border); vertical-align:top; }}
  th {{ color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.5px; }}
  td code {{ color:var(--accent); font-size:11.5px; }}
  td.svc {{ font-weight:600; }}
  .dim {{ color:var(--dim); }}
  .phases {{ display:flex; flex-direction:column; gap:8px; }}
  .phase {{ display:flex; align-items:center; gap:12px; background:var(--panel);
            border:1px solid var(--border); border-radius:9px; padding:9px 14px; }}
  .phase .ptitle {{ font-size:13px; }}
  .periphs {{ display:flex; gap:10px; flex-wrap:wrap; }}
  .periph {{ background:var(--panel); border:1px solid var(--border); border-radius:9px;
             padding:8px 12px; font-size:12px; color:var(--muted); }}
  .periph b {{ color:var(--text); }}
  footer {{ margin-top:40px; color:var(--dim); font-size:11px; border-top:1px solid var(--border); padding-top:14px; }}
</style>
</head>
<body>
<header>
  <div>
    <h1><span class="wrench">&#128295;</span> Garage &mdash; NAUTILUS fleet</h1>
    <div class="sub">Hardware CMDB &amp; workload topology &middot; as_of <b>{as_of}</b></div>
    <div class="variant">{variant}</div>
  </div>
  <button class="toggle" onclick="toggleTheme()">&#9788; theme</button>
</header>

<div class="stats">
  <div class="stat"><div class="num">{n_units}</div><div class="lbl">compute units</div></div>
  <div class="stat"><div class="num">{always_on_units}</div><div class="lbl">always-on nodes</div></div>
  <div class="stat"><div class="num">{n_iot}</div><div class="lbl">IoT devices</div></div>
  <div class="stat"><div class="num">{always_on_wl}/{n_wl}</div><div class="lbl">always-on workloads</div></div>
  <div class="stat"><div class="num">${capex}</div><div class="lbl">tracked capex</div></div>
  <div class="stat"><div class="num">${resale}</div><div class="lbl">resale (M2s)</div></div>
  <div class="stat"><div class="num">&euro;{monthly_eur}</div><div class="lbl">cloud /mo</div></div>
</div>

<h2>Compute fleet</h2>
{fleet_sections}

<h2>IoT layer</h2>
{iot_html}

<h2>Workload topology</h2>
<table>
  <thead><tr><th>Service</th><th>Cadence</th><th>Host now</th><th>Host target</th><th>Status</th></tr></thead>
  <tbody>{wl_rows}</tbody>
</table>

<h2>Migration phases</h2>
<div class="phases">{phase_rows}</div>

<h2>Peripherals</h2>
<div class="periphs">{periph_html}</div>

<footer>
  Generated {generated} by <code>build_dashboard.py</code> from fleet.json + workloads.json + MIGRATION_PLAN.md.
  Re-run the generator to refresh. Source of truth = the JSON, not this file.
</footer>

<script>
  function toggleTheme() {{
    const r = document.documentElement;
    r.dataset.theme = r.dataset.theme === 'dark' ? 'light' : 'dark';
    try {{ localStorage.setItem('garage-theme', r.dataset.theme); }} catch (e) {{}}
  }}
  try {{
    const saved = localStorage.getItem('garage-theme');
    if (saved) document.documentElement.dataset.theme = saved;
  }} catch (e) {{}}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
