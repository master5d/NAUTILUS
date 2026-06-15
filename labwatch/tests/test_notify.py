import json

import notify


def test_load_config_reads_token_and_chat(tmp_path):
    p = tmp_path / "telegram.env"
    p.write_text("# comment\nTELEGRAM_BOT_TOKEN=abc123\nTELEGRAM_CHAT_ID=42\n", encoding="utf-8")
    assert notify.load_config(str(p)) == ("abc123", "42")


def test_load_config_missing_file():
    assert notify.load_config("/no/such/telegram.env") == (None, None)


def test_load_config_incomplete_returns_none(tmp_path):
    p = tmp_path / "t.env"
    p.write_text("TELEGRAM_BOT_TOKEN=x\n", encoding="utf-8")
    assert notify.load_config(str(p)) == (None, None)


def test_critical_telegram_filters_severity_and_channel():
    fired = [
        {"id": "service-down:stt", "host": "m4", "severity": "critical", "channels": ["tray", "telegram"]},
        {"id": "disk-pressure", "host": "m4", "severity": "warning", "channels": ["tray"]},
        {"id": "x", "host": "m4", "severity": "critical", "channels": ["tray"]},
    ]
    assert set(notify.critical_telegram(fired)) == {("service-down:stt", "m4")}


def test_send_message_posts_to_bot_api(monkeypatch):
    captured = {}

    class FakeResp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(req, timeout=5.0):
        captured["url"] = req.full_url
        captured["data"] = req.data
        return FakeResp()

    monkeypatch.setattr(notify.urllib.request, "urlopen", fake_urlopen)
    assert notify.send_message("TOK", "42", "hi") is True
    assert "botTOK/sendMessage" in captured["url"]
    assert json.loads(captured["data"])["chat_id"] == "42"
    assert json.loads(captured["data"])["text"] == "hi"


def test_send_message_no_token_is_false():
    assert notify.send_message(None, "42", "hi") is False


def test_format_fire_and_clear():
    msg = notify.format_fire({"severity": "critical", "id": "a", "message": "stt down on m4"})
    assert msg.startswith("🚨") and "stt down on m4" in msg
    clr = notify.format_clear(("service-down:stt", "m4"))
    assert clr.startswith("✅") and "service-down:stt" in clr
