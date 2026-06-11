#!/usr/bin/env python3
"""
claude-posture-audit — supply-chain attestation + agency/policy lint for the
Claude Code harness. Closes the MCP/plugin-supply-chain and excessive-agency
classes in secops/posture.json that the agent-config-guard hook doesn't.

Two complementary check families, both over the live config:

  ABSOLUTE policy rules — things that are risky regardless of history:
    * defaultMode == bypassPermissions            (max agency)
    * skipDangerousModePermissionPrompt == true
    * permissions.allow entries with dangerous wildcards (Bash(*), Read(**), ...)
    * permissions.deny missing a critical-path entry (.ssh/.env/.aws/keys)

  DRIFT rules — change from the committed approved baseline:
    * plugin added / removed / pin (gitCommitSha|version) changed
    * marketplace added (trust extension)
    * user-scope MCP server added (~/.claude.json)
    * Claude Desktop MCP server added (claude_desktop_config.json)
    * enabledMcpjsonServers added / deniedMcpServers removed
    * hook command added or changed (new auto-exec surface)

Inputs (read-only): ~/.claude/settings.json, ~/.claude/plugins/
installed_plugins.json, ~/.claude.json (mcpServers keys only),
%APPDATA%/Claude/claude_desktop_config.json.

Baseline: secops/baselines/claude-posture-baseline.json  (committed = approved
state). `accepted` array in the baseline suppresses finding ids the user has
deliberately acknowledged (logged, not surfaced) — same idea as posture.json
accepted_risks.

Modes:
  audit       Advisory. Prints a findings block to stdout (SessionStart
              additionalContext) iff findings. Never blocks. Logs all.
  baseline    Snapshot current state -> baseline file (re-approve).
  report      Print findings to stdout always (manual run).

Stdlib only. No network.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
CLAUDE_HOME = os.environ.get("CLAUDE_HOME", os.path.join(HOME, ".claude"))
SETTINGS = os.path.join(CLAUDE_HOME, "settings.json")
INSTALLED = os.path.join(CLAUDE_HOME, "plugins", "installed_plugins.json")
CLAUDE_JSON = os.path.join(HOME, ".claude.json")
DESKTOP_CFG = os.path.join(os.environ.get("APPDATA", os.path.join(HOME, "AppData", "Roaming")),
                           "Claude", "claude_desktop_config.json")
HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(os.path.dirname(HERE), "baselines", "claude-posture-baseline.json")
LOG_PATH = os.path.join(CLAUDE_HOME, "semantic-logger", "agent-guard.jsonl")

CRITICAL_DENY = [".ssh", ".aws", ".env", ".pem", ".key", "id_rsa", "id_ed25519"]
DANGEROUS_ALLOW = [
    re.compile(r"^Bash\(\*?\)$", re.I),
    re.compile(r"^Bash\(:?\*\)$", re.I),
    re.compile(r"^Bash\(\*\*\)$", re.I),
    re.compile(r"^Read\(\*\*?\)$", re.I),
    re.compile(r"^Write\(\*\*?\)$", re.I),
    re.compile(r"^Edit\(\*\*?\)$", re.I),
    re.compile(r"^WebFetch\(\*\)$", re.I),
]


def _read_json(path, fallback=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return fallback if fallback is not None else {}


def _hook_commands(settings):
    """Flatten every hook command string across all events into a sorted set."""
    cmds = set()
    for event, blocks in (settings.get("hooks") or {}).items():
        for block in blocks or []:
            for h in block.get("hooks") or []:
                c = h.get("command")
                if c:
                    cmds.add(c.strip())
    return sorted(cmds)


def collect_state():
    settings = _read_json(SETTINGS)
    perms = settings.get("permissions") or {}
    installed = _read_json(INSTALLED)
    plugins = {}
    for name, entries in (installed.get("plugins") or {}).items():
        if entries:
            e = entries[0]
            plugins[name] = e.get("gitCommitSha") or e.get("version") or "unknown"
    cj = _read_json(CLAUDE_JSON)
    user_mcp = sorted((cj.get("mcpServers") or {}).keys())
    desktop = _read_json(DESKTOP_CFG)
    desktop_mcp = sorted((desktop.get("mcpServers") or {}).keys())
    return {
        "default_mode": perms.get("defaultMode"),
        "skip_dangerous": bool(settings.get("skipDangerousModePermissionPrompt")),
        "allow": list(perms.get("allow") or []),
        "deny": list(perms.get("deny") or []),
        "enabled_plugins": sorted((settings.get("enabledPlugins") or {}).keys()),
        "plugins": plugins,
        "marketplaces": sorted((settings.get("extraKnownMarketplaces") or {}).keys()),
        "mcp_servers_user": user_mcp,
        "mcp_servers_desktop": desktop_mcp,
        "mcp_enabled_jsonservers": sorted(settings.get("enabledMcpjsonServers") or []),
        "mcp_denied": sorted(d.get("serverName") for d in (settings.get("deniedMcpServers") or [])
                             if d.get("serverName")),
        "hooks": _hook_commands(settings),
    }


def absolute_findings(state):
    f = []
    if state["default_mode"] == "bypassPermissions":
        f.append(("HIGH", "agency:bypass-permissions",
                  "permissions.defaultMode = bypassPermissions — agent acts with no per-action gate"))
    if state["skip_dangerous"]:
        f.append(("MED", "agency:skip-dangerous-prompt",
                  "skipDangerousModePermissionPrompt = true — dangerous-mode confirmation suppressed"))
    for a in state["allow"]:
        for rx in DANGEROUS_ALLOW:
            if rx.match(a.strip()):
                f.append(("HIGH", f"agency:dangerous-allow:{a}",
                          f"permissions.allow has broad grant: {a}"))
                break
    deny_blob = " ".join(state["deny"]).lower()
    for crit in CRITICAL_DENY:
        if crit.lower() not in deny_blob:
            f.append(("HIGH", f"agency:deny-gap:{crit}",
                      f"permissions.deny has no rule covering '{crit}' — secret-file read not blocked"))
    return f


def drift_findings(state, base):
    f = []
    if not base:
        return [("MED", "supply:no-baseline",
                 "no approved baseline — run `claude-posture-audit.py baseline` to establish one")]
    # plugins
    bp, sp = base.get("plugins") or {}, state["plugins"]
    for name in sorted(set(sp) - set(bp)):
        f.append(("HIGH", f"supply:plugin-added:{name}", f"new plugin not in baseline: {name}"))
    for name in sorted(set(bp) - set(sp)):
        f.append(("INFO", f"supply:plugin-removed:{name}", f"plugin removed since baseline: {name}"))
    for name in sorted(set(bp) & set(sp)):
        if bp[name] != sp[name]:
            f.append(("MED", f"supply:plugin-changed:{name}",
                      f"plugin pin changed {bp[name][:12]}->{sp[name][:12]}: {name}"))
    # marketplaces / mcp / hooks: set-based
    def set_drift(key, sev_add, label_add, sev_rm=None, label_rm=None):
        b, s = set(base.get(key) or []), set(state[key])
        for x in sorted(s - b):
            f.append((sev_add, f"{key}:added:{x}", f"{label_add}: {x}"))
        if sev_rm:
            for x in sorted(b - s):
                f.append((sev_rm, f"{key}:removed:{x}", f"{label_rm}: {x}"))
    set_drift("marketplaces", "HIGH", "new plugin marketplace (trust extension)")
    set_drift("mcp_servers_user", "HIGH", "new user-scope MCP server")
    set_drift("mcp_servers_desktop", "MED", "new Claude Desktop MCP server")
    set_drift("mcp_enabled_jsonservers", "MED", "newly enabled .mcp.json server")
    set_drift("mcp_denied", None, None, "MED", "MCP server removed from deny list")
    set_drift("hooks", "HIGH", "new auto-exec hook command", "INFO", "hook command removed")
    return f


def audit(state, base):
    accepted = set((base or {}).get("accepted") or [])
    raw = absolute_findings(state) + drift_findings(state, base)
    findings = [{"severity": s, "id": i, "msg": m} for (s, i, m) in raw]
    surfaced = [f for f in findings if f["id"] not in accepted]
    return findings, surfaced


def _log(records, mode):
    if not records:
        return
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps({"ts": ts, "scanner": "posture-audit", "mode": mode, **r},
                                    ensure_ascii=False) + "\n")
    except OSError:
        pass


_SEV_ORDER = {"HIGH": 0, "MED": 1, "INFO": 2}


def _fmt(findings):
    return "\n".join(f"  [{f['severity']}] {f['msg']}"
                     for f in sorted(findings, key=lambda x: _SEV_ORDER.get(x["severity"], 9)))


def mode_baseline(state):
    os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
    prior = _read_json(BASELINE)
    snap = {"as_of": datetime.now(timezone.utc).date().isoformat(),
            "accepted": prior.get("accepted") or [],
            **{k: state[k] for k in
               ("marketplaces", "mcp_servers_user", "mcp_servers_desktop",
                "mcp_enabled_jsonservers", "mcp_denied", "hooks", "plugins")}}
    with open(BASELINE, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)
    print(f"baseline written: {BASELINE} ({len(snap['plugins'])} plugins, "
          f"{len(snap['hooks'])} hooks, accepted={len(snap['accepted'])})")
    return 0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "audit"
    state = collect_state()
    if mode == "baseline":
        return mode_baseline(state)
    base = _read_json(BASELINE)
    findings, surfaced = audit(state, base)
    _log(findings, mode)
    if mode == "report":
        print(_fmt(findings) if findings else "clean")
        return 1 if findings else 0
    # audit (SessionStart advisory)
    if not surfaced:
        return 0
    high = sum(1 for f in surfaced if f["severity"] == "HIGH")
    med = sum(1 for f in surfaced if f["severity"] == "MED")
    print(f"⚠️ claude-posture-audit: {high} high / {med} med posture finding(s) "
          "(supply-chain + agency). Review before trusting this session's autonomy:")
    print(_fmt(surfaced))
    print("  Acknowledge a deliberate choice by adding its id to `accepted` in "
          "secops/baselines/claude-posture-baseline.json; re-approve drift with "
          "`claude-posture-audit.py baseline`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
