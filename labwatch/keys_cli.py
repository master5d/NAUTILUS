"""nautilus-keys — manage the unified NAUTILUS key store.

Subcommands: gen | list | rotate | revoke.
Never prints raw key material; prints key IDs and SHA-256 fingerprints only
(silent-capture standing principle).

Usage:
    python -m keys_cli gen --host m4
    python keys_cli.py list
"""

import argparse
import base64
import hashlib
import json
import os
import secrets
from datetime import datetime, timezone

import keys as keymod


def _now():
    return datetime.now(timezone.utc).isoformat()


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _fingerprint(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()[:8]


def _load(path: str) -> dict:
    return keymod.load_keyring(path)


def _save(path: str, kr: dict):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(kr, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _next_id(kr: dict, host: str) -> str:
    existing = ((kr.get("hosts") or {}).get(host) or {}).get("keys") or {}
    n = 1 + len(existing)
    return f"{host}-{n}"


def _add_key(kr: dict, host: str) -> str:
    kr.setdefault("hosts", {}).setdefault(host, {"active": "", "keys": {}})
    kid = _next_id(kr, host)
    raw = secrets.token_bytes(32)
    kr["hosts"][host]["keys"][kid] = {
        "material": _b64(raw), "created": _now(), "revoked": False,
    }
    kr["hosts"][host]["active"] = kid
    return kid


def cmd_gen(args):
    kr = _load(args.keyring)
    kid = _add_key(kr, args.host)
    _save(args.keyring, kr)
    raw = keymod.material(kr, args.host, kid)
    print(f"generated {kid} fp={_fingerprint(raw)} (active)")
    return 0


def cmd_rotate(args):
    kr = _load(args.keyring)
    if args.host not in (kr.get("hosts") or {}):
        print(f"unknown host: {args.host}")
        return 1
    kid = _add_key(kr, args.host)
    _save(args.keyring, kr)
    raw = keymod.material(kr, args.host, kid)
    print(f"rotated -> {kid} fp={_fingerprint(raw)} (active; prior keys retained for overlap)")
    return 0


def cmd_revoke(args):
    kr = _load(args.keyring)
    keys_map = (((kr.get("hosts") or {}).get(args.host) or {}).get("keys") or {})
    if args.key_id not in keys_map:
        print(f"unknown key: {args.key_id}")
        return 1
    keys_map[args.key_id]["revoked"] = True
    keys_map[args.key_id]["rotated"] = _now()
    _save(args.keyring, kr)
    print(f"revoked {args.key_id}")
    return 0


def cmd_list(args):
    kr = _load(args.keyring)
    for host, h in (kr.get("hosts") or {}).items():
        for kid, e in (h.get("keys") or {}).items():
            flag = "active" if kid == h.get("active") else ("revoked" if e.get("revoked") else "ok")
            print(f"{host} {kid} {flag} created={e.get('created')}")
    return 0


def cmd_export_host(args):
    kr = _load(args.keyring)
    h = (kr.get("hosts") or {}).get(args.host)
    if not h:
        print(f"unknown host: {args.host}")
        return 1
    _save(args.out, {"hosts": {args.host: h}})
    for kid in (h.get("keys") or {}):
        print(f"exported {args.host} {kid} -> {args.out} (transfer securely, then delete)")
    return 0


def cmd_import_host(args):
    incoming = _load(args.infile)
    hosts = incoming.get("hosts") or {}
    if not hosts:
        print("no hosts in import file")
        return 1
    kr = _load(args.keyring)
    kr.setdefault("hosts", {})
    for host, h in hosts.items():
        kr["hosts"][host] = h
    _save(args.keyring, kr)
    print(f"imported hosts: {list(hosts)}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="nautilus-keys")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen"); g.add_argument("--host", required=True); g.add_argument("--keyring", default=keymod.KEYRING_PATH); g.set_defaults(fn=cmd_gen)
    r = sub.add_parser("rotate"); r.add_argument("--host", required=True); r.add_argument("--keyring", default=keymod.KEYRING_PATH); r.set_defaults(fn=cmd_rotate)
    v = sub.add_parser("revoke"); v.add_argument("--host", required=True); v.add_argument("--key-id", required=True); v.add_argument("--keyring", default=keymod.KEYRING_PATH); v.set_defaults(fn=cmd_revoke)
    e = sub.add_parser("export-host"); e.add_argument("--host", required=True); e.add_argument("--out", required=True); e.add_argument("--keyring", default=keymod.KEYRING_PATH); e.set_defaults(fn=cmd_export_host)
    i = sub.add_parser("import-host"); i.add_argument("--in", dest="infile", required=True); i.add_argument("--keyring", default=keymod.KEYRING_PATH); i.set_defaults(fn=cmd_import_host)
    l = sub.add_parser("list"); l.add_argument("--keyring", default=keymod.KEYRING_PATH); l.set_defaults(fn=cmd_list)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
