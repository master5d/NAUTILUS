"""Telegram escape for critical alerts — stdlib only (urllib), no requests.

Sends to the Telegram Bot API. Config (bot token, chat id) lives in the unified
secret store at ~/.config/nautilus/secrets/telegram.env and is user-provided;
this module only reads it and never logs the value.
"""

import json
import os
import urllib.request

DEFAULT_CONFIG = os.path.join(
    os.path.expanduser("~"), ".config", "nautilus", "secrets", "telegram.env"
)


def load_config(path: str = DEFAULT_CONFIG):
    """Return (token, chat_id), or (None, None) if absent/incomplete."""
    token = chat = None
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k == "TELEGRAM_BOT_TOKEN":
                    token = v
                elif k == "TELEGRAM_CHAT_ID":
                    chat = v
    except OSError:
        return None, None
    return (token, chat) if (token and chat) else (None, None)


def send_message(token: str, chat_id: str, text: str, timeout: float = 5.0) -> bool:
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


def critical_telegram(fired: list) -> dict:
    """{(id, host): alert} for fired alerts that are critical AND telegram-channeled."""
    out = {}
    for a in fired:
        if a.get("severity") == "critical" and "telegram" in (a.get("channels") or []):
            out[(a["id"], a["host"])] = a
    return out


def format_fire(alert: dict) -> str:
    return f"🚨 {alert.get('severity', '').upper()}: {alert.get('message') or alert.get('id')}"


def format_clear(key) -> str:
    aid, host = key
    return f"✅ RESOLVED: {aid} on {host}"
