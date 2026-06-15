"""NAUTILUS tray (Surface): persistent tunnel + fleet indicator + toasts.

Thin GUI shell over tray_logic (pure) and tunnel (shared). pystray and
windows_toasts are imported lazily so module import stays testable.
"""

import json
import threading
import time
import urllib.request
import webbrowser

from PIL import Image, ImageDraw

import tray_logic
import tunnel

API_URL = "http://127.0.0.1:4002/api/state"
DASH_URL = "http://localhost:4002"
POLL_S = 10

_RGB = {
    "green": (34, 197, 94),
    "amber": (251, 191, 36),
    "red": (239, 68, 68),
    "gray": (120, 120, 120),
}


def make_image(color: str) -> Image.Image:
    img = Image.new("RGB", (64, 64), (15, 23, 42))
    d = ImageDraw.Draw(img)
    d.ellipse((10, 10, 54, 54), fill=_RGB.get(color, _RGB["gray"]))
    return img


def fetch_state(url: str = API_URL, timeout: float = 3.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


class Tray:
    def __init__(self):
        import pystray
        self._prev_alerts = set()
        self._toaster = None
        self.icon = pystray.Icon(
            "nautilus", make_image("gray"), "NAUTILUS Mesh",
            menu=pystray.Menu(
                pystray.MenuItem("Open Dashboard", self._open, default=True),
                pystray.MenuItem("Restart Tunnel", self._restart),
                pystray.MenuItem("Quit", self._quit),
            ),
        )

    def _open(self, *_a):
        webbrowser.open(DASH_URL)

    def _restart(self, *_a):
        tunnel.stop()
        tunnel.ensure(4002, "m4", 4002)

    def _quit(self, *_a):
        tunnel.stop()
        self.icon.stop()

    def _toast(self, msg: str):
        try:
            from windows_toasts import Toast, WindowsToaster
            if self._toaster is None:
                self._toaster = WindowsToaster("NAUTILUS Mesh")
            t = Toast()
            t.text_fields = ["NAUTILUS Alert", msg]
            self._toaster.show_toast(t)
        except Exception:
            pass  # toasts are best-effort; never break the loop

    def _loop(self):
        while True:
            try:
                tunnel.ensure(4002, "m4", 4002)
                state = fetch_state()
                self.icon.icon = make_image(tray_logic.status_color(state))
                for (aid, host) in tray_logic.new_alert_keys(self._prev_alerts, state):
                    self._toast(f"{host}: {aid}")
                self._prev_alerts = tray_logic.alert_keys(state)
            except Exception:
                self.icon.icon = make_image("gray")
            time.sleep(POLL_S)

    def run(self):
        threading.Thread(target=self._loop, daemon=True).start()
        self.icon.run()


def main():
    Tray().run()


if __name__ == "__main__":
    main()
