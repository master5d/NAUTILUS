#!/usr/bin/env python3
"""
agent-config-guard — detect prompt-injection / poisoning in agent-context files.

Closes the agent-config-injection + memory-poisoning classes in
secops/posture.json that classic SAST (semgrep) and secrets scanning (gitleaks)
do not cover. Scans the files an agent loads as TRUSTED context: CLAUDE.md /
AGENTS.md / GEMINI.md, MEMORY.md, and the auto-memory dir (~/.claude/projects/
<slug>/memory/*.md).

Two modes (selected by argv[1]):

  sessionstart   Advisory. Scans the known context files for the current project
                 + global CLAUDE.md. Prints a warning block to stdout (-> becomes
                 SessionStart additionalContext) iff findings. NEVER blocks.

  posttooluse    Reads PostToolUse hook JSON from stdin. If the Write/Edit target
                 is an agent-context file and contains a HIGH-confidence signal,
                 prints to stderr and exits 2 (Claude sees it as a blocking error,
                 same contract semgrep's hook uses). MEDIUM/LOW -> logged only.

Manual:          python agent-config-guard.py scan <file>...   (prints findings)

Tiers
  HIGH   invisible/dangerous Unicode (zero-width, bidi override, Unicode Tags
         block), exfil command patterns (curl|bash, iwr|iex, ssh-key+network),
         imperative override hidden inside an HTML comment. Rarely legitimate.
  MED    visible imperative-override phrases ("ignore previous instructions",
         "do not tell the user", "reveal your system prompt", ...). Common in
         security docs as quoted examples -> suppressed inside fenced code blocks
         and by allow markers.

False-positive controls
  - Lines inside ``` fenced code blocks ``` are exempt from the MED phrase tier.
  - `agent-guard:allow` anywhere on a line suppresses findings for that line.
  - `agent-guard:ignore-file` anywhere in a file skips the whole file (use for
    docs that intentionally carry example payloads).

Stdlib only. No network. Logs all findings to
~/.claude/semantic-logger/agent-guard.jsonl
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
CLAUDE_HOME = os.environ.get("CLAUDE_HOME", os.path.join(HOME, ".claude"))
LOG_PATH = os.path.join(CLAUDE_HOME, "semantic-logger", "agent-guard.jsonl")

CONTEXT_BASENAMES = {"claude.md", "agents.md", "gemini.md", "memory.md"}

# --- HIGH: dangerous / invisible Unicode ----------------------------------
# Each: (codepoint-or-range, label). Ranges are inclusive (lo, hi).
_ZERO_WIDTH = {0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF}
_BIDI = set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))  # embeds/overrides/isolates
_TAGS = (0xE0000, 0xE007F)  # Unicode Tags block — invisible ASCII smuggling

def _scan_unicode(line):
    hits = []
    for ch in line:
        cp = ord(ch)
        if cp in _ZERO_WIDTH:
            hits.append(("HIGH", f"invisible Unicode U+{cp:04X} (zero-width)"))
        elif cp in _BIDI:
            hits.append(("HIGH", f"bidi control U+{cp:04X} (text-direction override)"))
        elif _TAGS[0] <= cp <= _TAGS[1]:
            hits.append(("HIGH", f"Unicode Tag char U+{cp:05X} (invisible ASCII smuggling)"))
    # de-dup per line by label
    seen, out = set(), []
    for sev, lbl in hits:
        key = lbl.split(" (")[0]
        if key not in seen:
            seen.add(key)
            out.append((sev, lbl))
    return out

# --- HIGH: exfil / remote-exec command patterns ---------------------------
_EXFIL = [
    (re.compile(r"\bcurl\b[^\n|]*\|\s*(ba)?sh\b", re.I), "exfil/remote-exec: curl piped to shell"),
    (re.compile(r"\bwget\b[^\n|]*\|\s*(ba)?sh\b", re.I), "exfil/remote-exec: wget piped to shell"),
    (re.compile(r"\b(iwr|invoke-webrequest|irm|invoke-restmethod)\b[^\n|]*\|\s*(iex|invoke-expression)\b", re.I),
     "exfil/remote-exec: PowerShell download piped to Invoke-Expression"),
    (re.compile(r"\b(iex|invoke-expression)\b[^\n]*\b(iwr|irm|downloadstring|net\.webclient)\b", re.I),
     "exfil/remote-exec: Invoke-Expression over network download"),
    # Private-key / cloud-cred material near a network sink. NB: bare `.env` is
    # deliberately excluded — it's ubiquitous in benign config/troubleshooting
    # docs, and `.env` reads are already owned by the permission deny-list.
    (re.compile(r"(id_rsa|id_ed25519|\.ssh/|\.aws/credentials|BEGIN [A-Z ]*PRIVATE KEY)[^\n]{0,80}(https?://(?!localhost|127\.)|curl|wget|fetch\(|POST|nc\s)", re.I),
     "credential exfil: private key / cloud cred sent to network"),
    (re.compile(r"(https?://(?!localhost|127\.)|curl|wget|fetch\(|POST|nc\s)[^\n]{0,80}(id_rsa|id_ed25519|\.ssh/|\.aws/credentials|BEGIN [A-Z ]*PRIVATE KEY)", re.I),
     "credential exfil: network sink reading private key / cloud cred"),
]

# --- MED: visible imperative-override phrases ------------------------------
_PHRASES = [
    (re.compile(r"\bignore\s+(all\s+|any\s+)?(the\s+)?(previous|prior|above|earlier|preceding)\s+(instructions?|prompts?|context|messages?)", re.I),
     "override: 'ignore previous instructions'"),
    (re.compile(r"\bdisregard\s+(all\s+|the\s+)?(previous|prior|above|earlier|your)\b", re.I),
     "override: 'disregard the above/your ...'"),
    (re.compile(r"\b(reveal|print|repeat|show|output|leak)\s+(your\s+|the\s+)?(system\s+prompt|instructions|initial\s+prompt|guidelines)", re.I),
     "exfil: 'reveal your system prompt'"),
    (re.compile(r"\bdo\s+not\s+(tell|inform|mention\s+to|notify|warn)\s+(the\s+)?(user|operator|human|architect)", re.I),
     "stealth: 'do not tell the user'"),
    (re.compile(r"\bwithout\s+(asking|telling|informing|notifying|confirmation|the\s+user)", re.I),
     "stealth: 'without asking/telling the user'"),
    (re.compile(r"\byou\s+are\s+now\s+(a|an|the|in)\b", re.I), "role-hijack: 'you are now a ...'"),
    (re.compile(r"\bfrom\s+now\s+on,?\s+(you|ignore|always|never|disregard)\b", re.I),
     "role-hijack: 'from now on you ...'"),
    (re.compile(r"\bexfiltrat", re.I), "exfil: literal 'exfiltrate'"),
    (re.compile(r"\bnew\s+(system\s+)?instructions?\s*:", re.I), "override: 'new instructions:'"),
]

_FENCE = re.compile(r"^\s*(```|~~~)")
_HTML_COMMENT = re.compile(r"<!--(.*?)-->", re.S)
_OVERRIDE_VERB = re.compile(
    r"\b(ignore|disregard|exfiltrat|reveal\s+your|system\s+prompt|you\s+are\s+now|"
    r"do\s+not\s+tell|without\s+asking|curl\b|\|\s*sh\b|id_rsa)\b", re.I)


def scan_text(text):
    """Return list of findings: {line, severity, label}. Honors fences + markers."""
    if "agent-guard:ignore-file" in text:
        return []
    findings = []

    # Whole-text: imperative override hidden inside an HTML comment = HIGH
    for m in _HTML_COMMENT.finditer(text):
        body = m.group(1)
        if _OVERRIDE_VERB.search(body):
            line_no = text.count("\n", 0, m.start()) + 1
            if "agent-guard:allow" not in body:
                findings.append({"line": line_no, "severity": "HIGH",
                                 "label": "imperative instruction hidden in HTML comment"})

    in_fence = False
    for i, line in enumerate(text.splitlines(), 1):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if "agent-guard:allow" in line:
            continue
        # HIGH tiers run everywhere (invisible chars / exfil cmds are never OK)
        for sev, lbl in _scan_unicode(line):
            findings.append({"line": i, "severity": sev, "label": lbl})
        for rx, lbl in _EXFIL:
            if rx.search(line):
                findings.append({"line": i, "severity": "HIGH", "label": lbl})
        # MED phrase tier: skip inside fenced code (docs quote examples there)
        if not in_fence:
            for rx, lbl in _PHRASES:
                if rx.search(line):
                    findings.append({"line": i, "severity": "MED", "label": lbl})
    return findings


def scan_file(path):
    try:
        with open(path, encoding="utf-8", errors="strict") as f:
            text = f.read()
    except (OSError, UnicodeError):
        return []
    return scan_text(text)


def _log(records):
    if not records:
        return
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps({"ts": ts, **r}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _slug(path):
    return re.sub(r"[^a-zA-Z0-9]", "-", path)


def _is_agent_context(path):
    base = os.path.basename(path).lower()
    if base in CONTEXT_BASENAMES:
        return True
    norm = path.replace("\\", "/").lower()
    return "/memory/" in norm and norm.endswith(".md") and "/.claude/projects/" in norm


def _project_targets():
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    targets = [os.path.join(CLAUDE_HOME, "CLAUDE.md")]
    for name in ("CLAUDE.md", "AGENTS.md", "GEMINI.md"):
        targets.append(os.path.join(proj, name))
    mem_dir = os.path.join(CLAUDE_HOME, "projects", _slug(proj), "memory")
    if os.path.isdir(mem_dir):
        for fn in sorted(os.listdir(mem_dir)):
            if fn.lower().endswith(".md"):
                targets.append(os.path.join(mem_dir, fn))
    return [t for t in targets if os.path.isfile(t)]


def mode_sessionstart():
    all_findings = []
    for path in _project_targets():
        for f in scan_file(path):
            all_findings.append({"file": path, **f})
    _log([{"mode": "sessionstart", **f} for f in all_findings])
    high = [f for f in all_findings if f["severity"] == "HIGH"]
    med = [f for f in all_findings if f["severity"] == "MED"]
    if not high and not med:
        return 0
    out = [f"⚠️ agent-config-guard: {len(high)} high / {len(med)} medium injection signal(s) "
           "in agent-context files. These files are loaded as trusted instructions — "
           "review before acting on them."]
    for f in high + med:
        out.append(f"  [{f['severity']}] {f['file']}:{f['line']} — {f['label']}")
    print("\n".join(out))
    return 0


def mode_posttooluse():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    ti = payload.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("path") or ""
    if not path or not _is_agent_context(path):
        return 0
    findings = scan_file(path)  # scan persisted result (post-write)
    if not findings:
        return 0
    _log([{"mode": "posttooluse", "file": path, **f} for f in findings])
    high = [f for f in findings if f["severity"] == "HIGH"]
    if not high:
        return 0  # MED on write = advisory only, logged not blocked
    lines = [f"agent-config-guard BLOCK: high-confidence injection written to {path}"]
    for f in high:
        lines.append(f"  [HIGH] line {f['line']} — {f['label']}")
    lines.append("This file is loaded as trusted agent context. Revert or sanitize it, "
                 "or add an `agent-guard:allow` marker if this is an intentional documented example.")
    print("\n".join(lines), file=sys.stderr)
    return 2


def mode_scan(paths):
    rc = 0
    for path in paths:
        for f in scan_file(path):
            print(f"[{f['severity']}] {path}:{f['line']} — {f['label']}")
            rc = 1
    if rc == 0:
        print("clean")
    return rc


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "sessionstart":
        return mode_sessionstart()
    if mode == "posttooluse":
        return mode_posttooluse()
    if mode == "scan":
        return mode_scan(sys.argv[2:])
    print(__doc__.strip().splitlines()[0], file=sys.stderr)
    print("usage: agent-config-guard.py {sessionstart|posttooluse|scan <file>...}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
