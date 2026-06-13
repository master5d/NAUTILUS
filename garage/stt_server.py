"""
SOVERN Garage — Parakeet STT service (M4 always-on node).
Stdlib HTTP + parakeet-mlx (Apple Silicon/Metal). Loads the model once,
transcribes posted audio. Echo (and anything on the LAN) calls it instead
of transcribing on the laptop.

Run (via .venv-stt that has parakeet-mlx):
    ~/nautilus/.venv-stt/bin/python ~/nautilus/garage/stt_server.py
POST /transcribe  (raw audio bytes in body; any ffmpeg-readable format)
    → {"text": "...", "ms": 123}
GET  /health → {"ok": true, "model": "..."}
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODEL_ID = os.environ.get("PARAKEET_MODEL", "mlx-community/parakeet-tdt-0.6b-v3")
PORT = int(os.environ.get("STT_PORT", "4100"))
FFMPEG = os.environ.get("FFMPEG", "/opt/homebrew/bin/ffmpeg")
MAX_BYTES = 100 * 1024 * 1024  # 100 MB cap

print(f"[stt] loading {MODEL_ID} …", flush=True)
from parakeet_mlx import from_pretrained  # noqa: E402

_model = from_pretrained(MODEL_ID)
print(f"[stt] model ready on :{PORT}", flush=True)


def _transcribe_bytes(raw: bytes) -> str:
    """Normalize arbitrary audio bytes → 16 kHz mono wav via ffmpeg, transcribe.

    All paths are fixed names inside a private TemporaryDirectory — never
    derived from request data, so there is no path-traversal surface.
    """
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "in")
        wav = os.path.join(d, "out.wav")
        with open(src, "wb") as f:
            f.write(raw)
        subprocess.run(
            [FFMPEG, "-y", "-i", src, "-ar", "16000", "-ac", "1", wav],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        result = _model.transcribe(wav)
        return getattr(result, "text", str(result))


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True, "model": MODEL_ID})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/transcribe":
            self._send(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > MAX_BYTES:
            self._send(413, {"error": "missing or oversized body"})
            return
        raw = self.rfile.read(length)
        try:
            t0 = time.time()
            text = _transcribe_bytes(raw)
            self._send(200, {"text": text, "ms": int((time.time() - t0) * 1000)})
        except Exception as e:
            self._send(500, {"error": str(e)})

    def log_message(self, *a):  # quiet
        pass


if __name__ == "__main__":
    # Bind LAN so Echo on the Surface can reach it; home-LAN trust boundary.
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[stt] serving on 0.0.0.0:{PORT}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
