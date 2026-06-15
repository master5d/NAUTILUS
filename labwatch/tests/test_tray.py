import json


def test_make_image_is_64px():
    import tray
    img = tray.make_image("green")
    assert img.size == (64, 64)


def test_fetch_state_parses_json(monkeypatch):
    import tray

    class FakeResp:
        def __init__(self, data):
            self._d = data
        def read(self):
            return self._d
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    payload = json.dumps({"hosts": {}, "alerts": []}).encode()
    monkeypatch.setattr(tray.urllib.request, "urlopen",
                        lambda *a, **k: FakeResp(payload))
    assert tray.fetch_state() == {"hosts": {}, "alerts": []}
